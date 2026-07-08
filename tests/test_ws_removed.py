"""The broken WebSocket chat endpoint must not exist; chat is REST-only."""
from app.main import app


def test_no_websocket_route():
    assert all(getattr(r, "path", None) != "/ws" for r in app.routes)


def test_dead_websocket_module_removed():
    import importlib.util

    assert importlib.util.find_spec("app.api.websocket") is None
