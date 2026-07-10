# Trust-Oriented Design & Color Research

**Question:** What design and color principles make California Motion Writer feel trustworthy to stressed, self-represented parents — some in DV situations — sharing sensitive family/legal data?

**Date:** 2026-07-10
**Method:** Multi-agent deep-research harness — 5 search angles, 24 sources fetched, 118 claims extracted, top 25 adversarially verified by 3-vote panels (24 confirmed, 1 refuted). Four gap dimensions (legal-tech conventions, sensitive-data patterns, trauma-informed design, typography) filled by targeted follow-up agents reading primary sources; those findings are source-quoted but **not** panel-verified, and are marked ◆.

## Executive summary

Color measurably affects perceived trustworthiness, but the effect is modest — trust is primarily earned through behavior: reliability, transparency, plain language, data stewardship (USWDS's explicit "Earn trust" principle). Within color's real-but-limited influence, evidence converges on: a **blue-family primary** (blue beat red, yellow, and black on trust in controlled experiments; lowest-arousal hue — important for stressed users), at **medium saturation** (high saturation reduced trust ratings and raised physiological arousal), with **near-black text on white at WCAG AA contrast**, which civic systems treat as a legally mandated trust floor. The current default-Tailwind indigo-600 (`#4f46e5`) is a violet-leaning, highly saturated hue with no civic precedent — the evidence argues for a deeper, truer civic blue (GOV.UK `#1d70b8` / CA Oceanside `#046b99` territory). The larger trust budget belongs to behavioral signals: privacy microcopy, progress transparency, save-and-resume, honest UPL disclaimers, and a correctly engineered Quick Exit.

## 1. Color psychology of trust (verified)

**Color scheme causally affects trust judgments — but the effect is small relative to other trust cues.** *(high confidence, 3-0/3-0/3-0)*
Cyr, Head & Larios 2010 (N=90, eye-tracking, 3 countries): "website colour appeal is a significant determinant for website trust and satisfaction." Alberts & van der Geest 2011 (N>200, identical finance/**legal**/medical sites in 4 colorways): different colors got statistically different trust ratings, but "color has a statistically significant but limited effect, compared with all other reasons people can have to trust a Web site." → Invest in color deliberately; weight behavioral signals higher.

**Blue is the most consistently trust-associated hue** — outperforming red, yellow, black in controlled experiments, in both implicit (IAT) and explicit measures. *(high confidence, 3-0/3-0/2-1/3-0)*
Alberts & van der Geest: blue > green > red > black on trust for identical sites. Cyr et al.: blue beat yellow; yellow disliked across all three cultures. Su, Cui & Walsh 2019: blue > red across three studies including implicit-association tests — the association is automatic. Caveats: culturally moderated (Canadians preferred grey; Germans rated blue highest); 2019 study was blue-vs-red on logos only.

**High saturation is wrong for a trust-critical app serving stressed users.** *(high confidence, 4× 3-0)*
Skulmowski et al. 2016 (50 sites, 10 domains): "negative effects of saturation [on trustworthiness and appeal] depending on the content domain." Wilms & Oberfeld 2018 (N=62, colorimetrically controlled): saturation had the largest arousal effect of hue/saturation/brightness (η²=.693); saturated colors produced stronger skin-conductance responses; **valence peaked at medium saturation**; blue was the lowest-arousal hue. → Medium-saturation deep blue primary; no neon/garish accents.

**Trust judgments are downstream of first-impression aesthetics.** *(medium confidence — single-study temporal model)*
Skulmowski's model: visual appeal → usability → trust (finalized last; first impressions form at ~50ms per Lindgaard). Pelet et al. 2013: color's trust effect operates through induced emotion. A related claim ("color raises trust only when arousal is high") was **refuted 0-3** in verification. → Polish and calm emotional tone are prerequisites, not decoration.

## 2. Civic/government design systems (verified)

**GOV.UK** anchors on one restrained brand blue **`#1d70b8`** (brightened from `#005ea5` in a 2019 accessibility refresh), near-black text `#0b0c0c` on white, tinted template background `#f4f8fb`. Key rationale: "the new colours use brightness and saturation to provide contrast, rather than simply adding black" — accessible palettes need not be dark or dull. *(high, 3× 3-0)*

**WCAG AA contrast is treated as a legal mandate, and USWDS encodes it arithmetically**: a 100-point luminance-normalized grade scale where a grade difference of 50+ guarantees AA (40+ AA-large, 70+ AAA). Tailwind's default palette is **not** luminance-normalized across hues — the guarantee only holds with custom values. *(high, 3-0/3-0/2-1/3-0)*

**Fixed semantic state colors, never ad-hoc**: GOV.UK ships dedicated tokens — error red `#ca3535` (error messages only), success green `#0f7a52` (success only), focus yellow `#ffdd00` with dark `#0b0c0c` focus text. *(medium — single system, corroborated via govuk-frontend releases)*

**USWDS locates trust in behavior, not visuals**: "Earn trust" is a core principle — "Trust has to be earned every time… Be reliable, consistent, and honest… Be a good steward of your audience's data, resources, and time." Its design-principles page contains **zero** color guidance. Its complete-a-complex-form pattern operationalizes trust as: transparency about data use, plain language, expectation-setting, save-and-resume, answer verification. *(high, 2× 3-0)*

**California's own web identity** (State Web Template, default "Oceanside" theme): deep blue `#046b99` primary, dark slate `#323a45`, single gold accent `#fdb81e`. Users arriving from ca.gov/courts.ca.gov are primed by this vocabulary. *(high, 3-0; note ca.gov itself uses the newer California Design System)*

## 3. Legal-tech conventions ◆ (targeted follow-up)

- **Observed palettes (live-site extraction, 2026-07-10, approximate):** LegalZoom — warm cream neutrals + hot orange CTA `#f45a27`, sales-energy tone. Rocket Lawyer — dark ink + orange `#d68021`. **Hello Divorce — calm deep teal-blue `#006080` + soft sky tints**, empathy-first voice ("Divorce is *hard*. The legal part doesn't have to be."). The nearest correct neighbor for us is Hello Divorce's lane; the orange-CTA urgency cliché is the anti-pattern for stressed parents.
- **Do not impersonate the courts**: CA self-help portal owns institutional dark-blue + seal + .gov dress. Gavel's UPL analysis: product design and *marketing copy* determine whether a tool crosses into legal advice — visual court-impersonation compounds UPL exposure.
- **CA Courts self-help redesign (Chapter Three)**: task-first IA ("What Would You Like to Do?"), plain language, scenario-based decision trees — validates our guided-Q&A structure.
- **UPL disclaimer pattern (consistent across LegalZoom / Rocket Lawyer / Hello Divorce)**: one-sentence persistent footer fine print on every page ("X is not a law firm and does not provide legal advice…"), full legalese in ToS only, **never** in hero/onboarding copy, no scary modals. Hello Divorce pairs the disclaimer with visible paths to real attorneys — converting a liability notice into a helpfulness signal.
- Gavel: "Clear disclaimers, user agreements, and **consistent** messaging" — repeated light-touch messaging beats one-time walls of text. Rules-based document assembly from user input (the North Carolina precedent) is the safe-harbor design pattern vs. personalized recommendations.

## 4. Sensitive-data trust patterns ◆ (targeted follow-up)

- **Baymard (primary research)**: perceived security is divorced from actual security. Visually encapsulating sensitive fields (distinct border/shading, reserved *only* for those fields) increases perceived security. A "homemade" padlock + reassurance label beat most paid SSL seals in 2023 testing. **Layout bugs destroy trust** — users read visual glitches as compromise ("This looks a bit strange. Especially when you are about to pay.").
- **NN/g trustworthiness factors**: design quality ("Typos… communicate disregard for the users"); up-front disclosure before users invest effort; comprehensive/correct/**current** content (stale Judicial Council form revs would be trust-fatal for us); confident outbound links — "third-party sites are much more credible than anything you can say yourself" → link to courts.ca.gov in-context.
- **GOV.UK question pages**: "make sure it's clear to users why you're asking each question"; one thing per page; mark optional fields "(optional)", never asterisk mandatory ones; "only ask for a piece of information once within a single journey" (validates profile auto-fill); check-your-answers review page before submission.

## 5. Trauma-informed & quick-exit design ◆ (targeted follow-up)

- **GOV.UK "Exit this page" pattern (tested with DV survivors)**: red warning-style button, top of page, instant loading overlay, default redirect to BBC Weather (plausible neutral site); triple-Shift keyboard shortcut with 5s window, progress dots, screen-reader announcements; hidden secondary link for AT users; honest disclosure that browsing history is **not** erased; a safety interruption page before the sensitive flow; do *not* put the pattern on neutral dashboards.
- **Turk & Hutchings, CHI 2023 (peer-reviewed, 2,045 sites)**: 80.3% of DV-service sites have exit buttons — a de facto expectation. **Most secure implementation: `window.location.replace()`** (removes the site from back-button history); plain redirects leak via back button/history. Optimal placement top-right (+186% discoverability); **sticky-on-scroll is the biggest usability factor (+816%)**; anything covering the button (cookie banners, modals) is near-fatal (−99.4%); labeled text buttons beat icons (+387%); advertise the keyboard shortcut next to the button.
- **NNEDV Safety Net**: quick exit only defeats shoulder-surfing; be honest that monitored devices and history are out of scope; safest advice is an unmonitored device.
- **GSA 10x trauma-informed design + SAMHSA principles** (Safety, Trustworthiness & Transparency, Choice, Collaboration, Empowerment): save-and-exit everywhere (VA forms "sometimes take months to complete"); sequence easy factual questions before emotionally hard ones; participant autonomy to stop; helplines at the end of hard sections.
- **Content Design London**: frontload what to expect; stress hormones impair comprehension, so plain language is a *functional* requirement; state timescales, save options, next steps; test flows with survivors via advocacy-org intermediaries.

## 6. Accessibility & typography as trust ◆ (verified for contrast; follow-up for type)

- Contrast: AA (4.5:1 text, 3:1 UI components) is the non-negotiable floor (verified — see §2). WebAIM corroborates.
- **WCAG 1.4.8**: line spacing ≥1.5 within paragraphs; max ~80-char lines; never justify text; 200% zoom without horizontal scroll.
- **GOV.UK type scale**: 19px body on *all* screens (2022: removed 14px entirely; shrinking text on mobile "negatively impacts those with visual impairments"). GDS on font choice: "We looked around for an extremely legible typeface… good enough for us not to need an 'easier to read' font option for the dyslexic." Their biggest accessibility win was "simplifying everything on the site — including the language."
- **USWDS**: Public Sans ("strong, neutral… derived from Libre Franklin", metrics-matched to system fonts); ≥16px body; line height ≥1.5 for long text; 45–90 char measure, 66 target.
- **NN/g low-literacy research**: ~43% of US adults have low literacy; they read word-by-word and skip dense blocks. Target **6th-grade reading level** for key pages, 8th elsewhere. Rewriting a site to a lower grade level raised task success 46%→82% and cut task time 22.3→9.5 min — and helped high-literacy users too.

## Refuted in verification

- "Color's positive trust effect is conditional on high user arousal" — **killed 0-3**. Do not design for arousal; for this audience, calm is the goal.

## Caveats

- The color-trust effect is small and culturally moderated — relevant for a diverse, heavily Spanish-speaking CA user base (open question: does blue-trust hold for this demographic?).
- Wilms & Oberfeld used color patches, not interfaces; blue-calm held for self-report, not cleanly for physiology, and vanishes at very low saturation. Skulmowski's saturation effect was domain-moderated (legal not tested).
- ◆ sections are primary-source-quoted but not adversarially panel-verified. Legal-tech hex values are live-site extractions, approximate.
- GOV.UK values reflect the post-2025 brand refresh; Oceanside is the default of 12 CA template themes; Section 508 references WCAG 2.0 AA while DOJ's ADA Title II rule points to WCAG 2.1 AA.

## Key sources

Academic: Cyr/Head/Larios 2010 (sciencedirect S1071581909001116) · Alberts & van der Geest 2011 · Su/Cui/Walsh 2019 · Skulmowski 2016 (S0747563216302254) · Wilms & Oberfeld 2018 · Turk & Hutchings CHI 2023 (dl.acm.org/10.1145/3544548.3581078).
Civic: design-system.service.gov.uk (colour, type-scale, exit-a-page-quickly, question-pages) · designsystem.digital.gov (design-principles, color & typesetting tokens) · template.webstandards.ca.gov · 10x.gsa.gov trauma-informed design · SAMHSA SMA14-4884 · w3.org WCAG 1.4.8 · section508.gov.
Industry: baymard.com perceived-security · nngroup.com communicating-trustworthiness & lower-literacy · techsafety.org (NNEDV) · gavel.io UPL · chapterthree.com CA courts case study · yeti.co Hello Divorce case study · live-site palette extraction (LegalZoom, Rocket Lawyer, Hello Divorce).

**Companion document:** [design-spec.md](design-spec.md) — the palette, tokens, typography, and per-screen application of these findings.
