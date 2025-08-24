# CLAUDE.md — Project Context

## Vision
- One-liner: Generate professional California family court motions with guided Q&A and LLM rewrite, exportable as ready-to-file PDFs.
- Users & pain: Parents in California custody disputes who cannot afford lawyers, struggling to draft proper motions.
- Value proposition: Guided intake + auto-fill from stored profile info + LLM rewrite ensures clear, court-appropriate motions without high legal fees.
- Success metric (14 days): Produce one complete, filed-ready RFO motion PDF from stored profile + guided Q&A.

## MVP Scope
- Must-have: RFO + Response motions; user auth; profile storage & auto-fill; guided Q&A; LLM rewrite; PDF export.
- Nice-to-have: All CA family motions; county-specific templates; e-filing; rich editor; analytics.
- Absolute minimum: Logged-in user generates an RFO PDF with stored profile + guided Q&A + LLM rewrite.

## Flow (simplest)
Sign up → pick "RFO" or "Respond" → auto-fill profile → guided Q&A → LLM rewrite → preview → PDF.

## Stack (Chosen)
- Cloud: GCP (us-central1)
- Compute: Cloud Run
- Data: Cloud SQL (Postgres) + Vertex AI Matching Engine (vector search)
- AI: Vertex AI (rewrite/orchestration)
- Messaging: Pub/Sub
- Auth: Google Identity Platform
- Secrets: Secret Manager
- Logging: Cloud Logging & Error Reporting

## Non-functional
- Transactional consistency for profiles & motions
- Dev + Prod environments
- TLS in transit; secrets in Secret Manager

## GCP Infrastructure

### Project Details
- **Project ID**: california-motion-writer
- **Project Number**: 479935274378
- **Owner**: sambrody34@gmail.com
- **Billing Account**: 01F34A-4D6E03-7BF5D9
- **Region**: us-central1

### Cloud SQL (PostgreSQL)
- **Instance**: app-sql
- **Database**: appdb
- **User**: appuser
- **Password Secret**: motion-db-password
- **Connection Name**: california-motion-writer:us-central1:app-sql

### Cloud Run Service
- **Service Name**: motion-api
- **URL**: https://motion-api-mlcaanldqq-uc.a.run.app
- **Environment Variables**:
  - DB_HOST: /cloudsql/california-motion-writer:us-central1:app-sql
  - DB_NAME: appdb
  - DB_USER: appuser
  - DB_PASSWORD_SECRET: motion-db-password
  - PUBSUB_TOPIC: app-events

### Pub/Sub
- **Topic**: app-events
- **Purpose**: Async processing for PDF generation and other tasks

### Vertex AI Vector Search
- **Index ID**: 8771272646722584576
- **Index Name**: motion-index
- **Endpoint ID**: 1505347966657888256
- **Endpoint Name**: motion-index-endpoint
- **Deployed Index ID**: motion_index_deployed
- **Dimensions**: 768 (for embeddings)
- **GCS Bucket**: gs://california-motion-writer-vectors/

### Enabled APIs
- Secret Manager
- Cloud Run
- Cloud SQL Admin
- Pub/Sub
- AI Platform (Vertex AI)

## Development Commands

### Database Connection
```bash
# Connect to Cloud SQL via proxy
gcloud sql connect app-sql --user=appuser --database=appdb
```

### Deploy Updates
```bash
# Build and deploy new Cloud Run revision
gcloud run deploy motion-api \
  --image=gcr.io/california-motion-writer/motion-writer:latest \
  --region=us-central1
```

### Testing
```bash
# Test Cloud Run endpoint
curl https://motion-api-mlcaanldqq-uc.a.run.app

# Publish test message to Pub/Sub
gcloud pubsub topics publish app-events \
  --message='{"action":"test","data":"hello"}'
```

### Monitoring
```bash
# View Cloud Run logs
gcloud run services logs read motion-api --region=us-central1

# Check SQL instance status
gcloud sql instances describe app-sql
```

## Next Steps
1. Implement the actual motion writer application code
2. Create Docker image and push to GCR
3. Set up CI/CD pipeline
4. Implement PDF generation worker
5. Add authentication and authorization
6. Create frontend application

## Important Notes
- The Cloud Run service currently uses a demo image (gcr.io/cloudrun/hello)
- Database password is stored securely in Secret Manager
- Vector index deployment takes 10-20 minutes to complete
- All infrastructure is in us-central1 region for optimal performance

## Useful Links
- [GCP Console](https://console.cloud.google.com/home/dashboard?project=california-motion-writer)
- [Cloud Run Service](https://console.cloud.google.com/run/detail/us-central1/motion-api/metrics?project=california-motion-writer)
- [Cloud SQL Instance](https://console.cloud.google.com/sql/instances/app-sql/overview?project=california-motion-writer)