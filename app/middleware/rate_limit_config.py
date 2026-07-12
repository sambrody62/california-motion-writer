"""
Rate limit, token, and quota configuration.
"""

# Exact request paths with enforced per-user/IP limits. Only paths listed
# here are throttled; all are static routes (no path parameters, which
# would never match this table).
RATE_LIMITS = {
    # Chat endpoints - higher limits for conversation
    "/api/v1/chat/messages": "50/hour",
    "/api/v1/chat/sessions": "20/hour",

    # LLM rewrite endpoints - moderate limits
    "/api/v1/llm/rewrite": "20/hour",
    "/api/v1/llm/rewrite-declaration": "10/hour",
    "/api/v1/llm/enhance-best-interests": "10/hour",
    "/api/v1/llm/parse-served-motion": "10/hour",

    # Full motion processing - strict limits
    "/api/v1/llm/process-motion": "5/hour",
    "/api/v1/documents/generate-pdf": "10/hour",
    "/api/v1/documents/generate-pdf-sync": "20/hour",

    # Violation processing
    "/api/v1/violations/process": "5/hour",

    # Auth - brute-force and signup-abuse protection
    "/api/v1/auth/token": "20/hour",
    "/api/v1/auth/register": "10/hour",
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


def get_token_limit(operation_type: str) -> int:
    """Get token limit for operation type"""
    return TOKEN_LIMITS.get(operation_type, TOKEN_LIMITS["max_per_request"])
