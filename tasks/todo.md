# Build Plan — California Motion Writer MVP

Source: PRD_COMPLETE.md + approved plan (Phase A-F).
Build strategy: orchestrator (this session) + Sonnet subagents for implementation, Haiku for mechanical tasks.

## Phase 0: Environment Setup
- [ ] Preflight: Docker, ports, env vars, test infra validated
- [ ] Confirm blank court form PDFs exist (forms/FL-300.pdf, MC-030.pdf, FL-150.pdf)
- [ ] Backend smoke: pdf_service.generate_motion_pdf() produces real output

## Phase A: Fix Integration Layer (CRITICAL PATH)
- [ ] A1. Wire motionAPI.saveDraft → POST /motions/{id}/drafts (frontend/src/services/api.ts)
- [ ] A2. Wire motionAPI.getDrafts → GET /motions/{id}
- [ ] A3. Wire motionAPI.processWithLLM → POST /llm/process-motion
- [ ] A4. Wire documentAPI.generatePDFSync → POST /documents/generate-pdf-sync (real ArrayBuffer)
- [ ] A5. Implement GET /documents/{id}/download (backend, sync path)
- [ ] A6. Profile auto-fill in GuidedIntake on mount

## Phase B: Backend Bug Fixes
- [ ] B1. Add enhance_declaration() to LLMService (app/services/llm_service.py)
- [ ] B2. Add city/zip_code/state to Profile model + migration
- [ ] B3. Fix WebSocket auth (app/main.py — remove hardcoded test_user)
- [ ] B4. Fix useAuth import in ChatInterface (.ts stub vs .tsx)
- [ ] B5. Fix walrus operator bug in validate_output()

## Phase C: PDF Quality
- [ ] C1. Verify FL-300 field mapping completeness
- [ ] C2. FL-150 conditional inclusion (support issues)
- [ ] C3. MC-030 declaration assembly verification

## Phase D: UX
- [ ] D1. LLM loading state in GuidedIntake
- [ ] D2. Form completion callback (FormExecution ← GuidedIntake)
- [ ] D3. Filing checklist post-download (county lookup table)

## Phase E: Tests
- [ ] E1. Fix api.test.ts (fetch mocks → axios-mock-adapter)
- [ ] E2. Backend PDF smoke test
- [ ] E3. E2E: register → profile → intake → LLM → PDF download >10KB

## Review

### M0 — Test Infrastructure Repair (DONE 2026-06-12)
- Backend: 60 failures → 0 (120 passed, 3 xfailed for M1 endpoints). Root causes: pytest.ini header syntax (config silently ignored), httpx not following FastAPI 307 redirects, bcrypt/passlib version conflict, plus real contract drift in auth/motions/profiles endpoints.
- Frontend: 0 tests running → 39 passed. Root cause: tests invoked via bare jest instead of react-scripts (no TSX transform). 2 stale fetch-era suites skipped pending M1 rewrite.
- Commits: chore(test) infra repair, fix(api) contract alignment.
- Notable: motions.py debug endpoint + DEBUG prints removed; profiles/motions gained PUT/DELETE; register returns 201.
- Flagged for later: chat_service intent regex misses "violated/violating/violations" (M3 triage work); pydantic/datetime deprecation warnings.

### M1 — MVP Integration (DONE 2026-06-12)
- All 5 frontend API stubs replaced with real backend calls; auth path and dev port fixed; useAuth shadow stub deleted.
- All 5 backend bugs fixed (enhance_declaration, walrus bug, Profile city/zip/state, WebSocket JWT auth, document download endpoint).
- PDF generation PROVEN: E2E test produces 306KB FL-300 with extractable party names. Found+fixed FL-150 missing caption fields. Key learning: templates are encrypted AcroForms — coordinate overlay is the right strategy, AcroForm field-filling silently fails.
- Profile auto-fill, LLM loading state, LLM-failure-never-blocks-PDF, completion tracking, filing checklist (5 counties) all in.
- Suites: backend 142 passed + 3 xfailed; frontend 73 passed.
- Commits: feat(backend) 4f49fa4, feat(frontend) c2fdc6b, docs f3008e0.
- KNOWN GAP → M3: no generate_packet() — FL-150 not auto-bundled when support issue present; single-form PDFs only.

### M2 — Claude LLM Backend (DONE 2026-06-12)
- Haiku 4.5 (chat/classification/UPL checks) + Sonnet 4.6 (drafting), USE_CLAUDE flag, prompt caching, UPL guardrails in system prompt + validate_output advice-phrase scan. 24 new tests.
- PENDING USER: ANTHROPIC_API_KEY in .env / Secret Manager + USE_CLAUDE=true to go live.

### M3 — Phase 2 Forms (DONE 2026-06-12)
- generate_packet() multi-form PDFs (closes M1 gap); FL-320 Response flow with 9-court-day deadline warning; FL-150 standalone; support-only path hides custody questions; violations wizard wired to existing SD backend; /emergency public route (911 banner, quick exit, DVRO/ex parte links — no DV generation, templates not in repo); triage panel (RFO vs contempt, neutral, never auto-routes).
- Suites: backend 174 + 3 xfailed, frontend 121. Committed.
- Remaining for M4: evidence upload/tagging/exhibit assembly. Tech debt: llm_service.py 634 lines (>300 rule).

### M4 — Evidence Synthesis (DONE 2026-06-12) = v1.0 launch feature freeze
- Evidence model + storage + CRUD; exhibit assembly (lettered exhibits, cover page, mechanical reference paragraph) into PDF packets; evidence UI with manual paste + upload-with-transcription. Backend 219, frontend 132.

### v1.1 — Gmail + OCR adapters (DONE 2026-06-12, flag-gated OFF)
- Two-version structure per user request: v1.0 launches without Gmail/OCR; v1.1 ships the same codebase with GMAIL_EVIDENCE_ENABLED / OCR_ENABLED / REACT_APP_GMAIL_ENABLED defaulting off. Flip flags (no code change) when Google approves.
- Gmail: stateless OAuth, scan-by-other-party, import as unconfirmed Evidence. OCR: Cloud Vision pre-fill suggestion on upload, user still confirms. Privacy policy + terms pages (/privacy, /terms), docs/GOOGLE_OAUTH_SETUP.md. Backend 244, frontend 161.
- NO iMessage integration (no platform API exists — screenshots+OCR is the path).

## M5 — E2E bug-fix round (DONE 2026-07-07, from tasks/e2e-test-findings.md)
Backend (pytest first):
- [x] M5.1 Route prefixes: violations/evidence routes match frontend calls
      (/api/v1/violations/tracks, /api/v1/motions/{id}/evidence/upload, /api/v1/evidence/{id});
      chat-pdf normalized; gmail routes renamed to frontend contract (/gmail/auth-url,
      /gmail/exchange-code, /motions/{id}/gmail/scan|import)
- [x] M5.2 Download regenerates via same generate_packet as generate-pdf-sync (correct FL-300);
      filename uses enum .value; listing `available` truthful
- [x] M5.3 Async generate-pdf: Motion.case_number crash (case number read from profile)
- [x] M5.4 llm_service boots with USE_GCP=false (mock fallback, no NameError);
      mock rewrite/declaration/enhance return the user's words, no placeholder copy
- [x] M5.5 motions create accepts case-insensitive motion_type; motion responses now
      include case_number (from profile) for dashboard cards + PDF filenames
Frontend (Jest):
- [x] M5.6 GuidedIntake onSubmit: correct saveDraft payload {step_number, step_name, question_data}
- [x] M5.7 GuidedIntake.loadStep + MotionPreview.loadMotionData: use getDrafts()/get() returns
      directly (removed `as any` casts; TS now enforces the contract); MotionPreview blob
      built from ArrayBuffer, not .data
- [x] M5.8 Case-intake radio: watch() returns "true"/"false" strings — normalized to boolean
- [x] M5.9 Profile setup: drop empty child rows on save
- [x] M5.10 Dashboard card case number: fixed via M5.5 (backend now supplies it)
- [x] M5.14 (found during verify) GuidedIntake returned to /form/execution which matches no
      route → blank page; now returns to /case/forms where FormExecution is mounted
Infra:
- [x] M5.11 run_local.sh: uvicorn app.main:app on port 8000 (main.py never existed)
Verify:
- [x] M5.12 Backend 278 passed + 3 xfailed; frontend 163 passed (18 suites)
- [x] M5.13 Live UI E2E re-run: login → profile → intake → gameplan → guided FL-300 all
      6 steps → completion screen → dashboard (case # shown) → preview (renders, user
      words, no MOCK text) → downloaded FL-300-24STFL05678.pdf (131KB, FL-300, no mock
      copy). Zero console errors, zero failed requests.

### M5 review
- Root cause cluster 1 (frontend): Jest mocks encoded axios-response shapes ({data: ...})
  while the api.ts helpers return unwrapped data; components were written against the
  mocks and every motion view crashed against the real API. Casts of `(motionAPI as any)`
  hid it from TS. Fixed mocks to real shapes; removed casts so tsc enforces the contract.
- Root cause cluster 2 (backend): routers included with prefixes the endpoint files
  already carried → doubled paths the frontend never called; plain-Enum MotionType
  compared against strings → always-FL-320 downloads and enum-repr filenames.
- New regression suite: tests/test_e2e_regressions.py (route contract asserted against
  app.routes, download/packet consistency, llm boot fallback, mock output policy).
- Tech debt noted: documents.py 397 lines (>300 rule).

## LAUNCH-BLOCKING (user actions, none are code)
1. Google OAuth verification — submit gmail.readonly (weeks; test mode works for 100 users now). See docs/GOOGLE_OAUTH_SETUP.md.
2. ANTHROPIC_API_KEY in .env + USE_CLAUDE=true to switch live drafting to Claude (mock works without).
3. Attorney review of privacy policy + terms (PRD hard blocker OD6) — pages carry visible "pending review" notices.
4. Staging deploy (needs go-ahead — touches GCP bill + live URL).

## Tech debt
- llm_service.py 634 lines (>300 rule, predates the rule). Split candidates: mock-response strings, prompt builders.
