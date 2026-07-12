"""
PII must not reach server logs: no chat message content, no SQL parameter
echo unless explicitly enabled.
"""
import logging

import pytest
from httpx import AsyncClient

from app.core.database import _sql_echo_enabled

pytestmark = pytest.mark.asyncio


async def test_chat_message_content_not_logged(
    client: AsyncClient, auth_headers: dict, caplog, monkeypatch
):
    from app.api.v1 import chat as chat_api

    class _StubMemory:
        entity_references = {"my ex": "John Doe"}

    class _StubMemoryService:
        async def update_memory(self, session_id, messages, profile):
            return _StubMemory()

        def resolve_references(self, message, refs):
            return message

        def get_memory_context(self, session_id):
            return ""

    monkeypatch.setattr(
        chat_api.chat_service, "memory_service", _StubMemoryService(), raising=False
    )

    resp = await client.post(
        "/api/v1/chat/sessions",
        json={"initial_message": "hello"},
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    session_id = resp.json()["session_id"]

    # INFO is the operational log level (main.py basicConfig); DB-driver
    # DEBUG records below it never reach production logs
    secret = "my ex threatened me, SSN 123-45-6789"
    with caplog.at_level(logging.INFO):
        resp = await client.post(
            "/api/v1/chat/messages",
            json={"session_id": session_id, "content": secret},
            headers=auth_headers,
        )

    assert resp.status_code == 200, resp.text
    assert "123-45-6789" not in caplog.text


def test_sql_echo_off_by_default_even_in_development(monkeypatch):
    monkeypatch.delenv("SQL_ECHO", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "development")
    assert _sql_echo_enabled() is False


def test_sql_echo_requires_explicit_opt_in(monkeypatch):
    monkeypatch.setenv("SQL_ECHO", "true")
    assert _sql_echo_enabled() is True
    monkeypatch.setenv("SQL_ECHO", "false")
    assert _sql_echo_enabled() is False
