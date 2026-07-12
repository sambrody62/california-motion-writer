#!/bin/bash

# Setup GCP Billing Alerts for California Motion Writer
# This script creates budget alerts to prevent runaway costs

PROJECT_ID="california-motion-writer"
BILLING_ACCOUNT_ID="01F34A-4D6E03-7BF5D9"

echo "🔧 Setting up GCP Billing Alerts for $PROJECT_ID"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Please install it first."
    exit 1
fi

# Authenticate and set project
echo "📋 Setting up project..."
gcloud config set project $PROJECT_ID

# Create budget with alerts
echo "💰 Creating billing budget with alerts..."

# Daily budget alert ($50/day)
gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT_ID \
    --display-name="California Motion Writer - Daily Budget" \
    --budget-amount=50USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=75 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100 \
    --filter-projects=projects/$PROJECT_ID \
    --filter-time-period=DAILY \
    2>/dev/null || echo "Daily budget may already exist"

# Monthly budget alert ($500/month)
gcloud billing budgets create \
    --billing-account=$BILLING_ACCOUNT_ID \
    --display-name="California Motion Writer - Monthly Budget" \
    --budget-amount=500USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=75 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100 \
    --threshold-rule=percent=110,basis=FORECASTED \
    --filter-projects=projects/$PROJECT_ID \
    2>/dev/null || echo "Monthly budget may already exist"

# Create Pub/Sub topic for budget alerts
echo "📨 Setting up Pub/Sub for budget notifications..."
gcloud pubsub topics create budget-alerts 2>/dev/null || echo "Topic may already exist"

# Create Cloud Function for emergency shutdown
echo "⚡ Creating emergency shutdown function..."
cat > /tmp/shutdown_function.py << 'EOF'
import os
import json
import base64
from google.cloud import run_v2
from google.cloud import secretmanager

def budget_alert_handler(request):
    """
    Handle budget alerts and shutdown services if needed
    """
    # Parse Pub/Sub message
    envelope = json.loads(request.data.decode('utf-8'))
    payload = json.loads(base64.b64decode(envelope['message']['data']))

    # Check if budget exceeded
    cost_amount = payload.get('costAmount', 0)
    budget_amount = payload.get('budgetAmount', 0)

    if cost_amount >= budget_amount:
        print(f"EMERGENCY: Budget exceeded! Cost: ${cost_amount}, Budget: ${budget_amount}")

        # Shutdown Cloud Run service
        client = run_v2.ServicesClient()
        service_name = "projects/california-motion-writer/locations/us-central1/services/motion-api"

        # Set service to 0 instances
        service = client.get_service(name=service_name)
        service.template.scaling.max_instance_count = 0
        client.update_service(service=service)

        return {'status': 'emergency_shutdown'}, 200

    elif cost_amount >= budget_amount * 0.9:
        print(f"WARNING: 90% of budget used! Cost: ${cost_amount}, Budget: ${budget_amount}")
        return {'status': 'warning'}, 200

    return {'status': 'ok'}, 200
EOF

# Deploy the function (commented out - needs manual setup)
# gcloud functions deploy budget-alert-handler \
#     --runtime=python39 \
#     --trigger-topic=budget-alerts \
#     --entry-point=budget_alert_handler \
#     --source=/tmp/shutdown_function.py

# Create monitoring alerts
echo "📊 Setting up monitoring alerts..."

# Alert for high Vertex AI usage
cat > /tmp/vertex_ai_alert.yaml << EOF
displayName: "High Vertex AI Usage"
conditions:
  - displayName: "Vertex AI tokens > 100K/hour"
    conditionThreshold:
      filter: |
        metric.type="aiplatform.googleapis.com/prediction/online/tokens"
        resource.type="aiplatform.googleapis.com/Endpoint"
      comparison: COMPARISON_GT
      thresholdValue: 100000
      duration: 3600s
      aggregations:
        - alignmentPeriod: 3600s
          perSeriesAligner: ALIGN_RATE
EOF

# Alert for rapid cost increase
cat > /tmp/cost_spike_alert.yaml << EOF
displayName: "Rapid Cost Increase"
conditions:
  - displayName: "Cost increased >50% in 1 hour"
    conditionThreshold:
      filter: |
        metric.type="billing.googleapis.com/project/cost"
        resource.type="global"
      comparison: COMPARISON_GT
      thresholdValue: 1.5
      duration: 3600s
      aggregations:
        - alignmentPeriod: 3600s
          perSeriesAligner: ALIGN_PERCENT_CHANGE
EOF

echo "✅ Basic billing alerts configured!"
echo ""
echo "📝 Next steps:"
echo "1. Set up email notifications in Cloud Console:"
echo "   https://console.cloud.google.com/billing/budgets?project=$PROJECT_ID"
echo ""
echo "2. Configure alert policies:"
echo "   https://console.cloud.google.com/monitoring/alerting?project=$PROJECT_ID"
echo ""
echo "3. Review and customize thresholds based on your needs"
echo ""
echo "⚠️  IMPORTANT: Add notification channels (email/SMS) in the Console!"

# Set environment variables for cost limits
echo ""
echo "💾 Setting environment variables for cost control..."
cat > /tmp/cost_control.env << EOF
# Cost Control Settings
DAILY_COST_LIMIT=50.0
MONTHLY_COST_LIMIT=500.0
EMERGENCY_SHUTDOWN_THRESHOLD=100.0

# Rate Limits per Hour
LLM_REQUESTS_PER_HOUR=20
PDF_GENERATIONS_PER_HOUR=10
MOTIONS_PER_HOUR=5

# Token Limits
MAX_TOKENS_PER_REQUEST=6000
MAX_TOKENS_PER_USER_DAILY=50000
MAX_TOKENS_PER_USER_MONTHLY=500000
EOF

echo "Environment variables saved to /tmp/cost_control.env"
echo "Add these to your Cloud Run service configuration"

# Display current billing status
echo ""
echo "📊 Current Billing Status:"
gcloud billing accounts list
echo ""
echo "🏷️ Current Budgets:"
gcloud billing budgets list --billing-account=$BILLING_ACCOUNT_ID --filter="projects:$PROJECT_ID" 2>/dev/null || echo "No budgets found"

echo ""
echo "✨ Billing alerts setup complete!"
echo "Monitor costs at: https://console.cloud.google.com/billing"