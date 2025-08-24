# TODO_MVP.md

## Phase 0 — Bootstrap (infra scaffolding only)
- [ ] Confirm GCP project: `california-motion-writer`
- [ ] Ensure APIs enabled: Secret Manager, Cloud Run, SQL Admin, Pub/Sub, Vertex AI
- [ ] Add files: CLAUDE.md, TODO_MVP.md, architecture.json

## Phase 1 — Core Scaffold (planning complete, no app code)
- [x] Define DB schema outline (users, profiles, motions)
- [x] Define motion templates (RFO + Response) structure fields
- [x] Define Q&A question set for RFO
- [x] Define LLM prompt outline (tone, constraints, redlines)
- [x] Define PDF layout plan (sections, headers, footer)

## Phase 2 — Core Value (next, when coding starts)
- [ ] Implement guided RFO intake (save answers)
- [ ] LLM rewrite using Vertex AI
- [ ] PDF generation pipeline (Pub/Sub worker)
- [ ] Minimal UI for preview + download

## Phase 3 — Fit & Finish
- [ ] Error states & validation
- [ ] Motion history per user
- [ ] Basic analytics & logs
- [ ] Docs/readme

## Phase 4 — Release
- [ ] Deploy to prod Cloud Run
- [ ] Smoke test end-to-end
- [ ] Collect first user feedback