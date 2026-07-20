# County Rules Dataset

This document describes where county-specific court rules live in this
codebase, what they cover, and the workflow for adding or verifying a county.

## Why local rules matter

The Judicial Council forms this app generates (FL-300, FL-320, MC-030, FL-150,
FL-335, FW-001) are **statewide** — identical in all 58 California counties.
What varies by county is everything around them, governed by each Superior
Court's **local rules**:

- Which courthouse / division handles family law for a given case
- Mandatory **local forms** and cover sheets (e.g. San Diego's D-046 ex parte
  application, which exists only in San Diego)
- E-filing mandates vs. paper filing
- Hearing date reservation procedures and department assignment
- Filing fees and copy requirements

A motion packet that is perfectly formatted statewide can still be rejected at
the filing window for missing a local requirement. That is why the rollout
posture is: **statewide forms work everywhere; county-specific guidance is
only shown where we have data, and unverified data is always flagged.**

## Where the data lives

| Location | Contents | Consumed by |
|---|---|---|
| `frontend/src/data/countyFilingInfo.ts` | **Canonical county dataset**: courthouses, fees, copies, service deadlines, court website, local-rules pointers, e-filing notes, verification status | `FilingChecklist.tsx` (motion preview page) |
| `forms/san-diego-violation/form-config.json` | San Diego violation/enforcement filing config: courthouse divisions, filing tracks (emergency / regular / contempt), required forms per track | `app/services/violation_service.py` (backend) |

Counties **not** in the dataset get a generic checklist in the UI with a link
to the statewide self-help center (`https://selfhelp.courts.ca.gov`) — never
fabricated specifics. The backend fact gate
(`app/services/fact_gate/authority_strip.py`) independently strips any local
rules or courthouse details the LLM invents, so unsupported counties cannot
receive hallucinated local guidance in generated documents.

## Schema (per county)

See the `CountyFilingInfo` interface in
`frontend/src/data/countyFilingInfo.ts`. Key fields:

- `courthouse` / `additionalCourthouses` — family law locations. Large
  counties have several; list them all so users confirm the right one.
- `filingFee`, `feeWaiverForm`, `copiesRequired`, `serviceDeadline` —
  filing-window mechanics. Always paired with a verify-with-court disclaimer.
- `courtWebsite` — official Superior Court site (root URL only; deep links to
  rules pages break when courts reorganize their sites — omit rather than
  guess).
- `localRules.note` / `localRules.url` — where users find the county's local
  rules. Only set `url` if it has been checked and is stable.
- `eFiling.note` — whether to check for e-filing requirements. Do not assert
  "required" or "not available" without verification.
- `verification.verified` / `verification.lastReviewed` — see below.

## Verification workflow

**Never present unverified data as authoritative.** Legal filing details
change (fees especially), and a wrong specific is worse than a generic
disclaimer.

1. New entries start with `verification: { verified: false }`. The UI
   automatically shows a "not verified — confirm with the court" notice for
   these.
2. To verify a county: check the court's current local rules and fee schedule
   on its official website, confirm courthouse addresses and family law
   division assignments, then set `verified: true` and `lastReviewed` to the
   review date.
3. Re-review verified counties periodically (fees typically change at the
   start of the fiscal year, July 1) and whenever a court reorganizes.

## Adding a new county

1. Add an entry to `countyFilingDatabase` in
   `frontend/src/data/countyFilingInfo.ts` following the schema above. Start
   with `verified: false`.
2. Add rendering tests in
   `frontend/src/components/__tests__/FilingChecklist.test.tsx`.
3. If the county needs a violation/enforcement flow (like San Diego's), that
   requires a per-county form config and local form PDFs — model it on
   `forms/san-diego-violation/`. Note that local ex parte forms differ by
   county; the San Diego flow must not be reused as-is elsewhere.

## Current status

| County | In dataset | Verified | Violation flow |
|---|---|---|---|
| San Diego | ✅ | ❌ | ✅ (only county) |
| Los Angeles | ✅ | ❌ | ❌ |
| Orange | ✅ | ❌ | ❌ |
| Riverside | ✅ | ❌ | ❌ |
| Sacramento | ✅ | ❌ | ❌ |
| Other 53 counties | ❌ (generic checklist) | — | ❌ |
