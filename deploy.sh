#!/bin/bash

# California Motion Writer - Build and Deploy Script
# This script builds the Docker image and deploys to Cloud Run

set -e  # Exit on error

# Configuration
PROJECT_ID="california-motion-writer"
REGION="us-central1"
SERVICE_NAME="motion-api"
IMAGE_NAME="motion-writer"

echo "🚀 California Motion Writer - Deployment Script"
echo "============================================"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
echo "📋 Setting GCP project to: $PROJECT_ID"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    containerregistry.googleapis.com \
    secretmanager.googleapis.com \
    sqladmin.googleapis.com \
    aiplatform.googleapis.com

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t gcr.io/$PROJECT_ID/$IMAGE_NAME:latest .

# Push to Google Container Registry
echo "📤 Pushing image to GCR..."
docker push gcr.io/$PROJECT_ID/$IMAGE_NAME:latest

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --add-cloudsql-instances $PROJECT_ID:$REGION:app-sql \
    --set-env-vars "DB_HOST=/cloudsql/$PROJECT_ID:$REGION:app-sql" \
    --set-env-vars "DB_NAME=appdb" \
    --set-env-vars "DB_USER=appuser" \
    --set-env-vars "DB_PASSWORD_SECRET=motion-db-password" \
    --set-env-vars "PUBSUB_TOPIC=app-events" \
    --set-env-vars "PROJECT_ID=$PROJECT_ID" \
    --set-env-vars "ENVIRONMENT=production" \
    --set-secrets "DB_PASSWORD=motion-db-password:latest" \
    --service-account motion-api@$PROJECT_ID.iam.gserviceaccount.com \
    --memory 1Gi \
    --cpu 1 \
    --timeout 60 \
    --concurrency 80 \
    --max-instances 10

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "============================================"
echo "Service URL: $SERVICE_URL"
echo ""
echo "Next steps:"
echo "1. Visit $SERVICE_URL to test the application"
echo "2. Download official CA court forms and place in forms/ directory"
echo "3. Run database migrations: gcloud run jobs execute migrate-db"
echo "4. Test the API endpoints:"
echo "   - Health check: $SERVICE_URL/health"
echo "   - API docs: $SERVICE_URL/docs"
echo ""
echo "To view logs:"
echo "gcloud run services logs read $SERVICE_NAME --region $REGION"