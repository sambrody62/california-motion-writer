#!/bin/bash

# Deploy to Firebase Staging Environment
# Usage: ./deploy-staging.sh

set -e

echo "🚀 Deploying to Staging Environment..."

# Navigate to frontend directory
cd frontend

# Use staging environment variables
cp .env.staging .env.local

# Build the application
echo "📦 Building staging application..."
npm run build

# Deploy to staging channel
echo "☁️ Deploying to Firebase Hosting staging channel..."
cd ..
npx firebase-tools hosting:channel:deploy staging \
  --project california-motion-writer \
  --expires 30d

# Restore production env
cd frontend
cp .env.production .env.local 2>/dev/null || true

echo "✅ Staging deployment complete!"
echo "🌐 Staging URL: https://california-motion-writer--staging-40cuimee.web.app"
echo "📅 This staging URL expires in 30 days"