# Real-LLM Browser Test Results — 2026-07-10/11

First test pass with the live Claude backend (`USE_CLAUDE=true`, real `ANTHROPIC_API_KEY`)
and the first pass driven entirely through the browser (Playwright/Chromium clicking the
real UI at localhost:3000). Backend: `uvicorn app.main:app` on 127.0.0.1:8000, fresh
`browser-test.db`, `RATE_LIMIT_ENABLED=false`. Scope per plan: LLM output quality + browser
UX only — flow wiring/security/rate-limits/PDF plumbing were verified in the 2026-07-10
mock pass (tasks/user-story-test-results.md) and were NOT re-tested at the API level.

Artifacts (screenshots per step, downloaded PDFs, raw agent JSON):
`/tmp/real-llm-browser-test/artifacts/`. Test scripts: `/tmp/real-llm-browser-test/*.js`.

## Scorecard

| Flow | What was tested | Result |
|---|---|---|
| 1 | RFO: register → SD profile → messy FL-300 intake → real rewrite → preview → PDF | **partial** — flow works E2E; 3 critical fabrications in the rewrite; wrong primary form on PDF |
| 2 | Gameplan: /case/intake → real analysis → form-execution loop | **partial** — no raw JSON (fix works live), real forms recommended (incl. apt FL-410); but "Case Analysis" renders an echoed prompt fragment, and form completion never registers |
| 3 | FL-320: upload flow-1 PDF → real extraction → prefill → deadline banner → response gen | **partial** — extraction half right; deadline banner exactly correct; generated response has fabrications |
| 4 | Violation: regular-track declaration quality | **partial** — intake page crashes for real users; declaration (via shim) structurally excellent, 2 sworn embellishments |
| 5 | UX sweep (spinners, footer, checklist, console) | **pass with notes** — spinners always present, footer everywhere, checklist correct; 129s single-spinner wait |

Overall verdict: **the LLM layer is not yet safe to file from.** Structure and tone are
genuinely court-appropriate — the failure mode is not gibberish, it is confidently
fabricated specifics (party roles, ages, a support amount, statutes, courthouse addresses)
embedded in otherwise-excellent prose. Every fabrication below is disqualifying for a
filed document. A post-generation fact-check layer against intake data (+ stripping
uninvited legal authority, markdown → plain text) is the launch gate.

## Budget

28 upstream `POST api.anthropic.com/v1/messages` calls across all four flows (+1 billing
pre-flight ping). One `process-motion` fans out to 6 upstream calls (one per intake
section) and takes ~120–130s; `parse-served-motion` ~2s; violation declaration ~29s;
gameplan chat ~10s. No retry loops observed anywhere (per-action counts verified
in-browser). One waste pattern confirmed live: React StrictMode double-fires the
gameplan mount effect → 2 paid Claude calls per intake submit in dev (see findings).
Estimated total spend: **well under $1** — within the $2 budget.

## Flow 1 — RFO with real rewrites (partial)

E2E through the UI: register `maria.realllm3@example.com` → San Diego petitioner profile
(Maria Delgado vs Jacob Delgado, case 24FL009812N, kids Sofia DOB 2018-03-22 / Mateo DOB
2020-11-05) → all 6 guided FL-300 steps with realistic messy answers → 1×
`POST /llm/process-motion` (200 in 129.4s, spinner shown throughout) → preview showed
LLM output for all 6 sections → PDF downloaded (`FL-300-24FL009812N.pdf`, 15 pages).
PyPDF2 confirms the rewritten text (not the raw run-ons) landed on the form, with party
names, case number, and every user date/amount present.

Rewrite quality — quotes and verdicts:

> "On or about June 14, 2026, a Saturday, Petitioner and the minor children waited at the
> designated location for Respondent to arrive for his scheduled visitation. Respondent
> did not appear. … Petitioner and the children waited approximately forty-five (45)
> minutes before returning home."

**usable-with-edits** — the facts-declaration section is excellent: every user fact
preserved, correctly formalized, nothing invented in this passage.

> "2.1 Petitioner is **Jacob Delgado**. 2.2 Respondent is **[TO BE COMPLETED]** … the
> supporting Declaration of Jacob Delgado, filed concurrently herewith."

**broken** — party-role swap. Jacob is the opposing party; the filing names him as movant
and declarant. Printed onto the court PDF.

> "Order Respondent to pay Petitioner child support of no less than **$3,200.00 per
> month**, allocated between Sofia Delgado and Mateo Delgado."

**broken** — $3,200 was entered as the petitioner's *own monthly income*; no support
amount was ever requested. Invented demand, on the PDF.

Children's ages rendered as 6 and 4 (entered: 8 and 5 — contradicted by the DOBs printed
in the same table). Also invented: two conflicting Self-Help Center addresses, "San Diego
Superior Court Local Rule 5.5.2", *In re Marriage of Burgess* cite, and unrequested
FL-150/Earnings-Assignment/health-insurance relief (near-advice).

UX: profile-autofill indicator showed while fields stayed empty (filled manually);
FilingChecklist correctly appeared only after download; footer on every screen; spinner
("Reviewing your answers and drafting court language…") for the whole 129s wait.

## Flow 2 — Gameplan with real analysis (partial)

E2E through the UI: register `gameplan.realllm@example.com` → Riverside profile (Dana
vs Marcus Whitfield, case 23FL118234, kids Ava/Liam) → #/case/intake with a messy
custody-enforcement description (order dated Oct 12 2024, missed exchanges May 8 and
June 19 2026, McDonald's lot on Van Buren Blvd) → gameplan in ~10s (spinner shown) →
form-execution loop for FL-300 (all 6 steps → 121s process-motion → returned to
#/case/forms).

**Headline check — extractResponseText fix works with a real LLM.** The gameplan page
contains zero raw-JSON artifacts (no braces/quoted keys/escapes; the pre-fix behavior
would have dumped the chat envelope). The parser took the personalized path, and the
enforcement triage panel (RFO vs Contempt, neutral) rendered.

**Recommended forms are real and sensible** — FL-300, FL-320, FL-410. No hallucinated
form numbers; FL-410 (Order to Show Cause and Affidavit for Contempt) is genuinely apt
for an enforcement case. (FL-320 as a card for the *moving* parent is catalog noise,
not a hallucination.)

**But the analysis content itself is broken.** The entire "Case Analysis" section reads:

> "Help me prepare a Form FL-410 (enforce the order)."

**broken** — that is an echoed prompt/suggestion fragment, not an analysis of the
user's situation; none of the user's facts appear. The remaining sections
(Recommended Approach / Timeline / Key Considerations / Next Steps) render the generic
fallback checklist copy ("Review the California courts self-help resources for your
case type…") under a header claiming "your personalized action plan". No fabrications —
but only because no case-specific prose was rendered at all.

Form-execution loop mechanics: steps completed and drafts saved, spinner during the
121s process, returned to #/case/forms — but **the FL-300 card never marked complete**
(0 green/success cards; card still styled in-progress after full completion).
Step-1 profile autofill was empty again (second flow to reproduce). LLM traffic showed
2× `POST /chat/sessions` + 2× `POST /chat/messages` for one submit — the StrictMode
double-fire predicted from code recon, confirmed live (both calls paid, one discarded).

## Flow 3 — FL-320 served-motion extraction (partial)

Uploaded the actual flow-1 PDF at the upload gate as `respond.realllm@example.com`
(respondent profile, same case number). `parse-served-motion` → 200 in 1.9s, "Reading
your document…" indicator shown.

Extraction scorecard vs ground truth: `case_number` **correct** (24FL009812N, prefilled);
`petitioner_name` **wrong** (Jacob Delgado — it followed the uploaded doc's own
role-swap error instead of the caption "PETITIONER: Maria Delgado");
`hearing_date`/`hearing_time` **correctly left blank** (absent from PDF — no invention);
`date_served` **correctly never prefilled** (by design); `other_party_requests` extracted
faithfully but then **wiped before render** — step-2 textarea empty while the "Filled
from your uploaded motion — please verify" badge still displayed. Extraction also
returned Mateo "age 3" (appears nowhere in the document — invented; currently latent
because the frontend discards the children field). Prefilled fields verified editable
(edit sticks).

**Deadline banner: exactly correct.** date_served = Friday 2026-07-10 → banner
"Responses are typically due 9 court days after service: Thursday, July 23, 2026" —
matches independent computation.

Generated response quality: section 1 **broken** (titled "REQUEST FOR ORDER" for a
responsive declaration, names "Jacob Delgado (Respondent)" as Moving Party, and recasts
the user's date served as the movant's 16-court-day proof-of-service deadline against an
invented Aug 14 hearing); sections 2–3 **usable-with-edits** (core positions faithful to
typed input, good placeholder discipline, but "In re Marriage of Delgado" asserts a
marriage never entered, Sofia "(age 7)" wrong again, invented Local Rule 5.5.3 and
courthouse addresses).

## Flow 4 — Violation declaration quality (partial)

**`#/violation/intake` crashes to a blank screen for every real user** —
`GET /violations/intake-questions` returns the flat question map from
`forms/san-diego-violation/form-config.json` while `ViolationIntake.tsx` expects a
step/`questions[]` shape → `TypeError: Cannot read properties of undefined (reading
'map')`. The mock pass drove the API directly, so this frontend contract break was
invisible to it. To still judge LLM quality, the agent shimmed ONLY that metadata
response test-side; the submit, `POST /violations/process` (200, 29.2s, real Claude),
result page and PDF were genuine. Regular track correctly determined ("Regular Motion
track (3–6 weeks)").

Declaration quality — structurally the best output of the pass: 21 numbered first-person
paragraphs, violation-by-violation sections, exhibit references, penalty-of-perjury
clause, pro-per signature block, and disciplined `[TO BE COMPLETED]` placeholders instead
of invented names, with "in substance" hedges on quoted texts:

> "On **June 6, 2026**, approximately **20 minutes** before the scheduled exchange time,
> Respondent sent me a text message stating, in substance, **"not happening today."**"

**court-ready** (that paragraph). But two sworn-statement embellishments:

> "Throughout the weekend of June 20–22, 2026, Respondent's cellular telephone was turned
> off or otherwise unavailable."

**usable-with-edits** — "June 22" was never entered (the visitation weekend ends the
21st), and elsewhere "I attempted to reach Respondent by telephone on multiple occasions"
asserts a call count the user never stated. And one broken citation:

> "Issue **monetary sanctions** against Respondent pursuant to Family Code section
> 3027.1…"

**broken** — FC §3027.1 is sanctions for false child-abuse accusations, inapposite to
visitation denial. A pro per would file a wrong-statute request.

Post-generation: motion preview page shows **no declaration text at all** (violations
store `generated_text`, no drafts); PDF download works (8 pages) but leaks raw Markdown
(`**`, `###`, `&nbsp;`, table pipes) into the court document, and the declaration says
"[PETITIONER'S FULL LEGAL NAME]" while the FL-300 caption in the same PDF has the name.

## Flow 5 — Browser UX sweep (pass with notes)

- **Spinners**: present during every LLM wait in every flow (129s, 73s, 29s, 2s waits) —
  no blank screens. Long single-stage 129s wait has no progress increments (note below).
- **Disclaimer footer**: "Family Court Helper is a document-preparation tool. It does not
  provide legal advice…" on every screen tested (only exception: the crashed
  violation-intake blank screen).
- **FilingChecklist**: hidden before download, "San Diego County Filing Checklist"
  appears after download — per design.
- **Console**: clean except 3× benign `GET /profiles/me` 404s pre-profile (all flows) and
  the violation-intake TypeError crash.

## Findings

### Critical — LLM output (all print onto filed documents)
- **L1 Party-role swap**: RFO rewrite names the opposing party as Petitioner/declarant
  (Flow 1 §Case Information); FL-320 response names the respondent as "Moving Party"
  under a "REQUEST FOR ORDER" title and inverts service-deadline logic (Flow 3 §1).
  Repro: any intake with distinct party names; open preview.
- **L2 Invented support demand**: "Your Monthly Gross Income" = $3,200 becomes "order
  Respondent to pay child support of $3,200.00/month". Repro: Flow 1 step 4.
- **L3 Fabricated children's ages**: 6/4 vs entered 8/5 (Flow 1, contradicting DOBs in
  the same table); Sofia "age 7" (Flow 3); extractor invents Mateo "age 3" found nowhere
  in the uploaded document (Flow 3, latent — frontend discards the field today).
- **L4 Sworn-statement embellishments**: violation declaration extends unreachability
  through an un-entered "June 22" and asserts "multiple" call attempts never stated —
  in a document signed under penalty of perjury (Flow 4).

### Critical — application
- **L5 `#/violation/intake` blank-screen crash for every user**: frontend/API shape
  mismatch on `/violations/intake-questions` (`ViolationIntake.tsx` maps
  `undefined`). Entire violation flow unusable in the browser; invisible to API-level
  tests. Repro: log in → navigate to #/violation/intake.

### High
- **L6 Wrong Judicial Council form on RFO packets**: pages 1–2 of the FL-300 download are
  FL-320 "Responsive Declaration". Root cause found by test agent:
  `app/services/pdf_packet_service.py:29` `_FL300_TYPES = {"rfo", "violation"}` omits
  `"fl-300"` (documents.py's equivalent includes it) → `_primary_form('FL-300')` →
  FL-320. Repro: guided FL-300 → preview → Download PDF. (M5.2 regression class.)
- **L7 Uninvited legal authority & near-advice**: invented courthouse addresses (two,
  conflicting), "Local Rule 5.5.2"/"5.5.3", *In re Marriage of Burgess*, FC §3027.1
  (wrong statute), unrequested FL-150/earnings-assignment instructions. UPL-adjacent and
  unverifiable — should be stripped or sourced from app data. (Flows 1, 3, 4.)
- **L8 Markdown leaks into court documents**: literal `**`, `###`, `|` tables, `&nbsp;`,
  mojibake on preview and PDF declaration pages (Flows 1, 3, 4).
- **L9 Served-motion prefill dropped**: correctly-extracted `other_party_requests` never
  reaches the step-2 field, yet the "Filled from your uploaded motion" badge shows over
  the empty required field (2/2 runs); petitioner misidentified (follows the uploaded
  doc's internal error over its caption). (Flow 3.)
- **L10 Gameplan "Case Analysis" is an echoed prompt fragment, not analysis**: renders
  `"Help me prepare a Form FL-410 (enforce the order)."` and the other sections show the
  generic fallback checklist copy under a "personalized action plan" header. Not raw
  JSON (that fix holds), but the feature's core output is missing — the parser extracts
  the wrong piece of the live chat response. Repro: #/case/intake → submit → gameplan
  page (flow2-05-gameplan.png). (Flow 2.)

### Medium
- **L11 Duplicate motion per guided-intake entry**: paired `POST /motions/ 201` on every
  entry (React 18 StrictMode double-effect in `useMotionInit`, no idempotency guard) —
  orphan draft accumulates per visit. (Flow 1.)
- **L12 Profile-autofill race**: "Filled from your profile" indicators render while the
  fields stay empty (≥15s; reproduced in Flows 1 and 2).
- **L13 Form-execution completion never registers**: after completing all 6 guided FL-300
  steps from the gameplan loop and returning to #/case/forms, the form card stays
  in-progress (0 success-styled cards, `allFormsCompleted=false`). (Flow 2.)
- **L14 Violation preview shows no declaration text** — nothing to review before filing;
  `generated_text` isn't rendered as sections. (Flow 4.)
- **L15 Declaration placeholders for data the app stores**: "[PETITIONER'S FULL LEGAL
  NAME]" etc. while the same PDF's caption has the real names. (Flows 1, 4.)
- **L16 `/motion/new/response` dead end**: "Guided Forms" → perpetual "We couldn't load
  this step" (real cause: `No template found for form type: response`). (Flow 3.)
- **L17 No dashboard entry points**: no "Respond to a motion" CTA (FL-320 reachable only
  by direct URL) and no direct RFO start (only gameplan/enforce paths). (Flows 1, 3.)
- **L18 No LLM-call cancellation**: when the browser disconnected mid-`process-motion`
  (test run 2), the backend kept issuing Anthropic calls for the abandoned request —
  cost/resilience issue. (Flow 1, incidental.)
- **L19 StrictMode double-fires paid LLM calls in dev**: one gameplan submit → 2×
  `/chat/sessions` + 2× `/chat/messages` (~10s each, one discarded). Dev-only (StrictMode
  doesn't double-invoke in prod builds) but doubles real spend during dev testing; same
  root pattern as L11. (Flow 2, confirmed live.)

### Low / informational
- 307 trailing-slash redirects on `POST /profiles`, `GET/POST /motions` (+ `PUT
  /profiles/me` 404-then-POST dance); redirected cross-origin POSTs drop Authorization.
- Latent: violation checkbox (multiSelect) answers would serialize to `[]`
  (`ViolationIntake.tsx` `toArray()` vs object shape) once L5 is fixed.
- 3× console 404 `GET /profiles/me` noise pre-profile.
- 129s `process-motion` (6 sequential upstream calls) behind a single static spinner —
  works, but merits progress staging.
- Env (not repo): the long-running CRA dev server had stale
  `REACT_APP_API_URL=127.0.0.1:8010` in its shell env — every real browser API call hit a
  dead port until the server was restarted mid-pass (agents bridged it harness-side
  first; flows unaffected). Repo footguns worth fixing: `frontend/.env.local` says
  `localhost:8000` and **overrides** `.env`'s `127.0.0.1:8000` — `localhost` resolves to
  the IPv6 Docker squatter on this machine; and the backend never loads `.env` itself
  (`os.getenv` at import in `llm_service.py`), so an un-exported shell boots the mock
  silently even with `USE_CLAUDE=true` in `.env`.

## Fix addendum (2026-07-11)

All 19 findings fixed TDD-first on `fix/real-llm-findings` (30 commits: 1 docs, 27 planned
A1–A3/B1–B13/C1–C11, 2 regression fixes). Suites: backend **520 passed / 3 xfailed**
(+122 new), frontend **252 passed / 36 suites** (+44 new), `npm run build` clean.
Plan: ~/.claude/plans/plan-the-fixes-then-jolly-fiddle.md.

Centerpiece: **`app/services/fact_gate/`** — a deterministic post-generation gate (markdown
strip → authority strip → placeholder fill → party-role correction → amount/date/age
verification → flag-only UPL/quantifier scan) run on every RFO/FL-320 section and violation
declaration before DB write, with corrections persisted to a new `motions.fact_check` JSON
column (idempotent schema upgrade — no alembic) and surfaced to users as an amber
"We corrected or flagged N details" banner (motion preview + violation result). The prompts
that actively *caused* citation fabrication (llm_service instruction #5 "Include relevant
California Family Code sections", #6 local-rules compliance) were removed and replaced with
a no-authority redline plus per-motion party/fact anchor blocks.

**Live re-verification (real Claude, browser-driven): 4/4 checks pass.**
- RFO: ages rendered 8/5 matching DOBs (was 6/4), no party-role swap, the $3,200 income
  never became a support demand, zero invented statutes/addresses, zero markdown on the
  PDF, corrections banner shown, **PDF page 1 is FL-300 REQUEST FOR ORDER** (was FL-320);
  1 motion created per entry (was 2); step-1 profile prefill populates (was empty).
- Violation: #/violation/intake loads and completes (was a blank crash for every user);
  declaration uses real profile names (no "[PETITIONER'S FULL LEGAL NAME]"), no statute
  cites, no invented date ranges; corrections listed; preview shows the declaration.
- Gameplan: exactly 1 chat call per submit (was 2 paid); honest fallback instead of the
  echoed prompt fragment; form-execution completion registers (all-complete screen).
- FL-320: extraction names Maria Delgado as petitioner (was Jacob), drops unevidenced
  children's ages (no fabricated "age 3"), extracted requests land in step 2 (was wiped),
  deadline banner exactly matches independent computation (Thu Jul 23, 2026).

**Verification caught a regression the suites couldn't**: the C3 prefill reorder made
`reset()` re-register the previous step's fields as blanks, which shadowed (29f2da8) and
then poisoned via submit-spread (2084eb5) the accumulated answers used for cross-step
conditional questions — step 4's child-support radio and step 5's best-interest textarea
vanished for every user with children. Both fixed TDD-first; the tests now call through to
the real condition evaluator, closing the always-true-stub gap that let it ship.

**Honest gaps / deferred (tracked):**
- **L18 — RESOLVED 2026-07-11**: rate limiter converted to pure ASGI middleware
  (branch fix/asgi-rate-limiter, commit 481c0ae; 522 backend tests). Live re-check:
  curl-aborted client at 2s → LLM section loop stopped after **1 call (was 3)** —
  disconnects now propagate and abandoned runs stop burning tokens. Noted pre-existing:
  429s sit outside CORS (cross-origin browsers can't read Retry-After) and Redis mode
  is dead code — both unchanged.
- Possible third regression manifestation on *resume*: drafts store raw submit data, so
  `resumeAnswers` (useMotionInit merge) could re-poison conditions in a resumed session —
  flagged, not yet reproduced.
- Deferred from the plan: templating the party-ID block out of the LLM (durable L1 fix),
  backend structured-JSON gameplan (durable L10 fix), ex-parte route alias, 129s progress
  staging, Dashboard 'complete'/'completed' badge key, authority-strip husk sentences.
- Gameplan live run took the honest-fallback path — real personalized analysis quality
  remains unassessed (blocked on the structured-JSON gameplan work).

Verification artifacts: /tmp/real-llm-browser-test/artifacts/verify-* (screenshots,
verify-final.json, gated FL-300 PDF + text dumps). Re-run cost: ~7 upstream Claude calls.

## Out of scope (unchanged)
OCR and Gmail import remain untested — feature flags off pending Google OAuth
verification (launch blocker #1). Real-LLM evidence ranking / screenshot threading /
claim citations (M7/M8) not exercised this pass.

## Review
- Test users: maria.realllm3@ / respond.realllm@ / violation.realllm@ /
  gameplan.realllm@example.com in `browser-test.db` (disposable).
- Fix-order suggestion: L5 (flow dead) → L1–L4 fact-fidelity guardrail (launch gate:
  validate generated facts against intake data; strip citations; render markdown) → L6
  (wrong form) → L10 (gameplan content) → L9/L13/L14 (review-before-file gaps) → the
  rest with the existing tech-debt cleanup.
- Test harnesses: `/tmp/real-llm-browser-test/*.js` (flow2-test.js moved there from the
  repo root). Raw agent findings: `/tmp/real-llm-browser-test/artifacts/workflow-final.json`
  and `flow*-results.json`.
- Test backend stopped after the pass; `browser-test.db` left for inspection. Frontend
  dev server left running, restarted mid-pass with the correct
  `REACT_APP_API_URL=http://127.0.0.1:8000/api/v1` (see env note above).
