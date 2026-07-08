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
