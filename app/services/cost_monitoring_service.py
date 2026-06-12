"""
Cost monitoring and control service for GCP usage
"""
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import asyncio
from collections import defaultdict

# Conditionally import GCP libraries
USE_GCP = os.getenv("USE_GCP", "true").lower() == "true"

if USE_GCP:
    try:
        from google.cloud import monitoring_v3
        from google.cloud import billing_v1
        from google.cloud import logging as cloud_logging
    except ImportError:
        USE_GCP = False
        print("Warning: GCP monitoring libraries not available")

logger = logging.getLogger(__name__)

# Cost thresholds and alerts
COST_ALERTS = {
    "daily": [
        {"threshold": 10, "level": "info"},
        {"threshold": 25, "level": "warning"},
        {"threshold": 50, "level": "critical"},
        {"threshold": 100, "level": "emergency"}
    ],
    "monthly": [
        {"threshold": 100, "level": "info"},
        {"threshold": 250, "level": "warning"},
        {"threshold": 500, "level": "critical"},
        {"threshold": 1000, "level": "emergency"}
    ]
}

# Service cost estimates (per 1000 tokens)
SERVICE_COSTS = {
    "vertex_ai_gemini_pro": 0.00125,  # $1.25 per 1M tokens
    "vertex_ai_gemini_flash": 0.00035,  # $0.35 per 1M tokens
    "cloud_sql": 0.10,  # Per hour (not per token)
    "cloud_run": 0.00024,  # Per vCPU-second
    "firestore_reads": 0.00004,  # Per document read
    "firestore_writes": 0.00012,  # Per document write
}

@dataclass
class UsageMetrics:
    """Track usage metrics for cost calculation"""
    timestamp: datetime
    service: str
    operation: str
    tokens_used: int = 0
    requests_count: int = 0
    estimated_cost: float = 0.0
    user_id: Optional[str] = None
    metadata: Optional[Dict] = None

class CostMonitoringService:
    """Monitor and control GCP costs"""

    def __init__(self):
        self.project_id = os.getenv("GCP_PROJECT_ID", "california-motion-writer")
        self.daily_limit = float(os.getenv("DAILY_COST_LIMIT", "50.0"))
        self.monthly_limit = float(os.getenv("MONTHLY_COST_LIMIT", "500.0"))

        # In-memory tracking (production would use database)
        self.usage_metrics: List[UsageMetrics] = []
        self.cost_accumulator = defaultdict(float)
        self.alert_history = []

        # Initialize GCP clients if available
        if USE_GCP:
            self._init_gcp_clients()
        else:
            self.monitoring_client = None
            self.billing_client = None

    def _init_gcp_clients(self):
        """Initialize GCP monitoring and billing clients"""
        try:
            self.monitoring_client = monitoring_v3.MetricServiceClient()
            self.billing_client = billing_v1.CloudBillingClient()
            logger.info("GCP monitoring clients initialized")
        except Exception as e:
            logger.error(f"Failed to initialize GCP clients: {e}")
            self.monitoring_client = None
            self.billing_client = None

    async def track_llm_usage(
        self,
        operation: str,
        tokens_used: int,
        model: str = "gemini-pro",
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> UsageMetrics:
        """Track LLM API usage and calculate cost"""
        # Calculate estimated cost
        cost_per_token = SERVICE_COSTS.get(f"vertex_ai_{model}", 0.00125) / 1000
        estimated_cost = tokens_used * cost_per_token

        # Create metrics record
        metric = UsageMetrics(
            timestamp=datetime.utcnow(),
            service="vertex_ai",
            operation=operation,
            tokens_used=tokens_used,
            requests_count=1,
            estimated_cost=estimated_cost,
            user_id=user_id,
            metadata=metadata or {}
        )

        # Store metric
        self.usage_metrics.append(metric)
        self.cost_accumulator[datetime.utcnow().date()] += estimated_cost

        # Check cost thresholds
        await self._check_cost_thresholds()

        # Log high-cost operations
        if estimated_cost > 1.0:
            logger.warning(
                f"High-cost operation: {operation} used {tokens_used} tokens "
                f"(${estimated_cost:.2f}) by user {user_id}"
            )

        return metric

    async def _check_cost_thresholds(self):
        """Check if costs exceed thresholds and trigger alerts"""
        today = datetime.utcnow().date()
        daily_cost = self.cost_accumulator[today]

        # Calculate monthly cost
        month_start = today.replace(day=1)
        monthly_cost = sum(
            cost for date, cost in self.cost_accumulator.items()
            if date >= month_start
        )

        # Check daily thresholds
        for alert in COST_ALERTS["daily"]:
            if daily_cost > alert["threshold"]:
                await self._trigger_alert(
                    f"Daily cost (${daily_cost:.2f}) exceeded ${alert['threshold']}",
                    alert["level"]
                )

        # Check monthly thresholds
        for alert in COST_ALERTS["monthly"]:
            if monthly_cost > alert["threshold"]:
                await self._trigger_alert(
                    f"Monthly cost (${monthly_cost:.2f}) exceeded ${alert['threshold']}",
                    alert["level"]
                )

        # Emergency shutdown if limits exceeded
        if daily_cost > self.daily_limit:
            await self._emergency_shutdown(f"Daily limit ${self.daily_limit} exceeded")
        if monthly_cost > self.monthly_limit:
            await self._emergency_shutdown(f"Monthly limit ${self.monthly_limit} exceeded")

    async def _trigger_alert(self, message: str, level: str):
        """Send cost alert notification"""
        alert = {
            "timestamp": datetime.utcnow(),
            "message": message,
            "level": level
        }

        # Avoid duplicate alerts
        recent_alerts = [
            a for a in self.alert_history
            if (datetime.utcnow() - a["timestamp"]).seconds < 3600
        ]
        if any(a["message"] == message for a in recent_alerts):
            return

        self.alert_history.append(alert)

        # Log alert
        if level == "critical" or level == "emergency":
            logger.critical(f"COST ALERT: {message}")
        elif level == "warning":
            logger.warning(f"Cost warning: {message}")
        else:
            logger.info(f"Cost info: {message}")

        # In production, send email/SMS/Slack notification
        # await self._send_notification(alert)

    async def _emergency_shutdown(self, reason: str):
        """Emergency shutdown to prevent runaway costs"""
        logger.critical(f"EMERGENCY SHUTDOWN: {reason}")

        # Set environment variable to disable LLM
        os.environ["USE_MOCK_LLM"] = "true"
        os.environ["EMERGENCY_SHUTDOWN"] = "true"
        os.environ["SHUTDOWN_REASON"] = reason

        # In production, would also:
        # - Disable Cloud Run service
        # - Send urgent notifications
        # - Create incident ticket

    def get_usage_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        user_id: Optional[str] = None
    ) -> Dict:
        """Generate usage report for specified period"""
        if not start_date:
            start_date = datetime.utcnow().replace(hour=0, minute=0, second=0)
        if not end_date:
            end_date = datetime.utcnow()

        # Filter metrics
        filtered_metrics = [
            m for m in self.usage_metrics
            if start_date <= m.timestamp <= end_date
            and (not user_id or m.user_id == user_id)
        ]

        # Calculate totals
        total_tokens = sum(m.tokens_used for m in filtered_metrics)
        total_requests = sum(m.requests_count for m in filtered_metrics)
        total_cost = sum(m.estimated_cost for m in filtered_metrics)

        # Group by service
        by_service = defaultdict(lambda: {"tokens": 0, "requests": 0, "cost": 0.0})
        for m in filtered_metrics:
            by_service[m.service]["tokens"] += m.tokens_used
            by_service[m.service]["requests"] += m.requests_count
            by_service[m.service]["cost"] += m.estimated_cost

        # Group by operation
        by_operation = defaultdict(lambda: {"tokens": 0, "requests": 0, "cost": 0.0})
        for m in filtered_metrics:
            by_operation[m.operation]["tokens"] += m.tokens_used
            by_operation[m.operation]["requests"] += m.requests_count
            by_operation[m.operation]["cost"] += m.estimated_cost

        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "totals": {
                "tokens": total_tokens,
                "requests": total_requests,
                "estimated_cost": round(total_cost, 2)
            },
            "by_service": dict(by_service),
            "by_operation": dict(by_operation),
            "metrics_count": len(filtered_metrics),
            "daily_limit": self.daily_limit,
            "monthly_limit": self.monthly_limit,
            "current_daily_cost": round(self.cost_accumulator[datetime.utcnow().date()], 2)
        }

    async def check_budget_available(
        self,
        estimated_tokens: int,
        operation: str,
        user_id: Optional[str] = None
    ) -> tuple[bool, str]:
        """Check if budget is available for operation"""
        # Calculate estimated cost
        cost_per_token = SERVICE_COSTS.get("vertex_ai_gemini_pro", 0.00125) / 1000
        estimated_cost = estimated_tokens * cost_per_token

        # Get current usage
        today = datetime.utcnow().date()
        daily_cost = self.cost_accumulator[today]

        # Check if operation would exceed limits
        if daily_cost + estimated_cost > self.daily_limit:
            return False, f"Operation would exceed daily budget limit (${self.daily_limit})"

        # Check monthly limit
        month_start = today.replace(day=1)
        monthly_cost = sum(
            cost for date, cost in self.cost_accumulator.items()
            if date >= month_start
        )

        if monthly_cost + estimated_cost > self.monthly_limit:
            return False, f"Operation would exceed monthly budget limit (${self.monthly_limit})"

        return True, ""

    async def optimize_token_usage(
        self,
        text: str,
        operation_type: str,
        max_tokens: Optional[int] = None
    ) -> Dict:
        """Optimize token usage based on operation type"""
        from app.middleware.rate_limiter import TOKEN_LIMITS

        # Get recommended token limit
        recommended_limit = TOKEN_LIMITS.get(operation_type, 3000)

        if max_tokens:
            recommended_limit = min(recommended_limit, max_tokens)

        # Estimate tokens in text (rough: 1 token ≈ 4 characters)
        estimated_input_tokens = len(text) // 4

        # Calculate available tokens for output
        available_output_tokens = recommended_limit - estimated_input_tokens

        if available_output_tokens < 500:
            # Text too long, need to truncate or summarize
            return {
                "needs_optimization": True,
                "recommended_action": "truncate",
                "original_tokens": estimated_input_tokens,
                "recommended_limit": recommended_limit,
                "available_output_tokens": max(500, available_output_tokens)
            }

        return {
            "needs_optimization": False,
            "recommended_limit": recommended_limit,
            "estimated_input_tokens": estimated_input_tokens,
            "available_output_tokens": available_output_tokens
        }

# Singleton instance
cost_monitor = CostMonitoringService()

# Helper functions for easy integration
async def track_llm_cost(
    operation: str,
    tokens: int,
    user_id: Optional[str] = None
) -> UsageMetrics:
    """Track LLM usage and cost"""
    return await cost_monitor.track_llm_usage(operation, tokens, user_id=user_id)

async def check_budget(
    tokens: int,
    operation: str,
    user_id: Optional[str] = None
) -> tuple[bool, str]:
    """Check if budget available for operation"""
    return await cost_monitor.check_budget_available(tokens, operation, user_id)

def get_cost_report() -> Dict:
    """Get current cost report"""
    return cost_monitor.get_usage_report()