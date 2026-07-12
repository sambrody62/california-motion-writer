# Trust Design Spec — Family Court Helper

**Status:** Approved research → spec. No code changes yet; implementation is a follow-up task.
**Evidence base:** [trust-design-research.md](trust-design-research.md). All contrast ratios below were computed (WCAG relative-luminance formula), not eyeballed.

## Principles (each traceable to research)

1. **Calm civic blue, medium saturation** — blue is the most trust-associated hue; high saturation raises arousal and can lower trust. Current indigo-600 `#4f46e5` is violet-leaning and highly saturated with no civic precedent — replace it.
2. **Behavior over color** — the bigger trust budget goes to microcopy, transparency, save-and-resume, and polish (layout bugs read as compromise).
3. **Fixed semantic colors** — dedicated error/success/warning/focus tokens, never ad-hoc. The current purple "completion" badges violate this; fold into the semantic set.
4. **AA contrast is the floor, encoded in tokens** — every approved pairing below passes 4.5:1 (text) or 3:1 (UI).
5. **Own lane visually** — calmer than LegalZoom/Rocket Lawyer orange-CTA urgency; distinct from court navy + gold + seal dress (impersonation/UPL risk). No gold accent, no seals/gavels/columns iconography.

## Color palette

### Primary (civic blue, hue ~207°, anchored on GOV.UK `#1d70b8`)

| Token | Hex | Use |
|---|---|---|
| primary-50 | `#f0f6fb` | Tinted page/section background (GOV.UK-style) |
| primary-100 | `#dbeaf5` | Selected-card fill, info-banner background |
| primary-200 | `#b7d5ec` | Borders on selected/info surfaces |
| primary-300 | `#85b7dd` | Decorative, disabled-state accents |
| primary-400 | `#4f94c9` | Icons on white (decorative) |
| primary-500 | `#2b7fbe` | Focus rings, UI outlines — 4.30:1 vs white (≥3:1 ✓) |
| primary-600 | `#1d70b8` | **Buttons, links, progress fill** — white text 5.17:1 ✓; on primary-50 4.75:1 ✓ |
| primary-700 | `#175a94` | Hover state — white text 7.18:1 ✓ |
| primary-800 | `#124873` | Info-banner text on primary-100 — 7.77:1 ✓ |
| primary-900 | `#0d3453` | Headings on tinted surfaces — 12.86:1 vs white ✓ |

### Neutrals & text (keep Tailwind gray — verified)

Body text `gray-900 #111827` (17.74:1 on white, 16.29:1 on primary-50 ✓). Secondary text `gray-600 #4b5563` (7.56:1 ✓). `gray-500 #6b7280` passes on white (4.83:1) but is marginal — do not use it on tinted backgrounds; prefer gray-600. Page background: white body, primary-50 for app-shell/section tinting.

### Semantic states (fixed, computed)

| State | Tokens | Verified pairing |
|---|---|---|
| Error | text `red-700 #b91c1c` on white (6.47:1 ✓); banners `red-800 #991b1b` on `red-50 #fef2f2` (7.60:1 ✓) | Error messages/validation ONLY |
| Success | `#0f7a52` (GOV.UK green): as text on white 5.35:1 ✓, white-on-it 5.35:1 ✓; banners `green-800` on `green-50` (6.81:1 ✓) | Success/saved/complete ONLY |
| Warning | `amber-800 #92400e` on `amber-50 #fffbeb` (6.84:1 ✓), `amber-400` border | Caution banners |
| Info | primary-800 on primary-100 (7.77:1 ✓) | Replaces blue-100/blue-600 ad-hoc uses |
| Quick Exit / danger action | white on `red-600 #dc2626` (4.83:1 ✓), hover `red-700` (6.47:1 ✓) | Exit button, destructive confirms |

**Migration rule:** `indigo-*` → `primary-*` (same shade number, mechanical). `purple-*` completion badges → success or primary-100/800. Ad-hoc `blue-*` → info tokens. Reds/greens/ambers already close to spec.

## tailwind.config.js (target state)

```js
theme: {
  extend: {
    colors: {
      primary: { 50:'#f0f6fb', 100:'#dbeaf5', 200:'#b7d5ec', 300:'#85b7dd', 400:'#4f94c9',
                 500:'#2b7fbe', 600:'#1d70b8', 700:'#175a94', 800:'#124873', 900:'#0d3453' },
      success: { 50:'#f0fdf4', 600:'#0f7a52', 800:'#166534' },
    },
    fontFamily: {
      sans: ['"Public Sans"', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"',
             'Roboto', '"Helvetica Neue"', 'Arial', 'sans-serif'],
    },
    fontSize: { base: ['1.0625rem', { lineHeight: '1.6' }] },  // 17px body
  },
}
```

## Typography

- **Public Sans** (Google Fonts or self-host, SIL OFL), weights **400 / 600 / 700 only** — GDS found "mostly one weight and one typeface" tested best with disabled and non-disabled users. Metrics-matched to system fonts, so fallback shift is minimal. Alternates if rejected: Source Sans 3 (VA.gov precedent, strong ESL glyph coverage), Inter.
- **Body 17px, line-height 1.5–1.6** (GOV.UK uses 19px everywhere; USWDS floor 16px + 1.5 leading; WCAG 1.4.8 requires ≥1.5). Never shrink on mobile; nothing users must read below 16px.
- **Measure:** `max-w-[65ch]` on all reading content (help text, previews, legal pages). Hard ceiling 75ch.
- **Scale:** h1 30px/1.2 · h2 24px/1.3 · h3 21px/1.35 (≈ text-3xl/2xl/lg with bumped base). Skip 4xl+ outside marketing.
- **Left-align everything; never `text-justify`;** single-column intake layouts; must survive 200% zoom.
- **Reading level:** 6th grade for intake questions, buttons, errors; 8th grade elsewhere. Paragraphs 1–3 sentences.

## Focus & interaction states

Keep the existing ring pattern, retargeted: `focus:ring-2 focus:ring-offset-2 focus:ring-primary-500` (4.30:1 vs white ≥3:1 ✓). Buttons: primary-600 base / primary-700 hover / ring on focus. Disabled: gray-300 bg + gray-600 text — never convey state by color alone (pair with icon/label).

## Per-screen guidance

- **[Dashboard.tsx](../../frontend/src/components/Dashboard.tsx)** — hero and CTAs indigo→primary; status badges onto semantic tokens: draft=gray, in-progress=primary-100/800, action-needed=warning, complete=success (kill purple). Keep "How It Works" 3-card grid — progress transparency is a verified trust device.
- **[Login.tsx](../../frontend/src/components/auth/Login.tsx) / Register.tsx** — primary buttons; add one reassurance line under the form: padlock icon + "Your information is encrypted and used only to prepare your court forms." (Baymard: homemade badge beats paid seals.) Link Privacy Policy adjacent.
- **[GuidedIntake.tsx](../../frontend/src/components/motion/GuidedIntake.tsx)** — progress fill primary-600 on gray-200. Add: (1) autosave indicator "✓ Saved just now" (success token); (2) "why we ask" helper line on sensitive questions, anchored to the form ("The court requires children's birth dates on FL-300, item 8."); (3) mark optional questions "(optional)", never asterisks; (4) sequence easy factual questions before incident narratives; (5) check-your-answers review screen before generation; (6) auto-filled fields labeled "Filled from your profile — check it's still correct."
- **[MotionPreview.tsx](../../frontend/src/components/motion/MotionPreview.tsx)** — at the LLM-rewrite step, one line: "This rewrite improves the clarity of your own statements. It is not legal advice about what to request." Show current Judicial Council form number + revision date; link the official form on courts.ca.gov (outbound links are a verified credibility signal).
- **[EvidenceManager.tsx](../../frontend/src/components/evidence/EvidenceManager.tsx) / EvidenceForm.tsx** — wrap high-sensitivity inputs (children's DOBs, addresses, incident text) in a single reserved "Protected information" treatment: primary-50 bg, primary-200 border, small padlock. Never reuse this treatment for anything else.
- **[EmergencyHelp.tsx](../../frontend/src/components/emergency/EmergencyHelp.tsx) + Quick Exit** — see spec below.
- **[LegalFooter.tsx](../../frontend/src/components/legal/LegalFooter.tsx)** — Tier-1 disclaimer (below) + "Where to get legal advice" link (lawhelpca.org, court self-help centers) beside it.

## Quick Exit behavioral spec (GOV.UK pattern + CHI 2023)

1. Sticky **top-right**, visible on load and while scrolling, on every DV-sensitive route (violation intake, evidence, emergency) — not on neutral dashboards.
2. Labeled text button — "Exit this page" — red-600, white text; never icon-only.
3. On activation: instant full-screen overlay, then **`window.location.replace('https://www.google.com')`** or a weather site — replace() removes this site from back-button history; plain redirects leak.
4. Triple-Shift keyboard shortcut (5s window, visual progress dots, screen-reader announcements); advertise it next to the button; hidden secondary link for assistive tech.
5. **Nothing may ever cover the button** — toasts, modals, cookie banners must z-index below it (coverage was near-fatal, −99.4%, in CHI testing).
6. Safety interruption page before first sensitive screen: honest that history is NOT erased, recommend unmonitored devices/private browsing; neutral `<title>` on sensitive routes so history entries stay generic.
7. Save-and-exit from every intake step: "Your answers are saved — you can close this safely."

## UPL disclaimer (three tiers — industry-consistent)

- **Tier 1, footer every page:** "Family Court Helper is not a law firm and does not provide legal advice. We provide self-help document preparation tools. Using this site does not create an attorney-client relationship."
- **Tier 2, once at signup/first motion:** short inline acknowledgment inside the flow-entry screen (before effort is invested — NN/g up-front disclosure).
- **Tier 3:** full legalese in Terms only. Never in hero copy; no modal interstitials; hero states what we ARE ("guided tools that help you prepare court-ready RFO documents").

## Branding fixes (trust liabilities today)

- [manifest.json](../../frontend/public/manifest.json): `short_name` "Court Helper", `name` "Family Court Helper", `theme_color` `#1d70b8`, `background_color` `#ffffff`.
- Replace stock CRA favicon/logo192/logo512 with a simple wordmark/monogram in primary-600 — no scales, gavels, or state seals.
- `public/index.html` title + meta description are already fixed (2026-07-10 fix pass); remaining work is keeping per-route document titles generic on sensitive routes (see Quick Exit §6).

## Implementation order (follow-up task)

1. tailwind.config.js tokens + Public Sans + base font size (foundation, no visual break).
2. Mechanical `indigo-*`→`primary-*`, purple/blue ad-hoc → semantic tokens.
3. Manifest/favicon/title branding fixes.
4. Quick Exit hardening (`location.replace`, sticky, shortcut, z-index audit).
5. Microcopy pass: disclaimers, "why we ask", autosave indicator, review screen.

**Verification:** re-run the contrast script on any adjusted values; axe/Lighthouse a11y pass ≥ current; visual QA of every screen listed above (Baymard: layout bugs read as compromise); test Quick Exit against the CHI checklist (back button, history, recent tabs, coverage).
