# Lessons

## 2026-07-07 — E2E bug-fix round

1. **Jest mocks must mirror the real helper's return shape, not the axios response.**
   `motionAPI.getDrafts()` returns an unwrapped array, but every test mocked it as
   `{data: {drafts: [...]}}`. Components were built against the mocks, passed CI, and
   crashed on the first real request. When adding a mock for an api.ts helper, copy the
   shape from the helper's return statement (or better, its TS return type) — never from
   what axios would return.

2. **`(x as any)` on an API helper call disables the only guard against contract drift.**
   The saveDraft positional-args bug (`saveDraft(id, step, data)` vs `saveDraft(id,
   payload)`) type-errors without the cast. Treat `as any` on service-layer calls as a
   review blocker.

3. **FastAPI: routers that declare their own `prefix=` must be included without one.**
   Doubled prefixes (`/violations/violations/...`) 404'd every frontend call for entire
   features. The route contract is now pinned by tests/test_e2e_regressions.py, which
   asserts exact paths against `app.routes` — extend it when adding routes the frontend
   calls.

4. **Plain `enum.Enum` members never equal their `.value` string.**
   `motion.motion_type == "RFO"` is always False for `MotionType.RFO`, and f-strings
   render `MotionType.RFO`. Normalize with `.value` at boundaries (or use `(str, Enum)`
   for new enums).

5. **`navigate('/path')` targets must exist in App.tsx.** GuidedIntake returned to
   `/form/execution` (no such route) → silent blank page. When adding navigation,
   grep App.tsx for the target path.

6. **Verify by driving the live app, not only test suites.** Both suites were green
   while the core user flow was unusable (wrong mocks, missing route). The Playwright
   run found two bugs the suites structurally could not.

## 2026-07-08 — fix/known-issues session
- Run frontend tests via `npm run test:ci` (react-scripts), never `npx jest` directly — bare jest skips CRA's babel/TS transform and every suite fails with syntax errors.
- Don't chain `test | grep pattern && git commit` — grep matching output lines returns 0 even when tests failed. Check the summary line explicitly before committing (one commit briefly landed with a failing test and needed --amend).
- Under Jest, react-router-dom v7 only exposes `BrowserRouter`/`Router`; `MemoryRouter` is undefined. Use `BrowserRouter` + `window.history.pushState` for route-dependent tests (existing pattern in Dashboard.test.tsx).
- Jest's babel transform accepts JSX the production build rejects (e.g. `unknown && <jsx>` children → TS2746). Run `npm run build` before finishing any component extraction.
- Backend evidence upload form field `tags` expects a JSON array string ('["threat"]'), not a bare tag name.

## 2026-07-11 — real-LLM browser test + fix pass (fix/real-llm-findings)
- **The envelope-mock disease recurred a third time**: ViolationIntake's Jest mock encoded
  a stepped question shape the real API never returned, so the suite was green while
  #/violation/intake crashed for every user. Rule: any Jest mock of an API response must be
  generated from (or verified byte-exact against) the real endpoint output, not written
  from the component's expectations. When a mock and a component agree but production
  crashes, the mock is the lie.
- **Prompts can contradict guardrails**: UPL_GUARDRAILS said "NEVER invent facts" while the
  rewrite prompt itself instructed "Include relevant California Family Code sections where
  appropriate" — the LLM obeyed the specific instruction over the general prohibition and
  fabricated statutes/local rules/case law. Audit prompt instructions against guardrails as
  a pair; the most specific instruction wins.
- **LLM output that must be factually faithful needs a deterministic post-generation gate,
  not just prompt hardening** — real-Claude output fabricated party roles, ages, and a
  support amount despite explicit "never invent facts" prompt language. Validate against
  the source-of-truth data (intake/profile) in code.
- **Mock-LLM green ≠ real-LLM safe**: every flow passed the mock pass; the first real-LLM
  browser run produced 4 critical fabrication classes. Anything user-facing that renders
  LLM output needs at least one live-model verification before launch.
- **`request.is_disconnected()` does not fire behind BaseHTTPMiddleware** (verified live):
  a curl-aborted client left the 6-section LLM loop running to completion. The
  `should_abort` hook is in place but inert until the rate limiter becomes pure ASGI
  middleware (deferred ticket).
- **Subagent sandboxes may allowlist only exact command forms** (full-suite
  `./venv/bin/python -m pytest tests/ -q` allowed; targeted single-file pytest denied).
  When an agent reports blanket Bash denial, check whether the exact approved invocation
  still works before assuming total loss.
