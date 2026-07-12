# 💰 California Motion Writer - Cost Reduction Plan

## Current Monthly Cost: ~$121.54 (projected)
**Primary Cost Driver:** Cloud SQL instance running 24/7

## 🔍 Resource Audit Results

### 1. **Cloud SQL (BIGGEST COST: ~$100/month)**
- **Instance:** `app-sql`
- **Status:** RUNNING 24/7
- **Tier:** db-custom-2-7680 (2 vCPUs, 7.5GB RAM)
- **Storage:** 10GB
- **Problem:** Over-provisioned for development/inactive project

### 2. **Cloud Run (~$5-10/month)**
- **Service:** `motion-api`
- **Resources:** 2 CPUs, 1GB memory
- **Scaling:** 0-5 instances (scales to 0 when idle)
- **Status:** OK - minimal cost when not in use

### 3. **Vertex AI Vector Search (~$10/month)**
- **Endpoint:** `motion-index-endpoint` (1505347966657888256)
- **Machine Type:** e2-standard-2
- **Problem:** Running but no deployed indexes (wasting resources)

### 4. **Artifact Registry (~$1/month)**
- **Storage:** ~792MB
- **Status:** OK - minimal cost

## 🎯 IMMEDIATE ACTIONS TO REDUCE COSTS

### Option 1: STOP Everything (Save $121/month)
If the project is not actively in use:

```bash
# 1. Stop Cloud SQL instance (saves ~$100/month)
gcloud sql instances patch app-sql --no-activation-policy \
  --project=california-motion-writer

# 2. Delete Vertex AI endpoint (saves ~$10/month)
gcloud ai index-endpoints delete 1505347966657888256 \
  --project=california-motion-writer \
  --region=us-central1

# 3. Cloud Run automatically scales to 0 - no action needed
```

### Option 2: Development Mode (Save ~$90/month)
Keep project functional but reduce costs:

```bash
# 1. Downgrade Cloud SQL to micro instance (saves ~$90/month)
gcloud sql instances patch app-sql \
  --tier=db-f1-micro \
  --project=california-motion-writer

# 2. Delete unused Vertex AI endpoint
gcloud ai index-endpoints delete 1505347966657888256 \
  --project=california-motion-writer \
  --region=us-central1

# 3. Set Cloud Run minimum instances to 0
gcloud run services update motion-api \
  --min-instances=0 \
  --project=california-motion-writer \
  --region=us-central1
```

### Option 3: Scheduled Start/Stop (Save ~$80/month)
Run Cloud SQL only during business hours:

```bash
# Create Cloud Scheduler jobs to start/stop SQL instance
# Start at 8 AM PST Monday-Friday
gcloud scheduler jobs create pubsub sql-start \
  --schedule="0 8 * * 1-5" \
  --topic=sql-scheduler \
  --message-body='{"instance":"app-sql","action":"start"}' \
  --time-zone="America/Los_Angeles" \
  --project=california-motion-writer

# Stop at 6 PM PST Monday-Friday
gcloud scheduler jobs create pubsub sql-stop \
  --schedule="0 18 * * 1-5" \
  --topic=sql-scheduler \
  --message-body='{"instance":"app-sql","action":"stop"}' \
  --time-zone="America/Los_Angeles" \
  --project=california-motion-writer
```

## 📊 Cost Comparison

| Configuration | Cloud SQL | Cloud Run | Vertex AI | Total/Month |
|--------------|-----------|-----------|-----------|-------------|
| **Current** | $100 | $5 | $10 | **$115** |
| **Option 1: Stopped** | $0 | $0 | $0 | **$0** |
| **Option 2: Dev Mode** | $10 | $5 | $0 | **$15** |
| **Option 3: Scheduled** | $30 | $5 | $0 | **$35** |

## ⚡ QUICK COMMAND TO STOP COSTS NOW

Run this to immediately stop the biggest cost (Cloud SQL):

```bash
# Stop Cloud SQL instance RIGHT NOW
gcloud sql instances patch app-sql --no-activation-policy \
  --project=california-motion-writer
```

This will save you ~$100/month immediately!

## 🔄 How to Restart When Needed

When you need to use the project again:

```bash
# Restart Cloud SQL
gcloud sql instances patch app-sql --activation-policy=ALWAYS \
  --project=california-motion-writer

# Your Cloud Run service will auto-start when accessed
# Access at: https://motion-api-mlcaanldqq-uc.a.run.app
```

## 💡 Long-term Recommendations

1. **Use Cloud SQL Proxy for local development** instead of cloud instance
2. **Consider Firebase/Firestore** instead of Cloud SQL for lower costs
3. **Set up billing alerts** at $20/month to catch unexpected costs
4. **Use Cloud SQL only when needed** (start/stop via scripts)
5. **Delete the Vertex AI endpoint** if vector search isn't being used

## 🚨 Set Up Billing Alert

```bash
# Create budget alert at $20/month
gcloud billing budgets create \
  --billing-account=YOUR_BILLING_ACCOUNT \
  --display-name="California Motion Writer Alert" \
  --budget-amount=20 \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=90 \
  --threshold-rule=percent=100
```

## Next Steps

**CHOOSE ONE:**
1. [ ] Run Option 1 commands to stop everything (if not in use)
2. [ ] Run Option 2 commands to switch to dev mode
3. [ ] Set up Option 3 scheduled start/stop

**Recommended: Option 1 (Stop Everything) if project is not actively being used**