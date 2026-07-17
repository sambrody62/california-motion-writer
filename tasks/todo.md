# Build Plan — Family Court Helper MVP (formerly California Motion Writer)

## Stripe subscription billing (2026-07-17, approved plan: ~/.claude/plans/buzzing-nibbling-emerson.md)
Decisions: $300 recurring every 3/6 months (interval set in Stripe dashboard via STRIPE_PRICE_ID);
paywall gates LLM drafting + PDF export (intake/gameplan/evidence free); hosted Checkout + customer
portal; 60-day money-back guarantee in offer copy (refunds manual via dashboard); guided-session
booking via external link (REACT_APP_SCHEDULING_URL). Branch: feat/stripe-billing.
- [x] S1 chore(billing): stripe~=15.3 dep, BILLING_ENABLED=false in conftest (24ac5f7)
- [x] S2 feat(billing): Subscription model + registrations (f0725c4)
- [x] S3 feat(billing): config settings STRIPE_* keys, FRONTEND_URL (991e354)
- [x] S4 feat(billing): 402 gate on llm.py router, documents generate-pdf/-sync + /download,
      chat_pdf generate-pdf + complete-workflow (d774c0b)
- [x] S5 feat(billing): stripe_service.py — idempotent webhook application, last_event_created
      guard, item-level current_period_end fallback for new Stripe API (e85934b)
- [x] S6 feat(billing): checkout/portal/status/verify endpoints + 10/hr checkout limit (2567939)
- [x] S7 feat(billing): POST /webhooks/stripe, real-HMAC signature tests. Gotcha: stripe v15
      StripeObject is not a dict — endpoint passes json.loads(payload) to apply (1f86968)
- [x] S8 feat(billing): billing.ts + isPaywallError (6030a8c)
- [x] S9 feat(billing): PaywallModal — $300, 60-day guarantee, 1-on-1 session copy (d417fce)
- [x] S10 feat(billing): GuidedIntake 402 → modal, returnTo /motion/{id}/edit/{lastStep};
      extracted intakeNavigation.ts to stay ≤300 (c69ae5b)
- [x] S11 feat(billing): MotionPreview 402 → modal; extracted utils/downloadBlob.ts (d15a007)
- [x] S12 feat(billing): BillingSuccess (verify-session + 5×2s status poll + scheduling link),
      BillingCanceled, BillingButton, /billing/* routes, Dashboard entry (e85169e)
- [ ] S13 Manual Stripe test-mode E2E — BLOCKED on owner: create test-mode Product/Price
      ($300 per 3 or 6 months) → STRIPE_PRICE_ID; sk_test key → STRIPE_SECRET_KEY;
      `stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe` → STRIPE_WEBHOOK_SECRET;
      set BILLING_ENABLED=true; save default portal config; dunning = cancel after retries fail.
      Verifies live: #-fragment success_url + {CHECKOUT_SESSION_ID} substitution.
      NOTE: user pasted a pk_live (publishable) key in chat — not usable server-side and
      live-mode; need sk_test via env, never in chat/repo.

### Review (2026-07-17)
Backend 589 passed / 3 xfailed; frontend 43 suites / 280 passed; prod build compiles
(pre-existing exhaustive-deps warnings only). Gate default: BILLING_ENABLED unset → billing ON
in prod code path (`getenv("BILLING_ENABLED", "true")`) but conftest forces false for tests —
deploy must set STRIPE_* secrets or gated endpoints 402 with no way to pay (checkout 503s until
configured). Entitled statuses: active/trialing/past_due (past_due grace delegated to Stripe
dunning). Refunds: manual in dashboard; cancel the sub there to revoke access via webhook.


## Model upgrade + LLM checker (2026-07-14, approved: Opus drafter + Opus checker, no Gemini)
- [x] U1 feat(llm): drafting tier Sonnet 4.6 → Opus 4.8 (1ff81b6) — live-verified, drafts
      carry claude-opus-4-8, ~54s per motion (comparable to Sonnet)
- [x] U2 feat(llm): Opus semantic refute-pass (8e231b8) — one flag-only call per motion,
      findings render in the existing corrections banner, fail-open. Haiku stays on utility.
- [x] U3 Verified live twice. Run 1 exposed a REAL pre-existing bug the checker caught:
      blank draft values poisoned the backend intake merge → the gate was stripping GENUINE
      user facts ($3,200/$85/June 14) as unverifiable. Fixed in 9a83606 (merge_intake_values
      ignores blank overwrites; verbatim live DB shapes as fixtures). Run 2: all real facts
      survive in the PDF, checker flags now catch a real drafting quality issue (Opus writes
      [TO BE COMPLETED] for provided case number/county). Backend 544 passed / 3 xfailed.
      Follow-ups: dedup near-identical checker findings; extend gate placeholder-fill to
      case_number/county; frontend per-step-only saveDraft payloads (upstream fix for the
      draft-poisoning family).

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

## M6 — Served-motion upload for FL-320 responses (DONE 2026-07-07)
Respondents can upload the FL-300 they were served (PDF or photo) as a skippable gate
before step 1 of the response wizard; the backend extracts text (PyPDF2; Cloud Vision for
photos when OCR_ENABLED) and the LLM pulls structured facts that pre-fill the wizard with
a "Filled from your uploaded motion — please verify" indicator. Parse-only (file never
stored); date_served structurally excluded (user must enter it; deadline calc depends on
it); mock LLM degrades to a notice + manual entry. New: served_motion_parser.py,
endpoints/served_motion.py (POST /llm/parse-served-motion), ServedMotionUpload.tsx,
servedMotionApi.ts, QuestionField.tsx (extracted from GuidedIntake, now 493 lines).
Suites: backend 311, frontend 173. Live-driven: upload path (gate → notice → wizard) and
skip path (wizard + deadline banner), curl smoke 200/400/401.
- Follow-up ticket: scanned-PDF OCR needs Vision batch_annotate_files (current
  ocr_service only accepts image bytes) — scanned PDFs get an honest "couldn't read
  this file" notice today.
- Real-extraction verification pending ANTHROPIC_API_KEY (launch blocker #2).

## M7 — Smart Evidence Finder (DONE 2026-07-07)
Four workstreams (order D→C→B→A), all TDD, all with mock-LLM graceful degradation:
- D. Court-ready exhibit formatting (exhibit_formatting.py, mechanical): declarant
  authentication ("true and correct copy") under the perjury clause, INDEX OF EXHIBITS
  with verified page numbers, case-caption header on every exhibit page, Page N of M
  stamps. Supersedes the old "Supporting exhibits:" paragraph.
- C. Claim-to-exhibit citations (claim_citation_service.py): LLM inserts "(Exhibit X)"
  inline; zero-drift guardrail (strip-citations + normalized-equality + letter whitelist,
  20s timeout); any doubt → original text, never blocks PDF.
- B. Bulk text-screenshot import: POST /motions/{id}/evidence/batch-upload (analysis
  only, ≤20 png/jpg, persists nothing) → OCR → conversation_threading LLM merge →
  BulkTextImport/BulkTranscriptReview UI (route /motion/:id/evidence/bulk-import) →
  single confirm via evidence create with user_confirmed (Bug-2 fix: EvidenceCreate
  silently dropped user_confirmed).
- A. Relevance-ranked Gmail scan (evidence_ranking_service.py): candidates ranked
  against intake claims (metadata only — bodies never reach the prompt), score/why/
  suggested-tag chips in GmailCallback, import accepts tags_by_message (validated);
  imports stay unconfirmed. Also fixed Bug-1: scan returned a bare array while the
  frontend expected {emails} (Jest mock had hidden it).
- Shared: llm_json.py (parse_llm_json extracted), 3 new Claude operations registered.
- Suites: backend 360 passed + 3 xfailed; frontend 184 passed. Live drive: bulk import
  (OCR-off degraded path: notice → manual transcript → tag → confirm) → evidence saved
  → packet downloaded with authentication text, INDEX OF EXHIBITS, caption headers,
  page stamps, transcript in Exhibit A. Zero console errors / failed requests.
- Real-LLM quality passes (ranking, threading, citation fallback rate) pending
  ANTHROPIC_API_KEY (launch blocker #2).

## M8 — Claude vision for chat screenshots (DONE 2026-07-08)
Bulk screenshot import now reads chat bubbles directly with Claude vision when the
Claude backend is live: ClaudeLLMService.generate_with_images (base64 image blocks,
screenshot_reading op on haiku, 6000 tokens), text_thread_service.read_screenshot_images
(bubble-side sender attribution in the prompt; sanitized JSON; returns None on any
failure), evidence_batch tries vision first with size guards (4.5MB/image excluded,
20MB/batch skips vision) then falls back to OCR+threading, then manual. Response schema
unchanged — zero frontend changes. Suites: backend 370, frontend 184. Live re-drive of
the evidence flow: identical to M7's verified behavior (no regression). Vision quality
verification pending ANTHROPIC_API_KEY.

## DEPLOY CHECKLIST — Supabase evidence storage (config only, code complete)
1. Supabase dashboard → Storage → create bucket `evidence` → **Private** (never public;
   legal evidence).
2. Render dashboard → env secrets: SUPABASE_URL, SUPABASE_SERVICE_KEY (render.yaml
   already sets STORAGE_BACKEND=supabase and SUPABASE_EVIDENCE_BUCKET=evidence).
3. Post-deploy smoke: upload one evidence file; its storage_path must start
   `supabase://evidence/`. Free tier = 1 GB (~hundreds of exhibits); Pro $25/mo = 100 GB.
4. Later, if a "view original file" feature is added: serve via time-limited signed URLs.

## LAUNCH-BLOCKING (user actions, none are code)
1. Google OAuth verification — submit gmail.readonly (weeks; test mode works for 100 users now). See docs/GOOGLE_OAUTH_SETUP.md.
2. ANTHROPIC_API_KEY in .env + USE_CLAUDE=true to switch live drafting to Claude (mock works without). Now also unlocks: evidence ranking, screenshot threading, claim citations, and vision reading of chat screenshots.
3. Attorney review of privacy policy + terms (PRD hard blocker OD6) — pages carry visible "pending review" notices.
4. Staging deploy (needs go-ahead — touches Render/Vercel/Supabase; see deploy checklist above).

## Tech debt
- llm_service.py 634 lines (>300 rule, predates the rule). Split candidates: mock-response strings, prompt builders.

## Remediation: 10 Design-Review Findings (branch fix/known-issues, 2026-07-08)

Plan: ~/.claude/plans/temporal-whistling-engelbart.md. TDD; one conventional commit per step.

- [x] R1. refactor(api): remove dead WebSocket chat endpoint
- [x] R2. refactor(frontend): remove chat entry points and dead chat UI
- [x] R3. refactor(auth)!: backend JWT only; delete Firebase layer
- [x] R4. fix(intake): edit/resume loads existing motion (no orphan drafts)
- [x] R5. fix(intake): surface step save/load failures inline with retry
- [x] R6. fix(preview): only claim legal-format rewrite when LLM output exists
- [x] R7. fix(gameplan): honest fallback when personalized plan unavailable
- [x] R8. fix(copy): replace UPL-risky "legal help/strategy" language
- [x] R9. feat(legal): global disclaimer footer; FilingChecklist after PDF download
- [x] R10. fix(evidence): delete confirmation + error surfacing
- [x] R11. fix(storage): evidence upload fails loudly on backend storage errors
- [x] R12. feat(api): enforce rate limits on LLM, PDF, auth routes
- [x] R13. fix(logging): strip PII logging; gate SQL echo behind SQL_ECHO

### Review (2026-07-08)
All 13 remediation items implemented TDD-first on `fix/known-issues` (13 commits + build fix).
- Backend: 381 passed, 3 xfailed. Frontend: 205 passed, 28 suites. `npm run build` compiles.
- New tests: test_ws_removed, test_evidence_storage_failure, test_rate_limiting, test_logging_hygiene (backend); FlowSelectors, Auth, GuidedIntakeResume, GuidedIntakeErrors, GameplanCreation, gameplanParser, LegalFooter, EvidenceDelete, ProfileSetup (frontend).
- 300-line rule: GuidedIntake 296, GameplanCreation 284, MotionPreview 289, rate_limiter 184 (extractions: useMotionInit, useIntakePrefill, IntakeStepForm, IntakeProgress, IntakeNotices, IntakeErrorBanner, gameplanParser, GameplanSections, EnforcementTriage, MotionPreviewBanners, rate_limit_config, usage_quotas).
- Deferred (known follow-ups): delete dead backend services/main_local.py (its /ws is unreachable), Firebase root artifacts (firebase.json etc.), cost counters to DB, docs rewrite (CLAUDE.md/README still describe GCP).
- Pre-existing, untouched: 4 tsc --noEmit errors in old test files; exhaustive-deps lint warnings.

## User-Story Feature Test Pass (2026-07-09/10)

Full report: tasks/user-story-test-results.md. Six personas driven end-to-end
against the live local stack (mock LLM, rate limits ON, fresh story-test.db).
Baselines green before AND after (backend 381 passed/3 xfailed; frontend 205 passed).

Works verified end-to-end: RFO signup→PDF (7-page packet, data verified in PDF text);
intake resume/edit; FL-320 served-motion gate + 9-court-day deadline (real courtDays.ts);
gameplan honest fallback; evidence CRUD/batch/upload; all Story-6 security checks
(401s, cross-user isolation, rate limits 429, zero PII in logs).

Bugs found (reported, NOT fixed):
- [x] F1 CRITICAL: /violations/process 500s for every user — lazy `current_user.profile`
      in async context (violations.py:69, MissingGreenlet); whole violation flow dead.
- [x] F2 MEDIUM: intake.py:36 evaluates `.includes(` before `||` — support step skipped /
      best-interests never asked via /intake/rfo/*. NOTE: frontend doesn't use this API
      (client templates + drafts); candidate for the dead-code cleanup instead.
- [x] F3 MEDIUM: extractResponseText (gameplanParser.ts) reads response.response but chat
      returns response.message.content → real-LLM gameplan would render raw JSON.
      Fix BEFORE real-LLM testing (launch blocker #2 unlock).
- [x] F4 LOW: _save_to_disk OSError not wrapped in EvidenceStorageError → raw 500, not
      the friendly 502 (prod supabase path is correct).
- [x] F5 LOW: POST /motions/ response omits case_number (GETs have it).
- [x] F6 LOW (UPL/compliance): CaseIntake.tsx lines 213/265/277 still say "legal strategy"
      — R8 leftover; Dashboard/GameplanCreation/FormExecution already say "action plan".
- Info: gmail-flagged routes 422 before 404 on malformed bodies; 429s lack Retry-After;
  app <title> still "React App".

### Fix pass review (2026-07-10)
All 6 findings + 2 nits fixed TDD-first on fix/known-issues (9 commits):
violations MissingGreenlet + None-city courthouse, gameplan extractResponseText,
intake || ordering, disk EvidenceStorageError wrap, create-response case_number,
CaseIntake UPL copy, app title, Retry-After on 429s, and violation-motion PDF
generation (found during re-verification: violations store generated_text, no drafts).
Backend 398 passed (+17 new), frontend 208 passed (+3 new, 29 suites), npm build OK.
Live re-verification: story1 26/26, story3 15/15 (was 10 pass/4 fail).
Gmail 422-before-404 accepted as-is (agreed scope).

### Trust design research + spec (2026-07-10)
Deep-research run (24 sources, 118 claims, 25 adversarially verified 3-vote, 24 confirmed)
plus 3 targeted gap agents (trauma-informed/quick-exit, typography, legal-tech/UPL).
Deliverables: docs/design/trust-design-research.md (cited findings by dimension) and
docs/design/design-spec.md (palette anchored on civic blue #1d70b8, all pairings
WCAG-AA computed; Public Sans 17px/1.5; Quick Exit hardening spec incl.
location.replace(); 3-tier UPL disclaimer; manifest/favicon branding fixes).
No frontend code changed — implementation order is in the spec. Found during
verification: index.html title/description already fixed; manifest + favicons still stock CRA.

### Trust re-theme, spec steps 1-3 (DONE 2026-07-10)
Branch feat/trust-theme, 4 commits (docs, feat(theme), refactor(theme), chore(branding)).
Tokens: civic-blue primary scale (#1d70b8 anchor) + success tokens in tailwind.config.js;
Public Sans 400/600/700 via @fontsource; 17px/1.6 base. Migration: 267 indigo + all
ad-hoc blue/purple classes → primary/success across 34 files; step circles unified;
'filed' badge now solid success; legal pages max-w-[65ch]. Branding: M-monogram
favicon/logo192/logo512 (SVG→qlmanage→PNG-in-ICO), manifest + theme-color #1d70b8.
Verified: 208 frontend tests pass, prod build clean (pre-existing lint warnings only),
headless-Chrome visual QA of login page. Note: types/forms.ts color field is dead data
(nothing consumes it). Remaining spec steps: 4 (Quick Exit hardening), 5 (microcopy pass).

## Real-LLM Browser Test Pass (2026-07-10)

Scope: LLM output quality + real browser E2E only (mock-LLM pass already verified wiring/
security/PDF — do not re-test at API level). Full plan in the prompt; results will go to
tasks/real-llm-browser-test-results.md. Stack: backend uvicorn on 127.0.0.1:8000 (fresh
browser-test.db, rate limits off), CRA on :3000, Playwright-driven Chromium.

- [x] P1. Billing pre-flight: one tiny real Messages call (passed — real completion)
- [x] P2. Backend up on 127.0.0.1:8000 with fresh SQLite (caught: backend never loads
      .env itself — must export USE_CLAUDE/ANTHROPIC_API_KEY in the shell or it silently
      boots mock)
- [x] P3. Frontend on :3000 — running instance had stale REACT_APP_API_URL=8010 baked in
      (dead port; every real browser call failed); restarted mid-pass with 127.0.0.1:8000
- [x] P4. Playwright chromium ready in /tmp/real-llm-browser-test
- [x] Flow 1: RFO real rewrites — PARTIAL: E2E works, prose quality high, but 3 CRITICAL
      fabrications (party-role swap, invented $3,200/mo support demand, wrong kids' ages)
      + wrong primary form on PDF (FL-320 for an RFO; pdf_packet_service.py:29)
- [x] Flow 2: Gameplan — PARTIAL: extractResponseText fix CONFIRMED live (no raw JSON),
      real form recs incl. apt FL-410; but Case Analysis renders an echoed prompt
      fragment, and form-execution completion never registers
- [x] Flow 3: FL-320 extraction — PARTIAL: case number exact, deadline banner exactly
      right (Thu Jul 23 2026), fields editable; but petitioner misidentified, extracted
      requests wiped before render, generated response mislabeled/fabricates
- [x] Flow 4: Violation — PARTIAL: #/violation/intake CRASHES for every real user
      (API/frontend shape mismatch, invisible to the API-level mock pass); declaration
      (via shim) structurally excellent but 2 sworn embellishments + wrong statute cite
- [x] Flow 5: UX sweep — spinners always present, footer everywhere, FilingChecklist
      correct; only console noise is 3x benign /profiles/me 404s (+ the L5 crash)
- [x] Wrap-up: full report in tasks/real-llm-browser-test-results.md (19 findings, L1-L19
      + env notes); test backend killed; OCR/Gmail remain untested (flags off, out of
      scope until Google OAuth verification)

VERDICT: LLM layer NOT yet safe to file from — confidently fabricated specifics inside
otherwise court-appropriate prose. Launch gate: post-generation fact-check against intake
data + strip uninvited legal authority + markdown rendering. Cost: 28 upstream Claude
calls, well under $1.

### Fix pass review (2026-07-11, branch fix/real-llm-findings)
All L1–L19 fixed TDD-first: 30 commits (27 planned + 2 regression fixes + docs).
Backend 520 passed/3 xfailed (+122), frontend 252 passed/36 suites (+44), build clean.
- fact_gate package (deterministic: markdown/authority strip, placeholder fill, party-role
  correction, amount/date/age verification vs intake+profile, flag-only UPL/quantifiers)
  gates every RFO/FL-320 section + violation declaration before save; corrections persist
  in motions.fact_check (idempotent schema upgrade) and render as an amber review banner.
- Prompt root cause removed: llm_service instruction #5 told the LLM to "Include relevant
  California Family Code sections" — deleted; party/fact anchors added.
- Live re-verification (real Claude, browser): 4/4 checks pass — ages/roles/amounts clean,
  FL-300 form correct, violation flow usable end-to-end, 1 chat call per gameplan submit,
  extraction drops unevidenced ages, prefill lands, deadline math exact.
- Verification caught what suites couldn't: the C3 reorder regressed cross-step conditional
  questions (blank re-registration shadowing/poisoning allAnswers) — fixed in 29f2da8 +
  2084eb5 with the evaluator-stub test gap closed.
- Deferred (tracked in report addendum): resumeAnswers re-poisoning on resume,
  party-block templating, structured-JSON gameplan, ex-parte alias, progress staging,
  Dashboard badge key. RESOLVED same day: rate limiter → pure ASGI (fix/asgi-rate-limiter,
  481c0ae) — live re-check shows the LLM loop stops after 1 section call on client
  disconnect (was 3); PR #5 (all L1-L19 work) merged to main.

### Rename to Family Court Helper (DONE 2026-07-10)
User's final call after 3-round naming exercise (Camino was recommended runner-up;
CourtReady/Court Compass/Poppy/Kidside/StrongSuit etc. all collision-burned).
feat(brand) commit: Dashboard header, LegalFooter/Terms/Privacy, index.html title,
manifest (Family Court Helper / Court Helper), F monogram icons, README + design docs,
3 test assertions. 208 tests pass, build clean.
ACTION REQUIRED (user): register familycourthelper.com — verified UNREGISTERED 2026-07-10.
