# Cost Control Implementation Guide

## 🛡️ Overview

This document details the comprehensive cost control measures implemented to prevent runaway costs in the California Motion Writer application.

## 🔒 Protection Layers

### 1. **Rate Limiting (First Line of Defense)**
- **Per-endpoint limits** to prevent API abuse
- **IP-based and user-based** tracking
- **Sliding window algorithm** for accurate rate limiting

#### Configuration:
```python
# Chat endpoints - higher limits
"/api/v1/chat/messages": "50/hour"

# LLM rewrite endpoints - moderate limits
"/api/v1/llm/rewrite": "20/hour"
"/api/v1/llm/rewrite-declaration": "10/hour"

# Full motion processing - strict limits
"/api/v1/llm/process-motion": "5/hour"
```

### 2. **Smart Token Limits**
- **Dynamic limits by operation type**
- **Maintains quality** while controlling costs

| Operation | Token Limit | Use Case |
|-----------|------------|----------|
| Chat Response | 1,024 | Quick conversations |
| Section Rewrite | 3,000 | Individual sections |
| Declaration | 4,000 | Full declarations |
| Complete Motion | 6,000 | Full documents |

### 3. **User Quotas**
- **Tiered system** (Free/Premium/Enterprise)
- **Daily and monthly limits**
- **Per-user tracking**

#### Free Tier Limits:
- 50,000 tokens/day (~10-15 sections)
- 500,000 tokens/month (~100 sections)
- 5 motions/month maximum

### 4. **Budget Monitoring**
- **Real-time cost tracking**
- **Automatic alerts** at 50%, 75%, 90% of budget
- **Emergency shutdown** at 100% of daily limit ($50)

### 5. **GCP Billing Alerts**
- **Cloud-level budget controls**
- **Pub/Sub notifications**
- **Automatic service scaling to zero** if exceeded

## 📊 Cost Projections

| Scenario | Daily Cost | Monthly Cost | Status |
|----------|------------|--------------|---------|
| Light Use (10 users) | $5-10 | $150-300 | ✅ Safe |
| Normal Use (100 users) | $15-30 | $450-900 | ✅ Controlled |
| Heavy Use (500 users) | $40-50 | $1200-1500 | ⚠️ Monitored |
| Abuse/Attack | **$50 max** | **$500 max** | 🛑 Limited |

## 🚀 Implementation Steps

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
```bash
# Cost limits
export DAILY_COST_LIMIT=50.0
export MONTHLY_COST_LIMIT=500.0

# Emergency shutdown threshold
export EMERGENCY_SHUTDOWN_THRESHOLD=100.0

# Redis URL for distributed rate limiting (production)
export REDIS_URL=redis://localhost:6379
```

### Step 3: Run Billing Alert Setup
```bash
chmod +x scripts/setup_billing_alerts.sh
./scripts/setup_billing_alerts.sh
```

### Step 4: Integrate Middleware
The middleware is automatically integrated in the FastAPI app:

```python
from app.middleware import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)
```

## 🔍 Monitoring

### Real-time Dashboard
Access cost monitoring at `/api/v1/admin/cost-report`:
```json
{
  "current_daily_cost": 12.45,
  "daily_limit": 50.00,
  "tokens_used_today": 145000,
  "alerts": [],
  "by_operation": {
    "section_rewrite": {"requests": 45, "cost": 8.20},
    "declaration": {"requests": 12, "cost": 4.25}
  }
}
```

### Alert Channels
1. **Application Logs** - All cost events logged
2. **GCP Console** - Billing alerts dashboard
3. **Email/SMS** - Configure in GCP Console
4. **Emergency Shutdown** - Automatic at limit

## 🛠️ Testing Cost Controls

### Test Rate Limiting
```python
# Test script to verify rate limiting
import asyncio
import httpx

async def test_rate_limit():
    async with httpx.AsyncClient() as client:
        for i in range(25):  # Try 25 requests
            response = await client.post(
                "http://localhost:8000/api/v1/llm/rewrite",
                json={"text": "test", "operation": "section_rewrite"}
            )
            print(f"Request {i+1}: {response.status_code}")
            if response.status_code == 429:
                print("Rate limit hit successfully!")
                break
```

### Test Budget Limits
```python
# Simulate high token usage
from app.services.cost_monitoring_service import cost_monitor

# This should trigger alerts
await cost_monitor.track_llm_usage(
    operation="test",
    tokens_used=100000,
    model="gemini-pro"
)
```

## 🚨 Emergency Procedures

### If Costs Spike:
1. **Automatic shutdown** triggers at daily limit
2. **Manual shutdown**: Set `EMERGENCY_SHUTDOWN=true`
3. **Scale to zero**: `gcloud run services update motion-api --max-instances=0`
4. **Review logs**: Check for abuse patterns
5. **Adjust limits**: Update rate limits if needed

### Recovery:
1. Clear emergency flag: `unset EMERGENCY_SHUTDOWN`
2. Reset daily counters in Redis
3. Scale service back up
4. Monitor closely for 24 hours

## 📈 Optimization Tips

### Reduce Costs Further:
1. **Use caching** for common sections
2. **Batch operations** where possible
3. **Use Gemini Flash** for simpler tasks
4. **Implement progressive enhancement** (start with less tokens)
5. **Pre-filter** obviously invalid requests

### Monitor Efficiency:
- Track tokens/request ratio
- Identify costly operations
- Review user patterns
- Optimize prompts for efficiency

## ✅ Checklist Before Production

- [ ] GCP billing alerts configured
- [ ] Email notifications set up
- [ ] Redis configured for production
- [ ] Environment variables set
- [ ] Rate limits tested
- [ ] Emergency shutdown tested
- [ ] Cost monitoring dashboard accessible
- [ ] Team trained on emergency procedures
- [ ] Budget approved by stakeholders
- [ ] Backup payment method configured

## 📞 Support

For cost-related issues:
1. Check dashboard: `/api/v1/admin/cost-report`
2. Review logs: `gcloud logging read "severity>=WARNING"`
3. Contact: Set up on-call rotation for budget alerts

## 🔄 Regular Maintenance

### Daily:
- Review cost dashboard
- Check for anomalies
- Verify rate limits working

### Weekly:
- Analyze usage patterns
- Review alert history
- Optimize high-cost operations

### Monthly:
- Full cost audit
- Adjust limits if needed
- Review user tiers
- Plan for scaling

## 📚 Additional Resources

- [GCP Billing Documentation](https://cloud.google.com/billing/docs)
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Rate Limiting Best Practices](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)