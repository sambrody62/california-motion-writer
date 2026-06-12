# California Motion Writer — Complete PRD with User Stories

**Version:** 2.0 | **Status:** Ready for Full Implementation | **Last Updated:** 2026-06-10

---

## Table of Contents
1. [Vision & Goals](#vision--goals)
2. [User Personas](#user-personas)
3. [Core User Journeys](#core-user-journeys)
4. [Phased Roadmap](#phased-roadmap)
5. [Phase 1: MVP (Request for Order)](#phase-1-mvp-request-for-order)
6. [Phase 2: Response & Support Forms](#phase-2-response--support-forms)
7. [Phase 3: Evidence Synthesis](#phase-3-evidence-synthesis)
8. [Technical Architecture](#technical-architecture)
9. [Legal Compliance & UPL Risk](#legal-compliance--upl-risk)
10. [Data Privacy & Retention](#data-privacy--retention)
11. [Failure States](#failure-states)
12. [Open Decisions](#open-decisions)
13. [Success Metrics](#success-metrics)

---

## Vision & Goals

### Product Vision
Enable self-represented litigants in California to file professional, court-ready family law motions without hiring an attorney. By combining guided Q&A, LLM-powered legal writing, and intelligent form assembly, we reduce the barrier to legal access for users who cannot afford $3k-10k in attorney fees.

### Core Promise
**"Answer a few simple questions → Get a ready-to-file PDF you can walk into court with."**

### Business Goals
- Launch MVP in 4 weeks
- Reach 1,000 users by month 6
- Achieve 80% successful filing rate (users who download and actually file)
- Build network effects: responses to motions → disputes → repeat users

### Success Threshold for MVP
A logged-in user completes a Request for Order (RFO) motion from start to PDF download in under 20 minutes, with zero legal knowledge required.

---

## User Personas

### Primary: Maya, The Overwhelmed Parent
- **Age:** 34, single parent, works as a barista
- **Income:** $32k/year
- **Legal Situation:** Ex won't follow custody schedule; wants to modify order
- **Pain:** Cannot afford lawyer ($5k retainer), deadline pressure (custody issue with kids' school)
- **Tech Level:** Comfortable with mobile apps, not legal documents
- **Goals:** Get a court-approved motion within 2 weeks; file it herself; save $5k

### Secondary: James, The DIY Petitioner
- **Age:** 41, divorced, self-employed contractor
- **Income:** $65k/year (variable)
- **Legal Situation:** Wanting to modify child support down due to lost income
- **Pain:** Tried to write motion himself, court rejected it for formatting
- **Tech Level:** Comfortable with computers, used legal documents before
- **Goals:** Get the format right; understand what the judge needs; file confidently

### Tertiary: Linda, The Responder (Phase 2)
- **Age:** 38, employed full-time, defensive
- **Income:** $48k/year
- **Legal Situation:** Ex filed RFO; Linda needs to respond to defend her position
- **Pain:** Intimidated by court filings; worried about losing custody
- **Tech Level:** Mobile-first, uses apps daily
- **Goals:** Respond to RFO properly; protect her custody arrangement; not give ground unnecessarily

### Quaternary: Carlos, The Support-Only Filer
- **Age:** 45, warehouse supervisor, hours cut from full-time to part-time
- **Income:** Dropped from $58k to $38k/year
- **Legal Situation:** No custody dispute — co-parenting works fine — but he can no longer afford the current support order
- **Pain:** Every month he waits, he falls further behind; doesn't know support changes aren't retroactive
- **Tech Level:** Basic; uses phone for everything
- **Goals:** File a support modification quickly (FL-300 support sections + FL-150) without touching custody at all

---

## Core User Journeys

### Journey 1: "I Need to Modify Custody" (RFO Filer)
```
Landing page → Create account → Complete profile (5 fields)
  ↓
"What's your situation?" (free text)
  ↓
LLM identifies: RFO for custody modification
  ↓
Guided intake: 12 questions over 4 screens
  - Current custody arrangement?
  - What change are you requesting?
  - Why? (LLM converts to formal declaration)
  - Children's info (auto-filled from profile if available)
  - Any support issues?
  ↓
LLM rewrites narrative → formal declaration
  ↓
Review & edit
  ↓
Download PDF packet (FL-300 + MC-030 + FL-150 if needed)
  ↓
Filing checklist: county-specific instructions, fees, courthouse address
  ↓
"Come back to update us after you file!" (analytics hook)
```
**Time to PDF:** 12-18 minutes
**Forms:** FL-300, MC-030, FL-150 (conditional)
**Success metric:** User downloads PDF with >5KB file size

---

### Journey 2: "I Need to Respond to a Motion" (FL-320 Responder — Phase 2)
```
Landing page → "I need to respond to a motion filed against me"
  ↓
Upload/paste RFO or describe what was filed against you
  ↓
LLM identifies key relief requested
  ↓
"Do you agree with any of these requests?"
  ↓
Guided intake: counter-arguments, evidence, your requests
  ↓
LLM drafts response language
  ↓
Download FL-320 packet
  ↓
"Service deadline is 9 days from when you were served" (warning)
```
**Time to PDF:** 15-20 minutes
**Forms:** FL-320, MC-030
**Success metric:** Response filed within 9 day deadline

---

### Journey 3: "The Other Parent Violated the Order" (Violation/Contempt — Phase 2)
```
Landing page → "The other parent violated our court order"
  ↓
"What did they violate?" (e.g., won't follow visitation schedule, non-payment)
  ↓
"When did this happen?" (dates matter for statute of limitations)
  ↓
Evidence upload: text screenshots, emails, missed payments
  ↓
LLM builds declaration from evidence + user narrative
  ↓
San Diego courthouse routing: Emergency (24-48hr) vs Regular (3-6 wk) vs Contempt (4-8 wk)
  ↓
Download FL-410/411 packet + emergency guidance if applicable
```
**Time to PDF:** 10-15 minutes (if evidence pre-collected)
**Forms:** FL-410, FL-411, MC-030, D-046 (San Diego ex parte)
**Success metric:** Emergency motions downloadable same-day

---

### Journey 4: "Gmail Evidence Synthesis" (Phase 3)
```
User has completed an intake → Ready to download
  ↓
"Add evidence to strengthen your case?"
  ↓
"Connect your Gmail" (OAuth) → App scans for emails from other party
  ↓
App auto-extracts: threats, promises, payment records, custody-relevant emails
  ↓
User reviews & tags: "This proves he won't follow schedule"
  ↓
Evidence auto-assembled as Exhibit A, B, C in declaration
  ↓
PDF now includes evidence summary + quoted emails with dates
  ↓
"We found 47 emails supporting your position"
```
**Time to add:** 3-5 minutes
**Impact:** Transforms declaration from weak to compelling

---

### Journey 5: "I Need to Change Child Support Only" (Support Modification — Carlos)
```
Landing page → "I need to change child support"
  ↓
"Did your income change, or the other parent's?" (both paths valid)
  ↓
Guided intake: income details (FL-150 questions), why the change is warranted
  ↓
App explains: support changes are NOT retroactive — file ASAP (date of filing matters)
  ↓
LLM drafts declaration: income change narrative → formal language
  ↓
Download packet: FL-300 (support boxes only) + FL-150
  ↓
Filing checklist + reminder: serve other party, bring pay stubs to hearing
```
**Time to PDF:** 10-15 minutes
**Forms:** FL-300 (support sections only), FL-150
**Key logic:** Skip all custody/visitation questions when intent = support-only
**Success metric:** Support-only filers never see a custody question

---

### Journey 6: "I'm Afraid for My Safety" (Emergency / DVRO) — HIGH STAKES
```
Landing page → "I need emergency protection" (prominent, always visible)
  ↓
IMMEDIATE banner: "If you are in danger right now, call 911."
  ↓
Triage: domestic violence? → DV-100/DV-109/DV-110 path (DVRO)
        emergency custody (child at risk)? → FL-300 + FL-303 ex parte path
  ↓
Shortened intake (urgency-first): what happened, when, children at risk?
  ↓
LLM drafts declaration with specific incidents + dates (courts require specificity)
  ↓
Download packet + SAME-DAY filing instructions:
  - Ex parte papers must be filed by county cutoff time (e.g., 10am in San Diego)
  - Notice requirement to other party (or declaration why notice should be excused)
  - Free filing (no fee for DVRO)
  ↓
Resources panel: DV hotline, local shelters, courthouse self-help center
```
**Time to PDF:** Must be under 15 minutes — speed is the product here
**Forms:** DV-100, DV-109, DV-110, CLETS-001 (DVRO) or FL-300 + FL-303 (ex parte custody)
**Product requirements:**
- This flow must NEVER be paywalled or rate-limited
- LLM failure must fall back to blank-form download + instructions — never a dead end
- App generates forms and instructions only; it does NOT give safety-planning advice — link out to DV resources

---

### Journey 7: "I Have a Hearing Next Week" (Hearing Preparation — Phase 2+)
```
Dashboard shows motion with hearing_date approaching → "Prepare for your hearing"
  ↓
Chat-based prep using the motion's own intake data:
  - "Here are the 3 things you're asking the judge for" (recap)
  - What to bring: filed copies, proof of service, evidence exhibits, pay stubs
  - What to expect: check-in, when to speak, addressing the judge ("Your Honor")
  - Likely questions from the judge based on relief requested
  - What the other party will probably argue (from FL-320 if filed)
  ↓
Printable one-page hearing cheat sheet
  ↓
Post-hearing follow-up: "How did it go?" → if order granted, offer FL-340/FL-341
  (Findings and Order After Hearing) guidance
```
**Forms:** None generated (cheat-sheet PDF only)
**Surface:** Chat interface + dashboard reminder
**Dependency:** `deadline_reminder_service.py` already exists in the backend, currently unwired
**Success metric:** Users with hearings return to the app in the week before their hearing

---

### Journey 8: "I Don't Know What I Need" (Triage / Intent Classification)
```
Landing page → "Not sure where to start? Describe your situation"
  ↓
Free-text: "My ex isn't paying support and won't let me see the kids on my weekends"
  ↓
LLM intent classification (chat_service.py — already built) detects MULTIPLE issues:
  1. Support enforcement (possible contempt — FL-410)
  2. Custody order violation (RFO enforcement or contempt)
  ↓
App explains each option in plain language with tradeoffs:
  - "Contempt is serious but slow (4-8 weeks) and has a higher proof standard"
  - "An RFO to enforce/modify is faster and usually enough"
  ↓
User picks a path (or chats to clarify) → routed into the matching guided intake
  ↓
Profile + situation context carries over — no re-entry
```
**Forms:** None directly — this journey routes into Journeys 1, 3, 5, or 6
**Surface:** Chat interface (exists) + GameplanCreation component (exists)
**Key logic:** When multiple intents are detected, always present options — never silently pick one
**Success metric:** >80% of triaged users reach the correct intake without support help

---

## Phased Roadmap

| Phase | Timeline | Scope | Journeys | Users Enabled | Dependencies |
|---|---|---|---|---|---|
| **Phase 1: MVP** | Weeks 1-4 | RFO + intake + PDF; support-only path (skip custody questions) | 1, 5 | Maya (custody filers), Carlos (support-only) | Backend mostly done; fix 5 integration stubs |
| **Phase 2: Responses & Support** | Weeks 5-6 | FL-320, FL-335, FL-150 standalone, violations (SD), emergency/DVRO flow, triage routing | 2, 3, 6, 8 | James (responders), Linda, safety-at-risk users | Phase 1 complete |
| **Phase 2+: Hearing Prep** | Weeks 6-7 | Chat-based hearing preparation, cheat sheet, FL-340/341 guidance | 7 | All users with hearings | Wire existing `deadline_reminder_service.py` |
| **Phase 3: Evidence Synthesis** | Weeks 7-10 | Gmail OAuth, SMS import, evidence tagging, exhibit assembly | 4 | All users 2x more powerful | Phase 1 + 2 complete; Gmail API setup |
| **Phase 4: Multi-County Expansion** | Weeks 11-14 | Add LA, SF, Sacramento, Fresno forms & courthouse routing | all | National expansion path | Phase 1-3 working in San Diego |
| **Phase 5: Production Hardening** | Ongoing | PII masking, audit logging, compliance, rate limiting, staging | all | Enterprise-ready | All above |

---

## Phase 1: MVP (Request for Order)

### Goals
- **Primary success:** User → motion → downloadable PDF with real content in 20 minutes
- **Secondary:** Demonstrate pattern for future forms (Q&A → LLM → PDF is repeatable)
- **Data:** Collect 50+ completed motions to train Phase 2

### Features

#### F1.1: User Onboarding & Profile
**User Story:** As Maya, I want to create an account and save my party information so I don't re-enter it for every motion.

**Acceptance Criteria:**
- ✅ Register with email + password
- ✅ Create profile: party name, other party name, case number, county, is_petitioner flag
- ✅ Auto-fill party names in intake when profile exists
- ✅ Update profile without losing motion drafts

**Technical:**
- Backend: `/auth/register`, `/auth/login`, `/profiles` endpoints (already implemented)
- Frontend: LoginForm, RegisterForm, ProfileSetup components (exist)
- Fields: `party_name`, `other_party_name`, `case_number`, `county`, `is_petitioner`, `children_info` (JSON array)

**Effort:** 2 hours (mostly wiring existing code)

---

#### F1.2: RFO Intake Wizard
**User Story:** As Maya, I want to answer a series of simple questions about my custody situation, and the app should intelligently ask follow-up questions based on my answers.

**Acceptance Criteria:**
- ✅ Multi-step form: 4 screens, 12-15 questions total
- ✅ Conditional questions: "Do you have income?" → show income questions; "Is this about custody?" → show custody questions
- ✅ Progress bar showing which step we're on
- ✅ Ability to go back and edit previous answers
- ✅ All answers saved to motion drafts on the backend after each step

**Questions:**
1. **Screen 1: Situation**
   - "Describe what you want to change about the current custody arrangement" (textarea)
   - "Is this about custody, visitation, support, or combination?" (radio)
   
2. **Screen 2: Current Order**
   - "What is the current custody arrangement?" (radio: sole/joint/supervised)
   - "What is the current visitation schedule?" (free text)
   - "When was this order made?" (date picker)
   
3. **Screen 3: What You're Requesting**
   - "What custody arrangement are you requesting?" (radio/checkboxes)
   - "What visitation are you requesting?" (free text)
   - "Is there a support issue?" (yes/no)
   - [If yes] "Do you want to modify support?" (increase/decrease/establish)
   
4. **Screen 4: Children & Context**
   - Children info (auto-filled from profile if available): names, ages, schools
   - "Any other information the court should know?" (textarea)
   - "Any evidence you have?" (file upload placeholder for Phase 3)

**Technical:**
- Frontend: `GuidedIntake.tsx` (partially exists, needs completion)
- Backend: `/intake/rfo/steps` and `/intake/rfo/submit-step` (exist, tested)
- Data: `FORM_TEMPLATES` in `frontend/src/data/formTemplates.ts` has structure; verify RFO section matches backend
- Drafts: `POST /motions/{id}/drafts` saves each step

**Effort:** 4 hours (finishing existing code, wiring to backend)

---

#### F1.3: LLM-Powered Declaration Writing
**User Story:** As Maya, after I answer the questions, the app should rewrite my answers into formal, court-appropriate language so my declaration is professional.

**Acceptance Criteria:**
- ✅ After user completes intake, trigger `POST /llm/process-motion`
- ✅ Show loading state: "Drafting your declaration..."
- ✅ LLM rewrites narrative answers into FL-300 "relief requested" field + MC-030 declaration
- ✅ User sees before/after: raw answers vs. LLM output
- ✅ User can edit LLM output if needed
- ✅ Model: Gemini 1.5 Flash (cost-effective), 3000-4000 token limit

**Backend prompt template:**
```
You are a California family law document assistant. 
Convert these intake answers into a court-ready declaration.

Current intake data:
[answers]

Generate:
1. FL-300 "Relief Requested" section (1-2 paragraphs)
2. MC-030 Declaration text (2-3 paragraphs, formal, specific)

Use legal language. Reference Family Code sections where relevant.
Do not mention attorney fees unless explicitly requested.
```

**Technical:**
- Frontend: `GuidedIntake.tsx` → trigger LLM on completion
- Backend: `/llm/process-motion` (exists, verify it works)
- Error handling: If LLM times out, show error and allow user to proceed without LLM

**Effort:** 3 hours (wire trigger, add loading state, test LLM output quality)

---

#### F1.4: PDF Generation & Download
**User Story:** As Maya, I want to download a PDF that's ready to take to the courthouse and file.

**Acceptance Criteria:**
- ✅ Generate PDF packet: FL-300 (main form) + MC-030 (declaration) + FL-150 (if support issue)
- ✅ PDF is filled with user's data: party names, case number, county, relief requested, declaration text
- ✅ File size > 50KB (actual content, not empty)
- ✅ Opens correctly in Adobe Reader / web browser
- ✅ All required fields filled; signature line blank (user signs in person)
- ✅ Page numbers + filing header present

**Technical:**
- Frontend: `MotionPreview.tsx` → `documentAPI.generatePDFSync()` button
- Backend: `POST /documents/generate-pdf-sync` → calls `pdf_service.generate_motion_pdf()`
- Forms: Requires blank CA court form PDFs in `forms/` directory:
  - `forms/FL-300.pdf`
  - `forms/MC-030.pdf`
  - `forms/FL-150.pdf`
- PDF Library: ReportLab + PyPDF2 (already in requirements)

**Field Mapping (FL-300):**
- Petitioner name → line 1
- Respondent name → line 2
- Case number → line 3
- County → line 4
- Relief requested checkboxes → based on motion type
- Declaration attachment indicator → check "Exhibit A" box

**Effort:** 6 hours (verify form PDFs exist, test field mapping, ensure sync generation works)

---

#### F1.5: Filing Checklist & Next Steps
**User Story:** As Maya, after I download my motion, I want clear instructions on how to actually file it.

**Acceptance Criteria:**
- ✅ Post-download page shows:
  - County-specific filing fee ($30-$300 depending on relief type)
  - How many copies to print (original + 2)
  - Courthouse address and hours
  - Required proof of service deadline (21 days before hearing)
  - "What to say at the clerk's window" script
- ✅ Link to CA court self-help center
- ✅ Email receipt of motion PDF to user

**Technical:**
- Frontend: FilingChecklist component, post-PDF page
- Data: County → courthouse address + fee lookup table (50 CA counties)
- Email: Trigger Sendgrid/AWS SES on PDF generation

**Effort:** 3 hours (build checklist component, county lookup table)

---

### Phase 1 User Stories Summary

| ID | Title | Effort | Priority |
|---|---|---|---|
| F1.1 | Onboarding & Profile | 2h | P0 |
| F1.2 | RFO Intake Wizard | 4h | P0 |
| F1.3 | LLM Declaration | 3h | P0 |
| F1.4 | PDF Generation | 6h | P0 |
| F1.5 | Filing Checklist | 3h | P1 |
| T1.1 | Smoke test (e2e) | 3h | P0 |
| T1.2 | Unit tests (backend) | 2h | P0 |
| T1.3 | Fix service test mocks | 2h | P0 |

**Phase 1 Total Effort:** ~25 hours (3-4 days with 1 eng)

---

## Phase 2: Response & Support Forms

### Goals
- Enable responders (Linda) to fight back against motions filed against them
- Unlock support-only filings (James needs to modify child support independently)
- Prove violations workflow (contempt motions for when orders are violated)

### Features

#### F2.1: FL-320 (Response to RFO)
**User Story:** As Linda, I received a motion from my ex requesting custody changes. I want to respond to defend my position without hiring a lawyer.

**Acceptance Criteria:**
- ✅ User uploads or pastes the RFO they received
- ✅ App identifies relief requested in the RFO (e.g., "requesting sole custody")
- ✅ Intake wizard asks: "Do you agree with this? Why or why not?"
- ✅ User provides counter-arguments
- ✅ LLM rewrites into formal response
- ✅ Generate FL-320 PDF
- ✅ Warning: "You have 9 days from being served. Current date is [X]. Filing deadline is [Y]."

**Technical:**
- Backend: `IntakeService` needs `/intake/fl-320/steps` endpoint (copy of RFO logic, FL-320-specific questions)
- Frontend: Routing to `/motion/new/RESPONSE` or start flow
- Questions differ from RFO:
  - "Do you agree with the current custody arrangement?" (yes/no)
  - "What do you disagree with?" (if no)
  - "What would you request instead?" (free text)
  - "Do you have evidence to support your position?" (file upload)

**Effort:** 5 hours

---

#### F2.2: FL-150 (Income & Expense Declaration) Standalone
**User Story:** As James, my income has decreased and I want to modify child support. I need to file a standalone FL-150 showing my new income, not a full RFO.

**Acceptance Criteria:**
- ✅ Dedicated FL-150 intake (shorter than RFO)
- ✅ Income questions: gross income, deductions, expenses, asset breakdown
- ✅ Questions conditional on income type (W-2 vs. self-employed vs. fixed income)
- ✅ Generate FL-150 PDF with all fields filled
- ✅ Optional: include declarative statement ("My income has decreased due to...")

**Technical:**
- Backend: `/intake/fl-150/steps`
- Frontend: Separate intake flow for FL-150
- Questions map to FL-150 fields exactly
- Integration: FL-150 auto-included in RFO if "support issue" is Yes

**Effort:** 4 hours

---

#### F2.3: FL-335 (Proof of Service)
**User Story:** As Maya, after I file my RFO, I need to prove I served the other party. The app should guide me through proof of service.

**Acceptance Criteria:**
- ✅ Simple intake: "How did you serve the other party?" (personal service, mail, publication)
- ✅ Date of service
- ✅ Name and address of person served
- ✅ Generate FL-335 PDF
- ✅ Integrate into post-filing workflow

**Technical:**
- Backend: `/intake/fl-335/steps`
- Frontend: Optional step after "Download PDF" in Phase 1
- Form: FL-335 is mostly pre-filled, user signs, dates

**Effort:** 2 hours

---

#### F2.4: Violations/Contempt Workflow (FL-410, FL-411, D-046)
**User Story:** As Maya, the other parent violated our custody order. I want to file a contempt motion and get emergency relief.

**Acceptance Criteria:**
- ✅ "The other parent violated the court order" intake flow
- ✅ Questions: What order was violated? When? Evidence?
- ✅ App determines track: Emergency (24-48hr), Regular (3-6 wk), or Contempt (4-8 wk)
- ✅ Generate appropriate form packet (FL-410 + D-046 if emergency)
- ✅ Courthouse routing: which San Diego courthouse + division
- ✅ LLM enhancement: convert evidence list into formal declaration of violation

**Technical:**
- Backend: `violation_service.py` exists; wire to frontend `/intake/violations/start`
- Frontend: Violations routing + intake
- Backend logic: Determine track based on `motion.intake_data.violation_type` and urgency
- Evidence handling: User provides text, emails, screenshots; LLM assembles into formal declaration

**Effort:** 6 hours

---

#### F2.5: Evidence Upload & Tagging (Phase 3 prep)
**User Story:** As a user building a motion, I want to upload evidence (photos, emails, text screenshots) and tag them so they get referenced in my declaration.

**Acceptance Criteria:**
- ✅ File upload widget in intake (optional for all forms)
- ✅ User tags evidence: "custody violation", "non-payment", "threat", "promise to follow schedule"
- ✅ Tags visible in motion preview
- ✅ Evidence not yet assembled into PDF (Phase 3), but stored for later

**Technical:**
- Frontend: File upload component + tag UI
- Backend: `/motions/{id}/evidence` endpoint to store files
- Storage: GCS bucket `gs://california-motion-writer-uploads/`
- Model: Add `Evidence` model linking to Motion

**Effort:** 4 hours

---

### Phase 2 User Stories Summary

| ID | Title | Effort | Priority |
|---|---|---|---|
| F2.1 | FL-320 Response | 5h | P0 |
| F2.2 | FL-150 Standalone | 4h | P0 |
| F2.3 | FL-335 Proof of Service | 2h | P1 |
| F2.4 | Violations/Contempt | 6h | P0 |
| F2.5 | Evidence Upload | 4h | P1 |
| T2.1 | Intake test coverage | 3h | P0 |

**Phase 2 Total Effort:** ~28 hours (3-4 days with 1 eng)

---

## Phase 3: Evidence Synthesis

### Goals
- Turn scattered emails/texts into compelling exhibits
- Reduce time users spend searching for evidence
- Make declarations orders-of-magnitude more persuasive

### Features

#### F3.1: Gmail OAuth Integration
**User Story:** As Maya, I want to connect my Gmail so the app can pull relevant emails from my ex to include as evidence in my motion.

**Acceptance Criteria:**
- ✅ OAuth flow: "Connect Gmail to pull evidence" button
- ✅ App scans emails FROM other party (by name/email)
- ✅ Filters: custody-relevant, threatening, non-payment evidence
- ✅ Shows user: "Found 47 emails. Do you want to include any?"
- ✅ User selects emails; app extracts date, sender, key quotes
- ✅ Selected emails become "Exhibit A, B, C..." in final PDF
- ✅ User can manually add/remove emails

**Technical:**
- Backend: New `GmailService` using `google.auth.oauthlib`
- Endpoint: `POST /evidence/gmail/auth` → OAuth flow
- Endpoint: `GET /evidence/gmail/scan` → returns filtered emails
- Endpoint: `POST /evidence/gmail/select` → user-selected emails for motion
- Storage: Cache emails in `Evidence` model (don't store full email body; store ID, date, sender, subject, extracted_quotes)
- Privacy: Users grant read-only access; no data leaves user's Google account except what they explicitly select
- Rate limit: 1 Gmail scan per motion (API quota)

**Error handling:**
- Gmail connection fails → fallback to manual upload
- No relevant emails found → "No emails found. Try manual upload."

**Effort:** 8 hours (OAuth flow, Gmail API integration, parsing)

---

#### F3.2: SMS/Text Evidence Import
**User Story:** As James, I have threatening texts from my ex on my phone. I want to upload screenshots of them and have the app include them as exhibits.

**Acceptance Criteria:**
- ✅ Upload text message screenshots (PNG/JPG)
- ✅ App auto-extracts via OCR: date, sender, message text
- ✅ User confirms extracted text (OCR corrections)
- ✅ Becomes "Exhibit A" in declaration
- ✅ Alternative: manual paste of text (user types transcription)

**Technical:**
- Backend: New `TextEvidenceService`
- Endpoint: `POST /evidence/text/upload` → file + manual transcription
- OCR: Google Cloud Vision API (already available in GCP project)
- Storage: `Evidence` model with `source: "text_ocr"` + `extracted_text`

**Effort:** 4 hours (OCR integration, manual fallback)

---

#### F3.3: Evidence Assembly & Exhibit Generation
**User Story:** As Maya, I've selected emails and texts as evidence. When I download my motion PDF, I want all evidence attached as numbered exhibits with proper formatting.

**Acceptance Criteria:**
- ✅ After LLM generates declaration, auto-insert exhibit references: "See Exhibit A (email dated 3/15/25)"
- ✅ Exhibit packet: cover page listing all exhibits with dates
- ✅ Each exhibit: date, sender, message/email body, page number
- ✅ PDF includes exhibits as separate pages at end (Exhibit A, B, C, ...)
- ✅ Numbering auto-adjusts if user adds/removes exhibits

**Technical:**
- Backend: New `ExhibitAssemblyService`
- Workflow:
  1. LLM generates declaration with placeholder references: `[EXHIBIT: custody_emails]`
  2. `ExhibitAssemblyService.insert_exhibit_references()` converts placeholders to "See Exhibit A"
  3. `pdf_service.generate_motion_pdf()` appends exhibit pages
- PDF assembly: ReportLab to generate exhibit cover page + exhibit pages

**Effort:** 6 hours

---

#### F3.4: Evidence Tagging & Summation
**User Story:** As Linda, when I tag emails as "custody violation" or "non-payment", the app should automatically reference them in my declaration.

**Acceptance Criteria:**
- ✅ Evidence tags: threat, non-payment, custody_violation, promise_to_follow, false_claim
- ✅ LLM prompt includes evidence summary: "User has 3 emails proving non-payment on [dates]"
- ✅ LLM declaration naturally references evidence: "As evidenced by emails dated March 15 and April 2, [other party] failed to make payments"
- ✅ User can override/edit LLM reference if needed

**Technical:**
- Frontend: Evidence tag UI (checkboxes for each tag)
- Backend: LLM prompt enhancement
  ```
  Evidence Summary:
  - Non-payment: 3 emails (2/15, 3/2, 3/20)
  - Custody violation: 5 text messages (1/10-1/12)
  - Threats: 2 emails (2/3, 2/5)
  
  Incorporate this evidence naturally into the declaration.
  ```
- Testing: Verify LLM output naturally cites evidence

**Effort:** 3 hours

---

### Phase 3 User Stories Summary

| ID | Title | Effort | Priority |
|---|---|---|---|
| F3.1 | Gmail OAuth | 8h | P0 |
| F3.2 | SMS/Text Import | 4h | P1 |
| F3.3 | Exhibit Assembly | 6h | P0 |
| F3.4 | Evidence Tagging | 3h | P1 |
| T3.1 | End-to-end evidence test | 4h | P0 |

**Phase 3 Total Effort:** ~28 hours (3-4 days)

---

## Technical Architecture

### Backend Stack
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL (Cloud SQL in prod, SQLite for local dev)
- **ORM:** SQLAlchemy + Alembic migrations
- **LLM:** Vertex AI Gemini 1.5 Flash (cost-controlled, mock fallback)
- **PDF:** ReportLab + PyPDF2
- **Cloud Storage:** Google Cloud Storage (GCS) for form templates + uploads
- **OCR:** Google Cloud Vision API
- **Gmail API:** `google-auth-oauthlib` for OAuth
- **Auth:** JWT (24-hour tokens), bcrypt password hashing
- **Rate Limiting:** slowapi (50 req/hr for chat, 5 motion gens/hr)
- **Monitoring:** Cloud Logging + Cloud Error Reporting

### Frontend Stack
- **Framework:** React 18 + TypeScript
- **State:** Context API (no Redux needed at this scale)
- **Styling:** Tailwind CSS
- **Forms:** React Hook Form + Zod validation
- **HTTP:** Axios + axios-mock-adapter for testing
- **Auth:** Firebase Auth (OAuth) with local fallback for dev
- **PDF download:** Native browser blob download

### Data Models

**User**
```python
- id (PK)
- email (unique)
- password_hash
- full_name
- phone
- is_active
- email_verified
- created_at, updated_at, last_login
```

**Profile**
```python
- id (PK)
- user_id (FK)
- party_name
- other_party_name
- case_number
- county
- court_branch
- is_petitioner
- party_address, party_phone
- other_party_address, other_party_attorney
- children_info (JSON: [{name, age, school}, ...])
- city, zip_code, state
```

**Motion**
```python
- id (PK)
- user_id (FK)
- profile_id (FK)
- motion_type (ENUM: RFO, RESPONSE, FL_150, FL_335, VIOLATION, etc.)
- status (ENUM: draft, submitted, completed)
- case_caption
- title
- intake_data (JSON: user answers + conditional data)
- generated_text (LLM output)
- filing_date, hearing_date
```

**MotionDraft**
```python
- id (PK)
- motion_id (FK)
- step_number
- step_name
- question_data (JSON: user answers for this step)
- llm_input, llm_output
- is_complete
```

**Evidence** (Phase 3)
```python
- id (PK)
- motion_id (FK)
- source (ENUM: gmail, text_ocr, manual_upload)
- evidence_type (ENUM: email, text, document, photo)
- tags (JSON: [threat, non-payment, custody_violation, ...])
- original_data (JSON: extracted email/text)
- gcs_url (if file-based)
- date_provided
- user_confirmed (bool: user reviewed OCR/extraction)
```

**ChatSession**
```python
- id (PK)
- user_id (FK)
- status (ENUM: ACTIVE, COMPLETED, ABANDONED)
- state (ENUM: GREETING, INTENT_GATHERING, ..., PDF_GENERATION)
- motion_id (FK, optional: if chat leads to motion)
- context (JSON: conversation memory)
- created_at, updated_at
```

### API Endpoints

**Authentication**
- `POST /auth/register` — create account
- `POST /auth/token` — login (returns JWT)
- `GET /auth/me` — current user

**Profile**
- `POST /profiles` — create/update profile
- `GET /profiles/me` — get profile

**Motions**
- `POST /motions` — create motion
- `GET /motions` — list user's motions
- `GET /motions/{id}` — get motion + drafts
- `POST /motions/{id}/drafts` — save draft step
- `POST /motions/{id}/complete` — mark complete

**Intake**
- `GET /intake/{motion_type}/steps` — step definitions
- `POST /intake/{motion_type}/start` — initialize intake
- `POST /intake/{motion_type}/step/{step_number}` — get step with conditions
- `POST /intake/{motion_type}/submit-step` — submit answers, get next step

**LLM**
- `POST /llm/process-motion` — rewrite all drafts through LLM
- `POST /llm/rewrite` — rewrite single section

**Documents**
- `POST /documents/generate-pdf-sync` — generate PDF synchronously
- `GET /documents/{id}/download` — download generated PDF
- `GET /motions/{id}/documents` — list motion documents

**Evidence** (Phase 3)
- `POST /evidence/gmail/auth` — OAuth callback
- `GET /evidence/gmail/scan` — scan Gmail for relevant emails
- `POST /evidence/gmail/select` — select emails to include
- `POST /evidence/text/upload` — upload text screenshot
- `GET /motions/{id}/evidence` — list evidence for motion

---

## Legal Compliance & UPL Risk

### The Risk
California Business & Professions Code §6125 prohibits the unauthorized practice of law (UPL). A software product that *prepares legal documents* is permitted (see CA legal document assistant statutes, B&P §6400 et seq.); a product that *advises a specific user what they should do* is not. This is an existential risk, not a feature decision — every flow must be designed with this line in mind.

### The Line We Must Not Cross
| Allowed (legal information / document preparation) | NOT allowed (legal advice) |
|---|---|
| "An RFO is typically faster than contempt; contempt has a higher proof standard." | "You should file an RFO instead of contempt." |
| "Here are the forms used for each option." | "In your case, the judge will likely grant this." |
| Reformatting the user's own words into formal language | Adding legal arguments or facts the user didn't provide |
| Presenting all applicable options with neutral descriptions | Recommending one option for this user's situation |

### Product Requirements
- **C1. Disclaimer at signup:** Required checkbox: "I understand this service provides document preparation and legal information, not legal advice, and is not a substitute for an attorney."
- **C2. Persistent disclaimer:** Footer on every page and on every generated PDF cover sheet: "Prepared without attorney review. [Product] is not a law firm."
- **C3. LLM guardrails:** System prompt must instruct the model to (a) never recommend a course of action, (b) only rephrase user-provided facts — never invent facts, dates, or allegations, (c) decline questions like "will I win?" and redirect to the court self-help center.
- **C4. Journey 8 wording:** Triage presents options with neutral descriptions and ALWAYS requires the user to choose. Never auto-route based on a recommendation.
- **C5. Self-help referrals:** Every flow links to the user's county court self-help center and lawreferral resources (CA State Bar Lawyer Referral Service, local legal aid).
- **C6. Legal review before launch:** Terms of Service, Privacy Policy, and disclaimer language reviewed by a California attorney before public launch. Budget for this.

### LLM Output Constraint (technical enforcement)
Post-generation validation in `llm_service.validate_output()` must check for advice-like phrases ("you should", "I recommend", "your best option") and regenerate or flag for the user to confirm wording is their own.

---

## Data Privacy & Retention

The app stores declarations about abuse, finances, children, and addresses — among the most sensitive data a consumer product can hold. Mishandling it is a trust dealbreaker and a legal liability.

### Commitments (user-facing, in Privacy Policy)
- **P1. No training on user content.** Motion text, intake answers, chat transcripts, and evidence are never used to train models. Vertex AI calls must use the no-data-retention configuration.
- **P2. User deletion rights.** "Delete my account" removes all motions, drafts, chat history, and evidence within 30 days, including GCS objects and backups on their rotation schedule.
- **P3. Retention period.** Active accounts: data retained while account is active. Inactive accounts: data deleted after 24 months of inactivity, with a 30-day email warning.
- **P4. Encryption.** TLS in transit (already in place); encryption at rest via Cloud SQL/GCS defaults; evidence files in a non-public GCS bucket with signed URLs only.

### Third-Party Demand Handling
- **P5. Subpoena policy:** The other party in a dispute may subpoena user data. Policy: require a valid court order, notify the affected user before responding unless legally barred, and produce the minimum required. Document this in the Privacy Policy so users are not surprised.
- **P6. No sale or sharing of data.** Ever. CCPA "Do Not Sell" compliance is trivial if we never do it.

### Internal Handling
- **P7. PII masking in logs** (already in Phase 5 roadmap): names, case numbers, addresses, and children's info must never appear in Cloud Logging. Log motion IDs, not content.
- **P8. Access control:** No admin tooling that displays user motion content without an audited reason. Audit log for any internal access.
- **P9. DV-specific care:** For Journey 6 users, session data is high-risk if an abuser shares the device. Provide a "quick exit" button and offer to not send email receipts for DVRO flows.

---

## Failure States

Journey 6 already specifies its fallback rules. These apply to all other flows:

| Failure | User Experience | Technical Behavior |
|---|---|---|
| LLM timeout / error | "We couldn't polish your wording right now. You can retry, or continue with your own words — they are legally valid." | Retry up to 2x with backoff; then proceed with raw intake text into the PDF. Never block PDF generation on LLM. |
| LLM budget cap reached | Same as above — user's own words flow into the PDF | `cost_monitoring_service` flips to mock mode (already built); frontend treats mock output same as failure fallback |
| PDF generation fails | "Something went wrong building your PDF. Your answers are saved." + retry button | Drafts are already persisted server-side; log error with motion ID; alert on >1% failure rate |
| Session expires mid-intake | On re-login, dashboard shows the motion as "In progress — resume" | Drafts saved after every step (F1.2), so max loss is the current screen |
| Form template missing on server | Generic error + support contact | Startup health check verifies all PDFs in `forms/` exist; deploy fails if missing |
| Gmail OAuth denied / fails (Phase 3) | "No problem — you can upload evidence manually." | Manual upload is always available; Gmail is additive, never required |
| Court rejects the user's filing | Out of app scope, but FAQ covers the top rejection reasons (missing proof of service, wrong county, unsigned forms) | Filing checklist (F1.5) is the prevention mechanism |

Design rule: **the user's own words are always good enough to file.** Every AI feature is an enhancement layer with a non-AI fallback.

---

## Open Decisions

Tracked here so they don't get lost; each needs an owner and a deadline.

| # | Decision | Status | Notes |
|---|---|---|---|
| OD1 | Spanish language support | Deferred to Phase 4 — revisit | ~1/3 of CA pro per litigants are primarily Spanish-speaking; Judicial Council publishes official Spanish forms. May matter more than county expansion. |
| OD2 | Monetization | Decision pending — free during beta | Decide by month 3. Constraint already set: Journey 6 (emergency/DVRO) is never paywalled. |
| OD3 | Analytics & instrumentation plan | Not started | Success metrics in this PRD need event tracking (funnel: signup → intake start → intake complete → PDF download). Pick tool (PostHog / GA4) in Phase 1. |
| OD4 | User support model | Not started | What happens when a user emails "the court rejected my motion"? Minimum: support inbox + FAQ. Decide before public launch. |
| OD5 | Phase 4/5 user stories | Not written | Roadmap rows exist; write stories when Phase 3 is underway. |
| OD6 | Attorney review of ToS/disclaimers (C6) | Not started | Required before public launch. |

---

## Success Metrics

### Phase 1 MVP Success
- ✅ 50+ users register
- ✅ 30+ RFO motions generated
- ✅ 80% of downloads are >50KB (actual content)
- ✅ 0 critical bugs reported in first 100 users
- ✅ Average time from start to PDF: <20 minutes

### Phase 2 Success
- ✅ 100+ total users
- ✅ 20+ responses filed (Linda persona activated)
- ✅ 10+ violation motions (enforcement use case)
- ✅ Support inquiry rate <5% (app is self-explanatory)

### Phase 3 Success
- ✅ 50% of users opt-in to Gmail evidence
- ✅ Motions with evidence have 40% higher "helpful" rating
- ✅ Declaration quality score (LLM + human judges): 8/10 average

### Long-term (6 months)
- ✅ 1,000+ users
- ✅ 500+ motions filed
- ✅ 70% filing success rate (users report motion was accepted by court)
- ✅ $0 customer acquisition cost (word-of-mouth, legal aid referrals)
- ✅ NPS >50 (users recommend to others)

---

## Implementation Notes

### Critical Blockers to Remove (Week 1)
1. Verify blank court form PDFs (FL-300, MC-030, FL-150) exist in Docker image
2. Test `pdf_service.generate_motion_pdf()` produces real output (>50KB)
3. Fix 5 API stub methods in frontend `api.ts`
4. Fix backend bugs (missing LLMService methods, Profile fields, WebSocket auth)
5. Establish County → Courthouse lookup table for all 58 CA counties

### Deployment Pipeline
1. **Dev:** Local Docker (FastAPI + SQLite)
2. **Staging:** Cloud Run (same config as prod, different DB)
3. **Prod:** Cloud Run + Cloud SQL (us-central1)
4. **CI/CD:** GitHub Actions (test on push, auto-deploy on merge to main)

### Testing Strategy
- **Unit:** Backend endpoints, LLM prompt building, PDF field mapping
- **Integration:** E2E intake flow (register → profile → complete intake → PDF)
- **Manual:** Download PDF, open in Adobe Reader, verify fields are filled
- **User:** A/B test LLM prompts on real users (Phase 3 data)

### Risk Mitigation
- **LLM quality:** Mock mode fallback if Vertex AI fails; pre-written templates for common scenarios
- **PDF generation:** Test with real CA court forms; have backup manual assembly process
- **Data privacy:** PII masking in logs; never log full names/case numbers; encrypt at rest
- **Rate limits:** Enforce per-user quotas; monitor spend; auto-reject if monthly budget exceeded

---

## Success Criteria for Launch

- [ ] Phase 1 features complete and tested
- [ ] 50+ beta users generated RFO motions
- [ ] At least 5 users reported successfully filing their motion
- [ ] No critical security vulnerabilities (OWASP top 10)
- [ ] PDF quality acceptable to users (80%+ "motion looks professional")
- [ ] Response time <5s for typical operations
- [ ] Mobile-friendly (iOS + Android browsers)
- [ ] Accessibility: WCAG 2.1 AA compliance

---

## Appendix: Intake Question Banks

### RFO Questions (Phase 1)
```
Screen 1: Situation
Q1: "Describe what you want to change about your custody arrangement" [textarea]
Q2: "Is this about custody, visitation, support, or a combination?" [radio]

Screen 2: Current Order
Q3: "What is the current custody arrangement?" [radio: sole/joint/supervised]
Q4: "What is the current visitation schedule?" [textarea]
Q5: "When was this order made?" [date picker]

Screen 3: Your Request
Q6: "What custody are you requesting?" [checkboxes: sole/joint/50-50/supervised]
Q7: "What visitation schedule do you want?" [textarea]
Q8: "Is there a support issue?" [yes/no]
Q8a: [IF yes] "Do you want to modify support?" [increase/decrease/establish]

Screen 4: Context
Q9: "Children's full names, ages, schools" [repeatable]
Q10: "Any other information the court should know?" [textarea]
Q11: "Do you have evidence to support your request?" [file upload]
Q12: "What is your preferred hearing date (if any)?" [date picker, optional]
```

### FL-320 Response Questions (Phase 2)
```
Screen 1: The Other Party's Request
Q1: "Copy/paste or describe what the other party is requesting" [textarea]

Screen 2: Your Position
Q2: "Do you agree with the request?" [yes/no]
Q2a: [IF no] "What specifically do you disagree with?" [textarea]
Q3: "What would you request instead (if anything)?" [textarea]

Screen 3: Evidence
Q4: "Do you have evidence to support your position?" [file upload, optional]
Q5: "Any other information?" [textarea]
```

### FL-150 Questions (Phase 2)
```
Screen 1: Income
Q1: "What is your primary income source?" [radio: W-2 employment, self-employed, fixed income, other]
Q1a: [IF W-2] "Gross monthly income?" [number]
Q1b: [IF self-employed] "Last year's net income?" [number]
Q2: "Do you have other income sources?" [yes/no]
Q2a: [IF yes] "List them" [textarea]

Screen 2: Expenses
Q3: "Average monthly living expenses (housing, food, utilities)?" [number]
Q4: "Do you support other children?" [yes/no]
Q4a: [IF yes] "How many? Total support amount?" [numbers]

Screen 3: Assets
Q5: "Do you own a home, car, or other assets?" [yes/no]
Q5a: [IF yes] "Describe (values estimated OK)" [textarea]
```

---

## Document History

| Version | Date | Author | Changes |
|---|---|---|---|
| 1.0 | 2026-05-15 | Initial | MVP PRD |
| 2.0 | 2026-06-10 | Phase 2-3 expansion | Added responses, violations, evidence synthesis |
| 2.1 | 2026-06-12 | Compliance & gaps | Added journeys 5-8, Carlos persona, UPL compliance, data privacy/retention, failure states, open decisions |

---

**For questions or updates, contact: sam@californiamotion.writer**
