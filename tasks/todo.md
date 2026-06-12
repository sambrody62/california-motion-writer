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
