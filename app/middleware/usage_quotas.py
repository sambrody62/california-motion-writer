"""
Per-user token/request quota tracking (mixin for RateLimiterMiddleware).

Currently unconsumed by any route — kept for the planned quota rollout.
"""
from typing import Dict
from datetime import datetime
import logging

from app.middleware.rate_limit_config import USER_QUOTAS

logger = logging.getLogger(__name__)


class UsageQuotaMixin:
    """Quota checks and usage recording backed by Redis or memory."""

    async def check_user_quota(
        self,
        user_id: str,
        user_tier: str,
        tokens_requested: int
    ) -> tuple[bool, str]:
        """Check if user has quota for requested tokens"""
        if not self.enable_quotas:
            return True, ""

        quota = USER_QUOTAS.get(user_tier, USER_QUOTAS["free"])

        # Get current usage
        usage = await self._get_user_usage(user_id)

        # Check daily token limit
        if usage["daily_tokens"] + tokens_requested > quota["daily_tokens"]:
            return False, f"Daily token limit exceeded ({quota['daily_tokens']} tokens)"

        # Check monthly token limit
        if usage["monthly_tokens"] + tokens_requested > quota["monthly_tokens"]:
            return False, f"Monthly token limit exceeded ({quota['monthly_tokens']} tokens)"

        # Check daily request limit
        if usage["daily_requests"] >= quota["daily_requests"]:
            return False, f"Daily request limit exceeded ({quota['daily_requests']} requests)"

        # Check concurrent requests
        if usage["concurrent_requests"] >= quota["max_concurrent_requests"]:
            return False, f"Too many concurrent requests (max {quota['max_concurrent_requests']})"

        return True, ""

    async def _get_user_usage(self, user_id: str) -> Dict:
        """Get current usage statistics for user"""
        if self.redis_client:
            return await self._get_redis_usage(user_id)
        return self._get_memory_usage(user_id)

    async def _get_redis_usage(self, user_id: str) -> Dict:
        """Get usage from Redis"""
        try:
            # Keys for different metrics
            daily_tokens_key = f"usage:daily_tokens:{user_id}:{datetime.utcnow().date()}"
            monthly_tokens_key = f"usage:monthly_tokens:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
            daily_requests_key = f"usage:daily_requests:{user_id}:{datetime.utcnow().date()}"
            concurrent_key = f"usage:concurrent:{user_id}"

            # Get values
            daily_tokens = await self.redis_client.get(daily_tokens_key) or 0
            monthly_tokens = await self.redis_client.get(monthly_tokens_key) or 0
            daily_requests = await self.redis_client.get(daily_requests_key) or 0
            concurrent = await self.redis_client.get(concurrent_key) or 0

            return {
                "daily_tokens": int(daily_tokens),
                "monthly_tokens": int(monthly_tokens),
                "daily_requests": int(daily_requests),
                "concurrent_requests": int(concurrent)
            }

        except Exception as e:
            logger.error(f"Redis usage check failed: {e}")
            return {
                "daily_tokens": 0,
                "monthly_tokens": 0,
                "daily_requests": 0,
                "concurrent_requests": 0
            }

    def _get_memory_usage(self, user_id: str) -> Dict:
        """Get usage from memory store"""
        user_data = self.memory_store[f"usage:{user_id}"]

        # Reset daily counters if needed
        if user_data["last_reset"].date() < datetime.utcnow().date():
            user_data["daily_tokens"] = 0
            user_data["daily_requests"] = 0
            user_data["last_reset"] = datetime.utcnow()

        return {
            "daily_tokens": user_data.get("daily_tokens", 0),
            "monthly_tokens": user_data.get("monthly_tokens", 0),
            "daily_requests": user_data.get("daily_requests", 0),
            "concurrent_requests": user_data.get("concurrent_requests", 0)
        }

    async def record_usage(
        self,
        user_id: str,
        tokens_used: int,
        endpoint: str
    ):
        """Record token and request usage"""
        if self.redis_client:
            await self._record_redis_usage(user_id, tokens_used)
        else:
            self._record_memory_usage(user_id, tokens_used)

        # Log high usage for monitoring
        if tokens_used > 5000:
            logger.warning(f"High token usage: {tokens_used} tokens by user {user_id} on {endpoint}")

    async def _record_redis_usage(self, user_id: str, tokens_used: int):
        """Record usage in Redis"""
        try:
            # Update counters
            daily_tokens_key = f"usage:daily_tokens:{user_id}:{datetime.utcnow().date()}"
            monthly_tokens_key = f"usage:monthly_tokens:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
            daily_requests_key = f"usage:daily_requests:{user_id}:{datetime.utcnow().date()}"

            # Increment counters
            await self.redis_client.incrby(daily_tokens_key, tokens_used)
            await self.redis_client.incrby(monthly_tokens_key, tokens_used)
            await self.redis_client.incr(daily_requests_key)

            # Set expiration
            await self.redis_client.expire(daily_tokens_key, 86400)  # 1 day
            await self.redis_client.expire(monthly_tokens_key, 2592000)  # 30 days
            await self.redis_client.expire(daily_requests_key, 86400)

        except Exception as e:
            logger.error(f"Failed to record usage in Redis: {e}")

    def _record_memory_usage(self, user_id: str, tokens_used: int):
        """Record usage in memory"""
        user_data = self.memory_store[f"usage:{user_id}"]
        user_data["daily_tokens"] = user_data.get("daily_tokens", 0) + tokens_used
        user_data["monthly_tokens"] = user_data.get("monthly_tokens", 0) + tokens_used
        user_data["daily_requests"] = user_data.get("daily_requests", 0) + 1
