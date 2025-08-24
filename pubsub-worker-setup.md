# Pub/Sub Worker Setup for PDF Generation

## Current Setup
- **Topic**: `app-events` (created)
- **Project**: california-motion-writer
- **Region**: us-central1

## Future Worker Setup

When ready to add PDF generation worker, run:

```bash
# Create subscription for the worker
gcloud pubsub subscriptions create app-events-worker \
  --topic=app-events \
  --ack-deadline=60

# Deploy worker as Cloud Run service
gcloud run deploy pdf-worker \
  --image=gcr.io/california-motion-writer/pdf-worker:latest \
  --region=us-central1 \
  --platform=managed \
  --no-allow-unauthenticated \
  --set-env-vars="DB_HOST=/cloudsql/california-motion-writer:us-central1:app-sql,DB_NAME=appdb,DB_USER=appuser,DB_PASSWORD_SECRET=motion-db-password" \
  --add-cloudsql-instances="california-motion-writer:us-central1:app-sql"

# Connect Pub/Sub to trigger the worker
gcloud run services add-iam-policy-binding pdf-worker \
  --region=us-central1 \
  --member=serviceAccount:service-479935274378@gcp-sa-pubsub.iam.gserviceaccount.com \
  --role=roles/run.invoker

# Create push subscription
gcloud pubsub subscriptions create app-events-worker-push \
  --topic=app-events \
  --push-endpoint=$(gcloud run services describe pdf-worker --region=us-central1 --format='value(status.url)')/process \
  --push-auth-service-account=service-479935274378@gcp-sa-pubsub.iam.gserviceaccount.com
```

## Message Format Example

```json
{
  "action": "generate_pdf",
  "motion_id": "123",
  "user_id": "456",
  "template": "california_motion",
  "data": {
    "case_number": "2024-CV-001234",
    "party_names": "Plaintiff v. Defendant",
    "motion_type": "Motion to Compel Discovery"
  }
}
```

## Testing

```bash
# Publish test message
gcloud pubsub topics publish app-events \
  --message='{"action":"generate_pdf","motion_id":"test-123"}'

# Check subscription metrics
gcloud pubsub subscriptions pull app-events-worker --auto-ack --limit=1
```