# AI-Powered Diagnostic System

A diagnostic-center booking platform: patients describe symptoms, get
AI-grounded test recommendations, book + pay for tests, and get lab reports
back with automatic anomaly flagging against clinical reference ranges.

```
backend/    FastAPI + PostgreSQL + Redis + Celery + Razorpay + Groq — see backend/README.md
frontend/   React + Vite + Tailwind                                — see frontend/README.md
```

## Quick start

```bash
# backend
cd backend
cp .env.example .env   # fill in SECRET_KEY, RAZORPAY_*, GROQ_API_KEY, S3 creds
docker compose up --build

# frontend, in a second terminal
cd frontend
cp .env.example .env
npm install && npm run dev
```

Backend on `:8000` (docs at `/docs`), frontend on `:5173`. See `backend/README.md`
for the one-time `CREATE EXTENSION vector` + seed steps needed for the RAG
anomaly explanations to work.

> **Running the backend locally without Docker?** The RAG feature needs the
> `pgvector` Postgres extension. It's prebuilt into the `pgvector/pgvector:pg16`
> Docker image used here, but installing it on a native Windows Postgres install
> means compiling from source - genuinely awkward on Windows. If you're doing
> local (non-Docker) dev, easiest path is running just Postgres via Docker
> (`docker compose up -d db`) while your API/Celery run locally against it -
> rather than installing a native Postgres + pgvector on Windows directly.

## Deployment

- **Backend** → Render (or Railway), root directory `backend/`
- **Frontend** → Vercel, root directory `frontend/`, framework preset Vite
- **DB** → managed Postgres with pgvector support (Render/Supabase both offer
  this - confirm the plan includes the `vector` extension); **Redis** → Render/Upstash

## Architecture

Patient → symptom-check (Groq, grounded in real package catalogue) → book
package → Razorpay checkout → server-side HMAC verification → confirmed
booking → center uploads report to S3 → Celery runs rule-based anomaly
detection → patient sees flagged values against normal ranges.

See `backend/README.md` for the full endpoint list, auth flow, and known
gaps (Alembic migration, admin center-approval route, OCR for lab values,
test suite).
