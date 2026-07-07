# AI-Powered Diagnostic System

Production-grade backend for a diagnostic-center booking platform: patients describe
symptoms, get AI-grounded test recommendations, book + pay for tests, and get lab
reports back with automatic anomaly flagging.

Built to the same standard as EcoPark/Eventix — this is a from-scratch rebuild, not
a patch on the original skeleton repo.

## Stack

- **FastAPI** + **async SQLAlchemy 2.0** + **PostgreSQL** (Alembic migrations)
- **Redis** (catalogue caching) + **Celery** (async email/anomaly jobs)
- **JWT** auth (access + refresh) with role-based access control (patient / center / admin)
- **Razorpay** (order creation + HMAC-SHA256 signature verification)
- **S3-compatible storage** (works with AWS S3 or Supabase Storage) for lab report files, via short-lived signed URLs
- **Groq** (Llama 3.3 70B) for symptom→test recommendation, grounded strictly in each
  center's actual package catalogue — it can only pick from real packages, never invents one
- Rule-based, deterministic lab anomaly detection (the LLM only phrases the explanation — it never decides what counts as abnormal)

## What makes this the "best version"

The original repo (and the report describing it) had all of this as a diagram/plan
with no working code. Here it's actually implemented, plus three things that matter
in a real system and get asked about in interviews:

1. **Object-level authorization (IDOR protection)** — a diagnostic-center account can
   only upload/view reports for bookings that belong to *its own* center, not just any
   booking. Role-based checks (`require_role`) are necessary but not sufficient; ownership
   is checked separately on every report/booking-scoped endpoint.
2. **Graceful degradation** — Redis being down doesn't take out the AI endpoint (falls
   back to Postgres), and a Celery/broker outage doesn't turn a *successfully verified
   payment* into a 500 for the patient. External dependencies fail closed only where
   they must (payment signature, storage), and fail open everywhere else (caching, notifications).
3. **Payment security** — Razorpay signature check uses `hmac.compare_digest`
   (constant-time comparison) to avoid timing attacks, exactly mirroring what
   Razorpay's own webhook verification expects.

## Project layout

```
app/
  models/       SQLAlchemy models (User, DiagnosticCenter, Package, Booking, Report, SymptomQuery)
  schemas/      Pydantic request/response schemas
  routers/      auth, centers, bookings, reports, ai
  services/     payment_service (Razorpay), storage_service (S3), ai_service (Groq), email_service
  tasks/        Celery app + async jobs (confirmation emails, report-ready emails, anomaly analysis)
  core/         Redis client
  security.py   bcrypt hashing + JWT issue/verify
  config.py     Pydantic settings, reads from .env
alembic/        DB migrations
docker-compose.yml   api + postgres + redis + celery worker + celery beat
```

## Running it

```bash
cp .env.example .env
# fill in SECRET_KEY, RAZORPAY_KEY_ID/SECRET, GROQ_API_KEY, S3 creds

docker compose up --build
```

API docs at `http://localhost:8000/docs`.

Enable the `vector` extension once (needed for RAG retrieval - the `db` image is
`pgvector/pgvector:pg16`, which ships the extension, but it still needs enabling
per-database):
```bash
docker compose exec db psql -U postgres -d diagnostic_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

First migration:
```bash
docker compose exec api alembic revision --autogenerate -m "init"
docker compose exec api alembic upgrade head
```

Populate demo data + the RAG reference snippets:
```bash
docker compose exec api python -m app.seed        # demo centers, packages, patient
docker compose exec api python -m app.seed_rag    # embeds reference material for anomaly explanations
```
`seed_rag` downloads a small embedding model (~130MB, fastembed/BAAI-bge-small)
from HuggingFace on first run - needs internet access once, then it's cached.

### Groq API key
Get one free at https://console.groq.com — drop it into `.env` as `GROQ_API_KEY`.
Without it, `/api/v1/ai/symptom-check` returns a clean `503` rather than crashing.

## How the RAG-grounded anomaly explanation works

`app/services/rag_service.py` is the whole pipeline in one file:
1. A lab value gets flagged as abnormal by `ai_service.flag_anomalies` (fixed
   reference-range table, zero AI involved in this decision)
2. The parameter name gets embedded and matched against `reference_snippets`
   (seeded by `app/seed_rag.py`) via Postgres/pgvector cosine similarity
3. The retrieved paragraph is passed to the LLM as the *only* material it's
   allowed to explain from - not free-recalled from training data
4. The response carries `explanation_sources` so the patient (or an examiner)
   can see exactly what the explanation was grounded in

If retrieval finds nothing (no snippets seeded yet, or the embedding model
couldn't download), it falls back to an ungrounded LLM explanation rather
than failing the report.

## Auth flow

1. `POST /api/v1/auth/register` — role is `patient` or `center` (admin is seeded manually)
2. `POST /api/v1/auth/login` — returns `access_token` + `refresh_token`
3. `POST /api/v1/auth/refresh` — rotate a new pair from a valid refresh token
4. Center accounts then `POST /api/v1/centers/me` to create their center profile
   (starts `is_approved=False` — an admin has to approve before it's publicly listed)

## Booking + payment flow

1. `POST /api/v1/bookings` — patient books a package at a center
2. `POST /api/v1/bookings/{id}/create-order` — creates a Razorpay order
3. Frontend runs Razorpay Checkout, gets back `razorpay_payment_id` + `razorpay_signature`
4. `POST /api/v1/bookings/verify-payment` — server-side HMAC verification, only then
   is the booking marked `CONFIRMED` and a confirmation email queued

## Report flow

1. Center: `POST /api/v1/reports/{booking_id}/upload` — uploads to S3, only if the
   booking belongs to that center
2. Center/Admin: `POST /api/v1/reports/{report_id}/analyze` — kicks off async anomaly
   detection against clinical reference ranges
3. Patient/Admin: `GET /api/v1/reports/{report_id}/download` — returns a short-lived
   signed URL, never the raw file path

## Known gaps / next steps

- Alembic migrations aren't generated yet in this scaffold — run the autogenerate
  command above against a real Postgres instance
- OCR/PDF parsing for lab values isn't wired up — `analyze_report` currently expects
  the extracted values as JSON (a real OCR step would produce this from the uploaded file)
- No test suite yet — smoke-tested manually against SQLite during scaffolding, but no
  pytest suite is checked in
- Admin approval endpoints for centers aren't built yet (the `is_approved` flag exists
  on the model but there's no `PATCH` route to flip it)
