"""
Tests for OCR service (env-gated Cloud Vision transcription suggestions).
"""
import os
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# ocr_enabled()
# ---------------------------------------------------------------------------

def test_ocr_enabled_false_when_flag_off(monkeypatch):
    """ocr_enabled() returns False when OCR_ENABLED is unset or not 'true'."""
    monkeypatch.delenv("OCR_ENABLED", raising=False)
    # Re-import so the module-level flag re-evaluates via the function call
    from app.services import ocr_service
    assert ocr_service.ocr_enabled() is False


def test_ocr_enabled_false_when_flag_false(monkeypatch):
    monkeypatch.setenv("OCR_ENABLED", "false")
    from app.services import ocr_service
    assert ocr_service.ocr_enabled() is False


def test_ocr_enabled_true_when_flag_on_and_lib_available(monkeypatch):
    """ocr_enabled() returns True when flag is 'true' and vision lib is present."""
    monkeypatch.setenv("OCR_ENABLED", "true")

    # Simulate the vision lib being available by patching the module-level sentinel
    from app.services import ocr_service
    with patch.object(ocr_service, "_VISION_AVAILABLE", True):
        assert ocr_service.ocr_enabled() is True


def test_ocr_enabled_false_when_flag_on_but_lib_missing(monkeypatch):
    """ocr_enabled() returns False even when flag is 'true' if lib not installed."""
    monkeypatch.setenv("OCR_ENABLED", "true")
    from app.services import ocr_service
    with patch.object(ocr_service, "_VISION_AVAILABLE", False):
        assert ocr_service.ocr_enabled() is False


# ---------------------------------------------------------------------------
# extract_text()
# ---------------------------------------------------------------------------

def _make_vision_response(text: str):
    """Build a minimal mock matching google.cloud.vision AnnotateImageResponse."""
    response = MagicMock()
    response.full_text_annotation.text = text
    return response


def test_extract_text_returns_text_from_vision(monkeypatch):
    """extract_text() returns text extracted by the Cloud Vision client."""
    from app.services import ocr_service

    mock_client = MagicMock()
    mock_client.document_text_detection.return_value = _make_vision_response("Hello World")

    with patch.object(ocr_service, "_VISION_AVAILABLE", True):
        with patch.object(ocr_service, "_build_vision_client", return_value=mock_client):
            result = ocr_service.extract_text(b"\x89PNG")

    assert result == "Hello World"
    mock_client.document_text_detection.assert_called_once()


def test_extract_text_returns_empty_string_on_client_error(monkeypatch):
    """extract_text() returns '' and never raises when Cloud Vision throws."""
    from app.services import ocr_service

    mock_client = MagicMock()
    mock_client.document_text_detection.side_effect = Exception("API unavailable")

    with patch.object(ocr_service, "_VISION_AVAILABLE", True):
        with patch.object(ocr_service, "_build_vision_client", return_value=mock_client):
            result = ocr_service.extract_text(b"\x89PNG")

    assert result == ""


def test_extract_text_returns_empty_when_vision_unavailable():
    """extract_text() returns '' immediately when the vision lib is not installed."""
    from app.services import ocr_service

    with patch.object(ocr_service, "_VISION_AVAILABLE", False):
        result = ocr_service.extract_text(b"\x89PNG")

    assert result == ""


def test_extract_text_returns_empty_on_empty_annotation():
    """extract_text() returns '' when full_text_annotation.text is empty."""
    from app.services import ocr_service

    mock_client = MagicMock()
    mock_client.document_text_detection.return_value = _make_vision_response("")

    with patch.object(ocr_service, "_VISION_AVAILABLE", True):
        with patch.object(ocr_service, "_build_vision_client", return_value=mock_client):
            result = ocr_service.extract_text(b"\x89PNG")

    assert result == ""
