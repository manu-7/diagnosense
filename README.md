# DiagnoSense — AI-Assisted Cloud Diagnostic Platform

**Final Year Project — Software Engineering & Cloud Computing**

DiagnoSense is a full-stack, cloud-deployed diagnostic-center booking platform.
Patients describe symptoms in plain language, receive AI-grounded test
recommendations from a real catalogue of bookable packages, pay for and book a
test, and later receive a lab report where abnormal values are automatically
flagged and explained in plain language — grounded in real clinical reference
material rather than a raw LLM guess.

The project was built to demonstrate two things end to end: sound **software
engineering practice** (layered architecture, typed data models, migrations,
authentication, payment-signature verification, defensive error handling) and
practical **cloud computing** deployment (containerized services, managed
Postgres with a vector extension, managed cache, a multi-provider cloud
topology, and object storage with time-limited signed access).

---

## 1. Problem Statement

Patients booking diagnostic tests typically have two disconnected problems:

1. **They don't know which test they need.** Symptom descriptions in plain
   language rarely map cleanly to a lab's list of package names.
2. **Reports are handed back as raw numbers.** A value like "Hemoglobin: 9.8"
   means little without context on why it might be low and what commonly
   causes it.

DiagnoSense addresses both: an AI triage step for the first problem, and a
retrieval-augmented explanation step for the second — while keeping every
recommendation and explanation traceable back to real data (real packages,
real reference ranges, real reference text) rather than free-floating model
output.

---

## 2. System Architecture

```
                        Frontend
                React + Vite + Tailwind
                   (Vercel, CDN)
                         |
                     HTTPS / REST
                         v
                    Backend API
                  FastAPI (async)
               (Render, containerized)
                 /        |         \
                /         |          \
    PostgreSQL+pgvector  Redis      Groq LLM API
    (Supabase, managed)  (Render)   (triage +
    - relational data    - cache      explanations)
    - RAG embeddings     - Celery
          |                broker
          v
  Supabase Storage         Razorpay
  (S3-compatible)          (payment +
  - report PDFs             HMAC verify)
  - signed URL access
```

**Why this topology:** the project deliberately spans more than one cloud
provider (Render for compute, Supabase for managed Postgres/pgvector/storage)
to reflect a realistic modern deployment — few real systems run entirely
inside a single vendor, and stitching these together (shared secrets, CORS,
connection pooling quirks) is itself part of the cloud-computing learning
outcome of this project, not incidental overhead.

---

## 3. Core Features

### Patient-facing
- Email/password auth (JWT access + refresh tokens)
- **AI symptom triage** — free-text symptom description is matched against
  the real, current package catalogue (not a fixed symptom list) by an LLM,
  with the catalogue cached in Redis to keep repeated queries fast
- Browse diagnostic centers, filter by city
- Book a package, pay via Razorpay (test mode), receive an email confirmation
- View past bookings and completed reports, including any flagged anomalies
  and their plain-language explanation
- Download the generated report PDF

### Center-facing
- Separate center account role, scoped to that center's own data only
- View paid bookings awaiting processing
- Enter measured lab values for a booking → system generates the PDF report,
  runs anomaly detection, and (if anything is out of range) retrieves the
  relevant clinical reference snippet and asks the LLM to explain it in
  plain language, citing that snippet rather than inventing an explanation

### Platform-level
- Retrieval-augmented generation (RAG): a small local sentence-embedding
  model embeds a bank of clinical reference sheets into `pgvector`; anomaly
  explanations retrieve the top matching snippet(s) for the specific
  out-of-range parameter before calling the LLM, so explanations are grounded
  in the same reference text every time rather than hallucinated
- Signed, time-limited (5-minute) URLs for report downloads — no report is
  ever publicly/permanently accessible
- Razorpay webhook/callback payloads are verified server-side via HMAC
  signature before a booking is marked paid — the frontend cannot forge a
  paid status

---

## 4. Technology Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React 18, Vite, Tailwind CSS | Fast dev loop, small bundle, utility-first styling |
| Backend | FastAPI (async), SQLAlchemy 2.0 (async), Alembic | Async end-to-end for DB/LLM/HTTP I/O without blocking |
| Database | PostgreSQL 16 + `pgvector` | Relational data + vector similarity search in one engine, no separate vector DB |
| Cache / Broker | Redis | Catalogue caching, Celery broker/result backend |
| Background jobs | Celery | Best-effort async notifications; core request paths never depend on a worker being up |
| LLM | Groq (Llama 3.3 70B) | Low-latency inference for real-time triage and explanation generation |
| Payments | Razorpay (test mode) | Order creation + client checkout + server-side signature verification |
| Object storage | Supabase Storage (S3-compatible) | Presigned URL access, no code difference from "real" S3 |
| Auth | JWT (HS256), bcrypt password hashing | Stateless auth suitable for a horizontally-scalable API |
| Deployment | Render (API + Redis), Vercel (frontend), Supabase (DB + storage) | Free-tier-friendly, realistic multi-provider cloud setup |

---

## 5. Data Model (high level)

- **User** — patient or center account, role-gated
- **DiagnosticCenter** — one-to-one with a center-role user
- **Package** — a bookable test, owned by a center, tagged with the symptoms
  it's relevant to and its test type (blood/urine/imaging/etc.)
- **Booking** — links a patient, a package, a schedule, and payment state
  (`PENDING` -> `PAID`/`FAILED`), plus the Razorpay order/payment/signature
- **Report** — one-to-one with a booking; stores the S3 object key, the
  measured values, detected anomalies, and the AI-generated explanation with
  its source reference snippets
- **ReferenceSnippet** — clinical reference text per lab parameter, with a
  384-dimension embedding column for similarity search

---

## 6. Local Development

### Prerequisites
Docker Desktop, Node.js 18+, a Groq API key, a Razorpay test-mode key pair.

### Quick start (recommended — fully self-contained)
```bash
# backend
cd backend
cp .env.example .env   # fill in SECRET_KEY, RAZORPAY_*, GROQ_API_KEY, S3 creds
docker compose up --build
```
```bash
# one-time setup, second terminal
docker compose exec db psql -U postgres -d diagnostic_db -c "CREATE EXTENSION IF NOT EXISTS vector;"
docker compose exec api alembic upgrade head
docker compose exec api python -m app.seed
docker compose exec api python -m app.seed_rag
```
```bash
# frontend, third terminal
cd frontend
cp .env.example .env
npm install && npm run dev
```
Backend on `:8000` (interactive docs at `/docs`), frontend on `:5173`.

### Running against a hosted Postgres (e.g. Supabase) instead of the local container
Two things to know if you go this route:
1. **pgbouncer transaction-mode pooling** (the default Supabase pooler on port
   `6543`) doesn't support asyncpg's prepared statements. The engine in
   `app/database.py` and the Alembic engine in `alembic/env.py` both set
   `statement_cache_size: 0` / `prepared_statement_cache_size: 0` to work
   around this — if you see `DuplicatePreparedStatementError`, this is why,
   and it's already handled in code.
2. Use `docker-compose.supabase.yml` alongside the main compose file to skip
   the local `db` container and let `api`/`celery_worker`/`celery_beat` read
   `DATABASE_URL` straight from `.env`:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.supabase.yml up --build api redis celery_worker celery_beat
   ```

### Running the backend natively (no Docker)
`pgvector` has no official native Windows build — installing it outside the
provided Docker image means compiling from source, which is impractical on
Windows. If you want to run the API/Celery natively, still run **Postgres**
via Docker (`docker compose up -d db`) and point your local process at it;
don't attempt a native Windows Postgres + pgvector install.

Redis is optional for a basic run: `redis.asyncio.from_url()` connects
lazily, so the API starts fine without it — only the symptom-catalogue cache
and Celery notifications are affected, not core booking/report flows.

---

## 7. Cloud Deployment

The deployed environment intentionally spans three providers:

| Component | Provider | Notes |
|---|---|---|
| API (FastAPI, Docker) | **Render** — Web Service | Built from `backend/Dockerfile`, root directory `backend/` |
| Cache/broker | **Render** — Key Value (Redis-compatible) | Same region as the API for internal networking |
| Database | **Supabase** — managed Postgres | `pgvector` extension enabled via the dashboard |
| Object storage | **Supabase Storage** | S3-compatible endpoint, presigned URLs |
| Frontend | **Vercel** | Built from `frontend/`, framework preset Vite |

### Deployment gotchas encountered (and already fixed in code)
These are documented because they're representative cloud-deployment issues,
not one-off mistakes — worth understanding rather than just working around:

- **CORS is origin-exact.** `CORSMiddleware` is configured with a single
  `FRONTEND_URL` value. Vercel's *preview* deployment URLs (unique per commit)
  differ from the stable production domain — testing against a preview URL
  while CORS only allows the production domain will silently fail every
  request with no useful browser error beyond a generic network failure.
- **SPA client-side routes need a rewrite rule on Vercel.** Without
  `frontend/vercel.json`'s catch-all rewrite to `index.html`, navigating
  directly to (or returning via browser back-button to) a client-side route
  like `/reports/:id` produces a genuine 404 from Vercel's static host, since
  no such file exists — only React Router (running client-side) knows that
  route.
- **`window.open()` after an `await` gets silently popup-blocked** in most
  browsers, since the call no longer counts as a direct result of the user's
  click by the time the awaited request resolves. Report downloads instead
  fetch the file as a `Blob` and trigger the download from a same-origin
  `blob:` URL, which browsers do not block and which also produces a real
  file in the Downloads folder (a cross-origin `href` with a `download`
  attribute is silently ignored by browsers, which is why a plain link to
  the signed URL only ever opens/navigates instead of saving a file).
- **Vite env vars are baked in at build time.** Changing `VITE_API_URL` in
  Vercel's dashboard has no effect until the next build — a redeploy is
  required, not just a saved setting.
- **Schema drift from ad-hoc table creation.** Bootstrapping tables via
  `Base.metadata.create_all()` (rather than clean Alembic migrations, done
  here as a pragmatic fix mid-project) only creates *missing* tables — it
  will not retrofit new columns onto a table that already exists. Two
  separate instances of this occurred here — reflected as a lesson to always
  reconcile live schema against models before assuming Alembic and ad-hoc
  fixes haven't diverged.

---

## 8. Security Notes

- Passwords hashed with bcrypt; never stored or logged in plaintext
- JWT access + refresh token pair; short-lived access token
- Payment status can only move to `PAID` after the backend independently
  recomputes and verifies the Razorpay HMAC signature — the client cannot
  set this directly
- Report files are never public; every download goes through a fresh
  5-minute presigned URL, generated per-request and scoped to the requesting
  user's own booking
- Center accounts can only see and act on bookings/packages belonging to
  their own center (enforced server-side, not just hidden in the UI)

---

## 9. Known Limitations / Future Work

- Alembic migration history was reset mid-project after diverging from the
  live schema; a clean migration baseline should be regenerated before any
  further schema changes
- No admin role/route yet for approving new center registrations — centers
  are currently auto-approved on signup
- Lab value entry is manual text/JSON input; OCR-based extraction from an
  uploaded scanned report is a natural next step
- Reviews/ratings are not yet implemented; the intended design is to
  restrict them to patients with a completed, paid booking at that center,
  to keep ratings verifiable rather than open to abuse
- Celery worker is not deployed in the current cloud environment (cost
  tradeoff on the free tier); notification emails and OCR-style background
  jobs are queued but not consumed in production — core booking/report flows
  do not depend on this and are unaffected

---

## 10. Repository Structure

```
backend/    FastAPI + PostgreSQL + Redis + Celery + Razorpay + Groq
            see backend/README.md for the full endpoint list and env vars
frontend/   React + Vite + Tailwind
            see frontend/README.md for component structure
```

## 11. Academic Context

Submitted as a final-year project under **Software Engineering and Cloud
Computing**. The engineering focus areas demonstrated are: layered
service/router/model separation, async I/O throughout the request path,
schema migrations, defensive handling of optional infrastructure (Celery),
and signature-verified payment integration. The cloud-computing focus areas
demonstrated are: containerized deployment, managed database with a vector
extension, a multi-provider production topology, object storage with
time-limited access, and the operational issues (CORS, SPA routing, build-time
vs runtime configuration, connection pooling behavior) that come with
deploying — not just building — a cloud-hosted system.
