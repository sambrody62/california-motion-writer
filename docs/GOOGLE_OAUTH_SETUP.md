# Google OAuth Setup — Gmail Evidence (v1.1)

The Gmail evidence adapter requires the `gmail.readonly` scope, which Google
classifies as a **restricted scope**. The code ships flag-gated and OFF
(`GMAIL_EVIDENCE_ENABLED=false`). These steps — done in the GCP console, not in
code — are what gate turning it on for the public. Start early: verification
review takes weeks and runs in parallel with everything else.

Project: `california-motion-writer` (479935274378)

## What works WITHOUT Google review (do this to test now)

In "Testing" publishing mode, the OAuth flow works for up to **100 designated
test users** with no verification. This is enough to build, demo, and let beta
users exercise the full Gmail flow while review is pending.

1. APIs & Services → **Enable APIs** → enable **Gmail API**.
2. APIs & Services → **OAuth consent screen**:
   - User type: External
   - App name, support email, developer contact
   - App logo + app domain (needed later for verification, harmless now)
   - **Publishing status: Testing**
   - **Test users**: add your own email and any beta testers
3. APIs & Services → **Credentials → Create OAuth client ID**:
   - Type: Web application
   - Authorized redirect URI: `http://localhost:3000/evidence/gmail/callback`
     (dev) and your production callback URL
   - Copy the client ID and secret into the backend env:
     `GMAIL_OAUTH_CLIENT_ID`, `GMAIL_OAUTH_CLIENT_SECRET`,
     `GMAIL_OAUTH_REDIRECT_URI`
4. Set `GMAIL_EVIDENCE_ENABLED=true` (backend) and
   `REACT_APP_GMAIL_ENABLED=true` (frontend). The "Connect Gmail" button now
   renders and works for your test users.

## What's required to go PUBLIC (the weeks-long part)

5. Host the **Privacy Policy** at a stable public URL (the `/privacy` page ships
   with v1.1) and link it on the consent screen.
6. Add the `https://www.googleapis.com/auth/gmail.readonly` scope to the consent
   screen and complete the **scope justification** (we use it only to let users
   select emails as evidence; Limited Use compliant).
7. **Submit for verification.** Restricted scopes may also trigger a **CASA
   third-party security assessment** — budget time and possibly cost for it.
8. When approved, switch publishing status to **In production**. No code change
   is needed — the feature is already built; the GCP flag flip is the release.

## OCR (Cloud Vision) — separate, simpler

`OCR_ENABLED=false` by default. To enable transcription pre-fill on uploaded
screenshots:

1. Enable the **Cloud Vision API** in the project.
2. Ensure the Cloud Run service account has the Vision API user role
   (Application Default Credentials are used — no key file needed on GCP).
3. Set `OCR_ENABLED=true`. Uploaded images get a suggested transcription the
   user still reviews and confirms (required — exhibits are filed under penalty
   of perjury, so the human confirmation step never goes away).

## Honest scope note

There is **no iMessage / SMS integration** and there will not be — no platform
exposes message history via API. The supported path for texts is a screenshot
upload, which OCR pre-fills and the user confirms.
