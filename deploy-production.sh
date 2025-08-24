#!/bin/bash

# Deploy to Firebase Production Environment
# Usage: ./deploy-production.sh

set -e

echo "🚀 Deploying to Production Environment..."

# Navigate to frontend directory
cd frontend

# Ensure we have production environment variables
if [ ! -f ".env.production" ]; then
    echo "⚠️ Creating .env.production from .env.local..."
    cp .env.local .env.production
fi

# Use production environment variables
cp .env.production .env.local

# Build the application
echo "📦 Building production application..."
npm run build

# Deploy to production
echo "☁️ Deploying to Firebase Hosting production..."
cd ..
npx firebase-tools deploy --only hosting \
  --project california-motion-writer

echo "✅ Production deployment complete!"
echo "🌐 Production URL: https://california-motion-writer.web.app"
echo "🔗 Alternative URL: https://california-motion-writer.firebaseapp.com"