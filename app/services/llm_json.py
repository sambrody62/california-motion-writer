"""
Shared parsing of JSON objects out of LLM output.

Used by served_motion_parser, evidence_ranking_service, and text_thread_service —
LLMs frequently wrap JSON in markdown code fences.
"""
import json
import re
from typing import Any, Dict


def parse_llm_json(raw: str) -> Dict[str, Any]:
    """JSON object from LLM output, tolerating code fences; {} on failure."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, ValueError):
        return {}
