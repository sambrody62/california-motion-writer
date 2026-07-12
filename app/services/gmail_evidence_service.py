"""
Gmail Evidence Service — flag-gated (GMAIL_EVIDENCE_ENABLED).

Conditionally imports Google OAuth/API libraries so the module imports cleanly
even when the libraries are absent or the flag is off.

Privacy contract:
- Access tokens are NEVER persisted to the database.
- Only evidence/message IDs are logged (never bodies or token values).
- Emails imported as Evidence are always user_confirmed=False.
"""
import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conditional Google library imports — same pattern as llm_service.py
# ---------------------------------------------------------------------------
try:
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build
    from google.oauth2.credentials import Credentials
    _GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    _GOOGLE_LIBS_AVAILABLE = False
    logger.warning("Google OAuth/API libs not available; gmail_evidence_service will use mock mode")

_GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
_MAX_SCAN_RESULTS = 50


def _build_flow() -> "Flow":  # type: ignore[return]
    """Build a google_auth_oauthlib Flow from environment variables."""
    client_config = {
        "web": {
            "client_id": os.getenv("GMAIL_OAUTH_CLIENT_ID", ""),
            "client_secret": os.getenv("GMAIL_OAUTH_CLIENT_SECRET", ""),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.getenv("GMAIL_OAUTH_REDIRECT_URI", "")],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=_GMAIL_SCOPES,
        redirect_uri=os.getenv("GMAIL_OAUTH_REDIRECT_URI", ""),
    )


def get_auth_url() -> str:
    """Return the Google OAuth consent URL for gmail.readonly scope."""
    flow = _build_flow()
    auth_url, _state = flow.authorization_url(
        access_type="online",
        include_granted_scopes="true",
    )
    return auth_url


def exchange_code(code: str) -> str:
    """Exchange an authorization code for an access token.

    Returns the access token string ONLY — never stored at rest.
    """
    flow = _build_flow()
    flow.fetch_token(code=code)
    token = flow.credentials.token
    logger.info("Gmail OAuth code exchanged successfully (token not logged)")
    return token


def scan_emails(
    access_token: str,
    other_party_name: Optional[str],
    other_party_email: Optional[str],
) -> List[Dict]:
    """Query Gmail for messages from/to the other party.

    Returns candidates as [{message_id, from, date, subject, snippet}].
    Full bodies are NOT fetched — this is the minimization step.
    Capped at _MAX_SCAN_RESULTS results.
    """
    if not _GOOGLE_LIBS_AVAILABLE:
        return []

    creds = Credentials(token=access_token)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    # Build query — search by email address or name
    query_parts = []
    if other_party_email:
        query_parts.append(f"(from:{other_party_email} OR to:{other_party_email})")
    if other_party_name and not other_party_email:
        query_parts.append(f'"{other_party_name}"')
    query = " ".join(query_parts) if query_parts else ""

    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=_MAX_SCAN_RESULTS)
        .execute()
    )
    messages = result.get("messages", [])

    candidates = []
    for msg in messages:
        msg_id = msg["id"]
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="metadata",
                 metadataHeaders=["From", "Date", "Subject"])
            .execute()
        )
        headers = {h["name"]: h["value"] for h in detail.get("payload", {}).get("headers", [])}
        raw_date = headers.get("Date", "")
        parsed_date = _parse_rfc2822_date(raw_date)
        candidates.append(
            {
                "message_id": msg_id,
                "from": headers.get("From", ""),
                "date": parsed_date,
                "subject": headers.get("Subject", ""),
                "snippet": detail.get("snippet", "")[:300],
            }
        )
        logger.info("Scanned message id=%s", msg_id)

    return candidates


def fetch_bodies(access_token: str, message_ids: List[str]) -> Dict[str, Dict]:
    """Fetch full body text for a user-selected list of message IDs.

    Returns {message_id: {date, from, subject, body_text}}.
    Only called for IDs the user explicitly selected — never auto-fetched.
    Body content is NOT logged (PII minimisation).
    """
    if not _GOOGLE_LIBS_AVAILABLE:
        return {}

    creds = Credentials(token=access_token)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    result = {}
    for msg_id in message_ids:
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        headers = {
            h["name"]: h["value"]
            for h in detail.get("payload", {}).get("headers", [])
        }
        raw_date = headers.get("Date", "")
        parsed_date = _parse_rfc2822_date(raw_date)
        body_text = _extract_body(detail)
        result[msg_id] = {
            "date": parsed_date,
            "from": headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "body_text": body_text,
        }
        logger.info("Fetched body for message id=%s", msg_id)
        # Intentionally NOT logging body_text — PII minimisation

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_body(message_detail: dict) -> str:
    """Extract plain-text body from a Gmail message detail dict."""
    import base64

    payload = message_detail.get("payload", {})
    parts = payload.get("parts", [])

    if not parts:
        # Simple message — body directly in payload
        data = payload.get("body", {}).get("data", "")
        if data:
            return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
        return ""

    for part in parts:
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")

    return ""


def _parse_rfc2822_date(raw: str) -> str:
    """Parse an RFC-2822 date header to YYYY-MM-DD, or return empty string."""
    if not raw:
        return ""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(raw)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return ""
