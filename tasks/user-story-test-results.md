# User-Story Feature Test Results — 2026-07-09/10

Executed against a locally running stack on branch `fix/known-issues`:
backend `uvicorn app.main:app` on 127.0.0.1:8000 with a dedicated SQLite DB
(`story-test.db`), `USE_MOCK_LLM=true`, rate limiting ON; CRA dev server on
:3000. Stories were driven through the exact API contract the frontend uses
(verified against `frontend/src/services/api.ts`), with frontend wiring
checked at source + dev-server level. Driver scripts: `/tmp/story-tests/`,
PDF artifacts: `/tmp/story-tests/artifacts/`.

Baselines before stories: backend 381 passed / 3 xfailed; frontend 28 suites,
205 tests passed. Re-run after stories: see Review section.

## Scorecard

| Story | Persona / flow | Result |
|---|---|---|
| 1 | Maria — RFO custody+support, full happy path + resume/edit | 24 pass / 2 findings (F2, F5) |
| 2 | David — served FL-300 → FL-320 response + deadline math | 15 pass / 0 fail |
| 3 | Rosa — San Diego violations, all 3 tracks | **BROKEN — F1 (critical)** |
| 4 | James — case-first gameplan → form execution | 8 pass / F3 found |
| 5 | Evidence — batch OCR, bulk text, upload, delete, storage failure | 12 pass / F4 found |
| 6 | Security — 401s, cross-user, rate limits, PII logs | 6/6 pass, logs clean |

## What works end-to-end (verified, not assumed)

- **Signup → profile → RFO intake → mock rewrite → evidence → PDF download.**
  Maria's 7-page FL-300 packet contains her party names, case number, county,
  custody/support content, and the evidence exhibit page (verified by PDF text
  extraction). Filename derives from her case number.
- **Resume/edit intake** (the orphan-motion remediation): abandon at step 3,
  re-login, summary shows partial progress, resubmitting a step updates the
  existing draft instead of duplicating.
- **FL-320 response flow** exactly as the frontend drives it (upload gate →
  client-template steps → drafts → process → 3-page PDF with David's data).
  Served-motion endpoint: honest "type it in" notice under mock LLM; rejects
  .txt (400), corrupt PDF (graceful notice, not 500), >10MB (413).
- **9-court-day response deadline**: ran the real `courtDays.ts` — served
  Wed 2026-07-15 → "Tuesday, July 28, 2026" (matches hand computation);
  weekend-served edge also correct. (Court holidays deliberately out of scope.)
- **Gameplan flow degrades honestly on mock LLM**: real `gameplanParser`
  returns `isFallback: true` with the generic checklist — no fake
  personalized plan. Form-execution loop (drafts → complete → PDF) works.
- **Evidence**: bulk text import, tag whitelist enforcement, file upload to
  local storage (file verified on disk), update/delete, batch-OCR honest
  notice with flag off, Gmail endpoints 404 with flag off, no orphan DB row
  after a failed upload.
- **Security remediations hold**: 8/8 endpoints 401 unauthenticated;
  cross-user access denied on 7 operations (get/evidence/draft/download/
  delete/process); no WebSocket route; `llm/rewrite` 429 at request #21;
  auth brute-force 429; **backend log contains zero PII** (no names, case
  numbers, message content, or passwords — only IDs/counts/flags).
- **UI wiring**: LegalFooter mounted app-wide (`App.tsx:183`), FilingChecklist
  on preview (`MotionPreview.tsx:176`), Gmail UI behind `gmailEnabled()`.

## Findings (report-only; nothing was fixed)

### F1 — CRITICAL: San Diego violation filing is completely broken
`POST /api/v1/violations/process` returns 500 for **every** user (with or
without a profile). `violations.py:69` reads `current_user.profile` — a
lazy-loaded relationship (`app/models/user.py:28`) — in an async context,
raising SQLAlchemy `MissingGreenlet`; the broad `except Exception` masks it
and leaks the raw SQLAlchemy message to the client. No track determination,
no declaration, no motion row — the entire Flow D dies at intake submit.
The surrounding endpoints (`/tracks`, `/forms/{track}`,
`/generate-declaration`) all work; only the core one is dead.
*Why unit tests miss it: they don't execute this endpoint through a real
async session + real `get_current_user`.*
Fix direction: eager-load (`lazy="selectin"`) or query the profile
explicitly; and stop `except Exception` from re-wrapping HTTPExceptions.

### F2 — MEDIUM: backend intake condition evaluator breaks on OR + includes
`app/services/intake.py:36` checks `.includes(` before `||`, so conditions
like `relief_categories.includes('child_support') || …` always evaluate
false. Effect on `/intake/rfo/*`: the Support Details step is silently
skipped for users requesting support, and `best_interest_factors` is never
asked for custody cases. **Mitigating fact discovered during testing:** the
production frontend doesn't use `/intake/rfo/*` at all — it uses client-side
templates + `POST /motions/{id}/drafts`, and the client evaluator
(`conditionEval.ts`) handles `||` first, correctly. So user impact today is
nil, but the API is exposed and wrong — fix or fold into the dead-code
cleanup already listed in tasks/todo.md.

### F3 — MEDIUM: gameplan response extraction doesn't match the chat API shape
`extractResponseText` (`frontend/src/utils/gameplanParser.ts`) looks for
`response.response`, but `POST /chat/messages` returns
`{response: {message: {content: …}}}`. The extractor therefore
JSON.stringifies the whole envelope. Under mock it lands on the honest
fallback, but with a real LLM the "analysis" shown to the user would be raw
JSON, and form-code detection would scan JSON noise. Fix: read
`response.message.content` first.

### F4 — LOW: local-disk storage failures bypass the friendly 502
`_save_to_disk` (`app/services/evidence_storage_service.py:71-76`) raises raw
`PermissionError`/`OSError`, but the upload endpoint only catches
`EvidenceStorageError` (`evidence.py:202-207`) → user gets a bare 500 instead
of the designed "nothing was saved, try again" 502. Still loud, no orphan
row (verified). Supabase/GCS paths (production) wrap correctly. Wrap the
disk path too.

### F5 — LOW: motion create response omits `case_number`
`POST /motions/` returns `case_number: null` even when the profile has one;
GET list/detail return it correctly. Frontend renders from GET, so impact is
cosmetic inconsistency in the create response.

### F6 — LOW: UPL copy leftover in CaseIntake
Remediation renamed "legal strategy" → "action plan" (done in Dashboard,
GameplanCreation, FormExecution), but `CaseIntake.tsx` still shows
user-facing "Create Legal Strategy" (button, line 265), "personalized legal
strategy" (line 277), and a placeholder mentioning "legal strategy"
(line 213). (Occurrences inside LLM prompts and Terms.tsx are fine.)

### Informational (no action urgency)
- Gmail-flagged endpoints return 422 for malformed bodies before the 404
  flag check — endpoint existence is discoverable; functionality still gated.
- 429 responses carry no `Retry-After` header.
- App `<title>` is still "React App".
- Registration rejects reserved TLDs (`user@x.test`) via email-validator —
  correct behavior, but worth knowing for test data.

## What mock-LLM testing could NOT validate
- Quality/accuracy of rewrites, declarations, best-interests enhancement.
- Real gameplan analysis and form recommendations (F3 will bite here first —
  fix before real-LLM testing).
- Served-motion field extraction (mock always returns the honest notice).
- OCR (flag off) and Gmail import (flag off + no OAuth creds).
Re-run Stories 1–4 with `ANTHROPIC_API_KEY` + `USE_CLAUDE=true` once the key
exists (launch blocker #1).

## Review

- Environment intact after testing: backend suite re-run green, frontend
  suite re-run green (see todo.md review section for the run stamps).
- Test users created (password pattern `<Name>Str0ng!pass`):
  maria.story@ / david.story@ / rosa.story@ / james.story@example.com in
  `story-test.db` (disposable; delete the file to reset).
- Suggested fix order: F1 (feature dead) → F3 (blocks real-LLM launch
  testing) → F6 (compliance copy) → F2/F4/F5 (with the dead-code cleanup).

## Fix addendum (2026-07-10)

All findings fixed TDD-first on `fix/known-issues` (9 commits, one per fix):

- **F1 fixed** — explicit Profile query replaces the lazy relationship access;
  HTTPExceptions pass through; generic 500 detail. Fixing it surfaced two more
  layers, both fixed: courthouse determination crashed on None city/zip (the
  profiles API never collects them), and violation motions couldn't generate
  PDFs (`generated_text`, no drafts — documents now synthesize a declaration
  section). New `tests/test_violations.py` (8 tests) drives the endpoint through
  a real async session. Story 3 driver: was 10 pass/4 fail → **15/15**.
- **F3 fixed** — `extractResponseText` reads `response.message.content` first;
  envelope test added from the recorded live shape.
- **F2 fixed** — `||` splits before `.includes(`; new `tests/test_intake_conditions.py`.
- **F4 fixed** — `_save_to_disk` wraps OSError in `EvidenceStorageError` → 502.
- **F5 fixed** — create response resolves `case_number` via `_user_case_number`.
- **F6 fixed** — CaseIntake copy now "action plan"; `CaseIntake.test.tsx` guards it.
- **Nits** — app title set; 429s carry `Retry-After`. Gmail 422-before-404
  accepted as-is (agreed scope).

Verification: backend 398 passed / 3 xfailed (+17 new tests), frontend 208
passed / 29 suites (+3 new), `npm run build` compiles, story1 driver 26/26,
story3 driver 15/15.
