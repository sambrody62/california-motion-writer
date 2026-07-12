# E2E Run-Through Test Findings — 2026-07-06

Fictional scenarios used:
- **Maria Vasquez** (API-level): LA County petitioner, case 24STFL01234, RFO to modify
  custody/visitation because ex (Daniel Reyes) returned kids Sofia (8) and Mateo (5) late
  nine times since March 2026.
- **Carlos Mendoza** (UI-level): Pasadena father requesting more parenting time for son
  Diego (6), case 24STFL05678.

Setup: backend `uvicorn app.main:app` on :8001 (mock LLM, fresh sqlite), CRA frontend on
:3001 with `REACT_APP_API_URL` override. Port 8000 was occupied by an unrelated project
container (`api-api-1`, GrowthBenchmarks/fathom) — see Environment notes.

## What works
- Register → login → JWT auth (register even returns a token directly).
- Profile create/read round-trip incl. children_info; frontend auto-fill from profile
  into guided FL-300 step 1 (case number, county, other party) works.
- Full 6-step RFO intake API: conditional steps skip correctly (support step skipped when
  not requested), progress tracking, `ready_for_llm`, FL-311 attachment flagged.
- `POST /llm/process-motion` and `POST /llm/rewrite` (mock backend).
- `POST /documents/generate-pdf-sync` → valid 6-page PDF containing all scenario data.
- AuthZ: other users get 404 on foreign motions/documents/summaries; 401 without token.
- Chat sessions/messages endpoints.
- UI: signup, login, profile save (via POST fallback), case intake → gameplan → forms list.

## Blockers (P0)

### 1. Guided form flow hard-stuck on Step 1 — saveDraft called with wrong arguments
`GuidedIntake.tsx:224`: `saveDraft(motionId!, currentStep, data)` but
`api.ts` signature is `saveDraft(motionId, payload)`. `currentStep` (a number) lands in
the payload slot → request body serializes to `{}` → backend 422 (step_number/step_name/
question_data all missing) → catch keeps user on step 1 with **no visible error**.
The `(motionAPI as any)` cast hides the type mismatch. Every "Next" click fails; the
guided FL-300 cannot be completed by any user.

### 2. Motion preview & detail pages crash → redirect to dashboard
`GuidedIntake.tsx:178` and `MotionPreview.tsx:58` do `draftsResponse.data.drafts` but
`motionAPI.getDrafts()` already returns the unwrapped drafts array
(`response.data.drafts`). Result: `TypeError: Cannot read properties of undefined
(reading 'drafts')` in `loadStep`/`loadMotionData`; `/motion/:id/preview` and
`/motion/:id` bounce to dashboard. Even with completed drafts, the user can never
preview or download their PDF through the UI.

### 3. Violations ("Enforce an existing order") frontend paths all 404
Frontend calls `/violations/tracks`, `/violations/intake-questions`,
`/violations/process`, `/violations/generate-declaration`; backend registered them under
a doubled prefix: `/violations/violations/...` (router included with prefix
`/violations` AND routes declared with `/violations/...`). Verified: frontend paths 404,
doubled paths 200. Whole enforcement track broken. Same doubled-prefix pattern exists on
`/evidence/evidence/{id}` and `/chat-pdf/chat-pdf/...` (latter currently unused by FE).

### 4. Evidence endpoints path mismatches (v1.1, flag-gated)
- FE `POST /motions/{id}/evidence/upload` → 404 (backend:
  `/evidence/motions/{id}/evidence/upload`).
- FE `PUT|DELETE /evidence/{id}` → 404 (backend: `/evidence/evidence/{id}`).

### 5. Document download returns the wrong court form (FL-320) for every motion
`documents.py` download handler regenerates the PDF via legacy
`pdf_service.generate_motion_pdf(motion_type=motion.motion_type, ...)` passing the raw
enum. `MotionType` is a plain `enum.Enum`, so `motion_type == "RFO"` is always False in
`pdf_service.py:268` → **every** download renders a mostly-blank FL-320 (responsive
declaration) instead of the generated FL-300 packet. Maria's RFO download came back as
a 2-page blank FL-320 (326KB 6-page packet was generated; 97KB blank form downloaded).
Root causes: (a) generated PDFs never persisted (`gcs_url=""`), so download regenerates;
(b) regeneration uses a different generator than generate-pdf-sync; (c) enum vs value.

## High

### 6. Async `POST /documents/generate-pdf` 500s
`'Motion' object has no attribute 'case_number'` (case_number lives on Profile). Sync
endpoint works; async path crashes.

### 7. Backend won't boot with USE_GCP=false unless USE_MOCK_LLM=true
`llm_service.py`: import guard only falls back to mock on ImportError; with
`USE_GCP=false, USE_MOCK_LLM=false, USE_CLAUDE=false` the `else` branch still calls
`vertexai.init()` → NameError at import → entire API dead. Also `USE_GOOGLE_AI` (set in
root `.env`) is never read by `llm_service.py` — dead config.

### 8. LLM/mock output flows into filing-ready PDF unvalidated
With the mock backend, "MOCK LLM RESPONSE..." boilerplate was embedded verbatim in the
generated court PDF. No guard that rewritten sections are real content — an LLM failure
mode (or mock in the wrong env) produces a court-filing PDF with garbage, no warning.

### 9. Gameplan page shows placeholder strategy with a success checkmark
When the strategy LLM output can't be parsed, the UI silently renders generic fallback
("Legal situation analysis", "Legal strategy recommendation") under a green check — the
user cannot tell the AI produced nothing.

## Medium / polish
- Filename leaks enum repr: `24STFL01234_MotionType.RFO_20260706.pdf`
  (`documents.py:244` interpolates the enum, not `.value`).
- Documents listing always `available: false` (`gcs_url` never set) even though download
  route exists; FE can't tell what's downloadable.
- `POST /motions/` rejects lowercase `"rfo"` — enum values are uppercase; error message
  is good, but FE/BE should agree on canonical casing.
- Register UI has no full-name field though API `UserCreate` requires `full_name`
  (FE presumably defaults it; users get a profile with no name until profile setup).
- Profile "Add Child" allows saving an empty child row (`{"name":"","date_of_birth":""}`)
  — no validation.
- React warning: `checked="false"` string on case-intake radio (truthy in HTML).
- Fresh-user `GET /profiles/me` 404 logged as console error noise on every dashboard load
  before profile creation (FE falls back to POST correctly).
- Dashboard motion card: "Case #: Draftcompleted" — missing value + status strings run
  together.
- `run_local.sh` runs `python main.py` but no root `main.py` exists (correct entry:
  `uvicorn app.main:app`).

## Environment notes (not app bugs)
- Local port 8000 is currently held by container `api-api-1` (GrowthBenchmarks "fathom")
  while frontend `.env`/`.env.local` point the motion-writer FE at :8000 — running the
  user's normal dev setup right now would hit the wrong backend.
- Playwright driver + screenshots for this run: `/tmp/pw-e2e/` (shots in
  `/tmp/pw-e2e/shots/`), API artifacts in `/tmp/e2e_*.json`, generated PDF at
  `/tmp/e2e_motion.pdf`.
