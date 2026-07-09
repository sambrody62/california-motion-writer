"""
Rate limiting middleware for cost control and abuse prevention.

Only paths listed in RATE_LIMITS are enforced (all static). Storage is
in-memory per process unless Redis is configured — with 2 uvicorn workers
the effective limit is up to 2x the configured value, acceptable for MVP.
RATE_LIMIT_ENABLED=false disables enforcement (used by the test suite).
"""
from typing import Optional
from datetime import datetime, timedelta
import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.util import get_remote_address
import logging
import os

from app.middleware.rate_limit_config import RATE_LIMITS
from app.middleware.usage_quotas import UsageQuotaMixin

# Only import redis if not in local development
if os.getenv("ENVIRONMENT") != "development":
    try:
        import redis.asyncio as redis
    except ImportError:
        redis = None
else:
    redis = None

logger = logging.getLogger(__name__)


class RateLimiterMiddleware(UsageQuotaMixin):
    """Rate limiting with token quotas and cost control"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        enable_quotas: bool = True
    ):
        # Redis for distributed rate limiting (production)
        self.redis_client = None
        self.redis_url = redis_url
        self.enable_quotas = enable_quotas

        # In-memory fallback for development
        self.memory_store = defaultdict(lambda: {
            "requests": [],
            "tokens_used": 0,
            "last_reset": datetime.utcnow()
        })

    async def init_redis(self):
        """Initialize Redis connection for production"""
        if self.redis_url:
            try:
                self.redis_client = await redis.from_url(self.redis_url)
                await self.redis_client.ping()
                logger.info("Redis rate limiter connected")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.redis_client = None

    def _get_user_id(self, request: Request) -> str:
        """Extract user identifier from request"""
        # Try to get authenticated user
        if hasattr(request.state, "user") and request.state.user:
            return f"user:{request.state.user.id}"

        # Fall back to IP address
        return f"ip:{get_remote_address(request)}"

    async def check_rate_limit(self, request: Request, endpoint: str) -> bool:
        """Check if request is within rate limits"""
        user_key = self._get_user_id(request)

        limit, period = self._parse_rate_limit(RATE_LIMITS[endpoint])

        # Check using Redis if available
        if self.redis_client:
            return await self._check_redis_rate_limit(user_key, endpoint, limit, period)

        # Fallback to memory store
        return self._check_memory_rate_limit(user_key, endpoint, limit, period)

    def _parse_rate_limit(self, limit_str: str) -> tuple:
        """Parse rate limit string like '20/hour' into (20, 3600)"""
        parts = limit_str.split("/")
        count = int(parts[0])

        period_map = {
            "second": 1,
            "minute": 60,
            "hour": 3600,
            "day": 86400
        }

        period = period_map.get(parts[1], 3600)
        return count, period

    async def _check_redis_rate_limit(
        self,
        user_key: str,
        endpoint: str,
        limit: int,
        period: int
    ) -> bool:
        """Check rate limit using Redis"""
        key = f"rate_limit:{user_key}:{endpoint}"

        try:
            # Use sliding window algorithm
            now = time.time()
            window_start = now - period

            # Remove old entries
            await self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count requests in window
            count = await self.redis_client.zcard(key)

            if count >= limit:
                return False

            # Add current request
            await self.redis_client.zadd(key, {str(now): now})
            await self.redis_client.expire(key, period)

            return True

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return True  # Allow on error

    def _check_memory_rate_limit(
        self,
        user_key: str,
        endpoint: str,
        limit: int,
        period: int
    ) -> bool:
        """Check rate limit using in-memory store"""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=period)

        # Get user data
        user_data = self.memory_store[f"{user_key}:{endpoint}"]

        # Filter requests within window
        user_data["requests"] = [
            req_time for req_time in user_data["requests"]
            if req_time > window_start
        ]

        # Check limit
        if len(user_data["requests"]) >= limit:
            return False

        # Add current request
        user_data["requests"].append(now)
        return True


# Create middleware instance
rate_limiter = RateLimiterMiddleware()


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware enforcing RATE_LIMITS on expensive routes"""
    enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    if not enabled or request.url.path not in RATE_LIMITS:
        return await call_next(request)

    if not await rate_limiter.check_rate_limit(request, request.url.path):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later."
            }
        )

    return await call_next(request)
