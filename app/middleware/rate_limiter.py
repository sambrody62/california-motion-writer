"""
Rate limiting middleware for cost control and abuse prevention
"""
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import time
import asyncio
from collections import defaultdict
from fastapi import HTTPException, Request, Response
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json
import logging
import os

# Only import redis if not in local development
if os.getenv("ENVIRONMENT") != "development":
    try:
        import redis.asyncio as redis
    except ImportError:
        redis = None
else:
    redis = None

logger = logging.getLogger(__name__)

# Rate limit configurations by endpoint type
RATE_LIMITS = {
    # Chat endpoints - higher limits for conversation
    "/api/v1/chat/messages": "50/hour",
    "/api/v1/chat/sessions": "20/hour",

    # LLM rewrite endpoints - moderate limits
    "/api/v1/llm/rewrite": "20/hour",
    "/api/v1/llm/rewrite-declaration": "10/hour",
    "/api/v1/llm/enhance-best-interests": "10/hour",

    # Full motion processing - strict limits
    "/api/v1/llm/process-motion": "5/hour",
    "/api/v1/documents/generate-pdf": "10/hour",

    # Violation processing
    "/api/v1/violations/process": "5/hour",

    # Default for other endpoints
    "default": "100/hour"
}

# Token limits by operation type
TOKEN_LIMITS = {
    "chat_response": 1024,
    "section_rewrite": 3000,
    "declaration": 4000,
    "complete_motion": 6000,
    "best_interests": 3500,
    "violation_filing": 4000,
    "max_per_request": 6000  # Reduced from 8192 for cost control
}

# User quota configurations
USER_QUOTAS = {
    "free": {
        "daily_tokens": 50000,      # ~10-15 sections
        "monthly_tokens": 500000,   # ~100 sections
        "daily_requests": 100,
        "monthly_requests": 2000,
        "max_motions_per_month": 5,
        "max_concurrent_requests": 2
    },
    "premium": {
        "daily_tokens": 200000,     # ~40-60 sections
        "monthly_tokens": 2000000,  # ~400 sections
        "daily_requests": 500,
        "monthly_requests": 10000,
        "max_motions_per_month": 50,
        "max_concurrent_requests": 5
    },
    "enterprise": {
        "daily_tokens": 1000000,
        "monthly_tokens": 10000000,
        "daily_requests": 2000,
        "monthly_requests": 50000,
        "max_motions_per_month": -1,  # Unlimited
        "max_concurrent_requests": 10
    }
}

class RateLimiterMiddleware:
    """Advanced rate limiting with token quotas and cost control"""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        enable_quotas: bool = True
    ):
        # Initialize slowapi limiter
        self.limiter = Limiter(key_func=self._get_user_id)

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

        # Get rate limit for endpoint
        limit_str = RATE_LIMITS.get(endpoint, RATE_LIMITS["default"])
        limit, period = self._parse_rate_limit(limit_str)

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

# Create middleware instance
rate_limiter = RateLimiterMiddleware()

async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    # Skip rate limiting for health checks and static files
    if request.url.path in ["/health", "/", "/docs", "/redoc"]:
        return await call_next(request)

    # Check rate limit
    if not await rate_limiter.check_rate_limit(request, request.url.path):
        return JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please try again later."
            }
        )

    # Process request
    response = await call_next(request)

    # Add rate limit headers
    response.headers["X-RateLimit-Limit"] = "varies"
    response.headers["X-RateLimit-Remaining"] = "varies"

    return response

def get_token_limit(operation_type: str) -> int:
    """Get token limit for operation type"""
    return TOKEN_LIMITS.get(operation_type, TOKEN_LIMITS["max_per_request"])