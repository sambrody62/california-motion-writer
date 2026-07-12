"""
Rate limiting middleware for cost control and abuse prevention.

Only paths listed in RATE_LIMITS are enforced (all static). Storage is
in-memory per process unless Redis is configured — with 2 uvicorn workers
the effective limit is up to 2x the configured value, acceptable for MVP.
RATE_LIMIT_ENABLED=false disables enforcement (used by the test suite).

Implemented as pure ASGI middleware (not BaseHTTPMiddleware): the original
receive channel is passed through untouched so downstream
request.is_disconnected() sees real http.disconnect events, letting the
process-motion abort hook stop paid LLM calls when the client goes away.
"""
from typing import Optional
from datetime import datetime, timedelta
import time
from collections import defaultdict
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi.util import get_remote_address
from starlette.types import ASGIApp, Receive, Scope, Send
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


class RateLimiter(UsageQuotaMixin):
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

    async def check_rate_limit(self, request: Request, endpoint: str) -> tuple:
        """(allowed, retry_after_seconds) — retry_after is 0 when allowed"""
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
    ) -> tuple:
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
                # Oldest request's slot frees up first
                oldest = await self.redis_client.zrange(key, 0, 0, withscores=True)
                retry_after = int(oldest[0][1] + period - now) + 1 if oldest else period
                return False, max(retry_after, 1)

            # Add current request
            await self.redis_client.zadd(key, {str(now): now})
            await self.redis_client.expire(key, period)

            return True, 0

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return True, 0  # Allow on error

    def _check_memory_rate_limit(
        self,
        user_key: str,
        endpoint: str,
        limit: int,
        period: int
    ) -> tuple:
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
            # Oldest request's slot frees up first
            oldest = user_data["requests"][0]
            retry_after = int((oldest + timedelta(seconds=period) - now).total_seconds()) + 1
            return False, max(retry_after, 1)

        # Add current request
        user_data["requests"].append(now)
        return True, 0


# Create shared limiter instance
rate_limiter = RateLimiter()


class RateLimiterMiddleware:
    """Pure ASGI middleware enforcing RATE_LIMITS on expensive routes"""

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        path = scope["path"]
        if not enabled or path not in RATE_LIMITS:
            await self.app(scope, receive, send)
            return

        allowed, retry_after = await rate_limiter.check_rate_limit(
            Request(scope), path
        )
        if not allowed:
            response = JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later."
                },
                headers={"Retry-After": str(retry_after)}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
