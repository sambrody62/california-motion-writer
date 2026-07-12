# Deploying — Supabase + Render + Vercel (~$0/mo)

The repo is fully configured; going live is about 20 minutes of clicking
through three dashboards. Do these in order.

## 1. Supabase (database + file storage) — ~5 min
1. https://supabase.com → New project (any region near us-west).
2. Project Settings → Database → **Connection string (URI)** — copy the
   **direct** one (port **5432**, not the 6543 pooler). This is `DATABASE_URL`.
3. Project Settings → API → copy the **service_role** key → `SUPABASE_SERVICE_KEY`,
   and the project URL → `SUPABASE_URL`.
4. Storage → New bucket → name it `evidence`, **private**.

Tables create themselves on the backend's first boot — no SQL to run.

## 2. Render (backend) — ~5 min
1. https://dashboard.render.com → New → **Blueprint** → connect this GitHub repo.
   Render reads `render.yaml` and creates the `california-motion-api` service.
2. Paste the secrets it prompts for: `DATABASE_URL`, `SUPABASE_URL`,
   `SUPABASE_SERVICE_KEY`, `ANTHROPIC_API_KEY`.
   Leave `CORS_ORIGINS` blank for now (set in step 4).
3. Deploy. Verify: `https://<your-service>.onrender.com/health` returns
   `{"status":"healthy",...}`.
   - If the service URL is not `california-motion-api.onrender.com`, note the
     real one for step 3.

Free-tier note: the service sleeps after 15 idle minutes; the first request
after that takes ~50s. Fine for beta; $7/mo removes it later.

## 3. Vercel (frontend) — ~5 min
1. https://vercel.com → Add New Project → import this repo.
2. **Root Directory: `frontend`** (it will detect Create React App).
3. Environment variables: copy everything from `frontend/.env.production`,
   updating `REACT_APP_API_URL` to your real Render URL + `/api/v1`.
   Auth is backend JWT (`/api/v1/auth`); no Firebase configuration is needed.
4. Deploy. Note your Vercel domain (e.g. `https://<project>.vercel.app`).

## 4. Connect the two
1. Render → california-motion-api → Environment → set
   `CORS_ORIGINS=https://<your-project>.vercel.app` → save (auto-redeploys).

## 5. Smoke test the live app
Register → set up profile → start an RFO → complete intake → download the
PDF packet. If the PDF has your test names in it, you're live.

## Flags reference (all currently OFF by design)
| Flag | Where | Turn on when |
|---|---|---|
| `GMAIL_EVIDENCE_ENABLED` | Render | Google OAuth verification approved (docs/GOOGLE_OAUTH_SETUP.md) |
| `REACT_APP_GMAIL_ENABLED` | Vercel | Same time as above |
| `OCR_ENABLED` | Render | Cloud Vision credentials configured |

## Rollback / GCP note
The GCP path still works (`USE_GCP=true`, no `DATABASE_URL`) — nothing was
deleted. The old Cloud Run/Cloud SQL setup is simply unused; make sure no GCP
resources are left running so nothing bills.
