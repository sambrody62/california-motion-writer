"""
/llm/process-motion must run the fact gate on every rewritten section before
saving, store the corrections report on motions.fact_check, and return the
corrections (real-LLM findings L1-L4, L7, L8). Fixtures are the verbatim
fabricated prose from tasks/real-llm-browser-test-results.md Flow 1.
"""
from datetime import date
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

# Patch the instance the endpoint module holds: an earlier suite file reloads
# app.services.llm_service, so the module attribute and the endpoint's captured
# singleton can be different objects by the time this file runs.
from app.api.v1.endpoints import llm as llm_endpoint

pytestmark = pytest.mark.asyncio

PROFILE = {
    "case_number": "24FL009812N",
    "county": "San Diego",
    "is_petitioner": True,
    "party_name": "Maria Delgado",
    "other_party_name": "Jacob Delgado",
    "children_info": [
        {"name": "Sofia Delgado", "birthdate": "2018-03-22"},
        {"name": "Mateo Delgado", "birthdate": "2020-11-05"},
    ],
}

FABRICATED_CASE_INFO = (
    "2.1 Petitioner is **Jacob Delgado**. 2.2 Respondent is [TO BE COMPLETED] "
    "as stated in the supporting Declaration of Jacob Delgado, filed "
    "concurrently herewith. Sofia Delgado, age 6, and Mateo Delgado, age 4, "
    "reside with Petitioner. Petitioner requests a hearing pursuant to "
    "San Diego Superior Court Local Rule 5.5.2."
)
FABRICATED_SUPPORT = (
    "Order Respondent to pay Petitioner child support of no less than "
    "$3,200.00 per month, allocated between Sofia Delgado and Mateo Delgado."
)
CLEAN_TEXT = (
    "Petitioner respectfully requests that the court modify the current "
    "custody schedule to reflect the parties' work schedules."
)


def _age(dob: date) -> int:
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _llm_result(sections):
    return {
        "motion_type": "RFO",
        "sections": [
            {
                "step_number": number,
                "section": name,
                "original_answers": {},
                "rewritten_text": text,
                "success": True,
                "error": None,
                "tokens_used": 42,
            }
            for number, name, text in sections
        ],
        "total_tokens": 84,
        "model": "mock-llm",
        "success": True,
    }


async def _create_motion_with_drafts(
    client: AsyncClient, headers: dict, drafts: list
) -> str:
    resp = await client.post("/api/v1/profiles/", json=PROFILE, headers=headers)
    assert resp.status_code == 201, resp.text
    resp = await client.post(
        "/api/v1/motions/",
        json={"motion_type": "RFO", "title": "Custody RFO"},
        headers=headers,
    )
    assert resp.status_code == 201, resp.text
    motion_id = resp.json()["id"]
    for number, name, question_data in drafts:
        resp = await client.post(
            f"/api/v1/motions/{motion_id}/drafts",
            json={
                "step_number": number,
                "step_name": name,
                "question_data": question_data,
            },
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
    return motion_id


async def _get_detail(client: AsyncClient, headers: dict, motion_id: str) -> dict:
    resp = await client.get(f"/api/v1/motions/{motion_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_fabricated_sections_are_gated_before_save(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    motion_id = await _create_motion_with_drafts(
        client,
        auth_headers,
        [
            (1, "case_information", {"case_summary": "Please fix the schedule."}),
            (2, "relief_requested", {"monthly_income": "3200"}),
        ],
    )
    monkeypatch.setattr(
        llm_endpoint.llm_service,
        "process_complete_motion",
        AsyncMock(
            return_value=_llm_result(
                [
                    (1, "case_information", FABRICATED_CASE_INFO),
                    (2, "relief_requested", FABRICATED_SUPPORT),
                ]
            )
        ),
    )

    resp = await client.post(
        "/api/v1/llm/process-motion", json={"motion_id": motion_id}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["success"] is True
    assert body["sections_processed"] == 2

    # The response carries the corrections the gate made
    corrections = body["corrections"]
    types = {c["type"] for c in corrections}
    assert {"markdown", "authority_removed", "party_role", "amount", "age"} <= types

    detail = await _get_detail(client, auth_headers, motion_id)
    outputs = {d["step_number"]: d["llm_output"] for d in detail["drafts"]}

    # L1 party-role swap corrected: Maria is the petitioner and the declarant
    case_info = outputs[1]
    assert "Petitioner is Maria Delgado" in case_info
    assert "Declaration of Maria Delgado" in case_info
    assert "Jacob Delgado" not in case_info
    # L8 markdown stripped
    assert "**" not in case_info
    # L7 invented local rule stripped
    assert "Local Rule 5.5.2" not in case_info
    # L3 ages corrected from the profile DOBs
    assert f"age {_age(date(2018, 3, 22))}" in case_info
    assert "age 6" not in case_info
    assert f"age {_age(date(2020, 11, 5))}" in case_info
    assert "age 4" not in case_info

    # L2 income-sourced support amount blocked
    support = outputs[2]
    assert "$3,200.00" not in support
    assert "[TO BE COMPLETED]" in support

    # Report persisted on the motion and served by GET /motions/{id}
    fact_check = detail["fact_check"]
    assert fact_check["version"] == 1
    assert fact_check["corrections"] == corrections
    assert any(c["section"] == "case_information" for c in corrections)


async def test_clean_text_is_untouched_with_empty_report(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    motion_id = await _create_motion_with_drafts(
        client,
        auth_headers,
        [(1, "facts", {"facts": "The schedule needs adjusting."})],
    )
    monkeypatch.setattr(
        llm_endpoint.llm_service,
        "process_complete_motion",
        AsyncMock(return_value=_llm_result([(1, "facts", CLEAN_TEXT)])),
    )

    resp = await client.post(
        "/api/v1/llm/process-motion", json={"motion_id": motion_id}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["corrections"] == []

    detail = await _get_detail(client, auth_headers, motion_id)
    assert detail["drafts"][0]["llm_output"] == CLEAN_TEXT
    assert detail["fact_check"] == {"version": 1, "corrections": []}


# Verbatim per-step question_data shapes from the 2026-07-11 live run
# (browser-test3.db): the wizard saves each step with the raw form store, so
# later steps re-register earlier fields as blank/all-false (871cafa family).
LIVE_RUN_DRAFTS = [
    (2, "order_types", {"order_types": {"custody": True, "visitation": True, "support": False}}),
    (3, "children", {"order_types": {"custody": False, "visitation": False, "support": False}}),
    (4, "income", {"has_children": None, "current_custody": "", "monthly_income": "3200"}),
    (5, "facts", {
        "monthly_income": "",
        "facts_summary": "On June 14, 2026 Respondent kept the children overnight.",
    }),
    (6, "review", {"facts_summary": ""}),
]

REAL_FACTS_TEXT = (
    "Petitioner's monthly income is $3,200. On June 14, 2026, Respondent "
    "kept the children overnight without notice."
)


async def test_blank_later_drafts_do_not_poison_the_intake_merge(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    """Blanked re-registrations must not make the gate false-positive on real facts."""
    motion_id = await _create_motion_with_drafts(client, auth_headers, LIVE_RUN_DRAFTS)
    monkeypatch.setattr(
        llm_endpoint.llm_service,
        "process_complete_motion",
        AsyncMock(return_value=_llm_result([(5, "facts", REAL_FACTS_TEXT)])),
    )

    resp = await client.post(
        "/api/v1/llm/process-motion", json={"motion_id": motion_id}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text

    detail = await _get_detail(client, auth_headers, motion_id)
    outputs = {d["step_number"]: d["llm_output"] for d in detail["drafts"]}
    facts_output = outputs[5]
    # The user genuinely entered these on steps 4/5 — the gate must keep them
    assert "$3,200" in facts_output
    assert "June 14, 2026" in facts_output
    assert "[TO BE COMPLETED]" not in facts_output


SEMANTIC_FLAG = {
    "type": "semantic_flag",
    "severity": "needs_review",
    "section": "reviewer",
    "original": "the parties' work schedules",
    "replacement": None,
    "message": (
        "Our automated reviewer flagged: The intake data does not mention work "
        "schedules. — verify \"the parties' work schedules\" against your "
        "records before filing."
    ),
}


async def test_semantic_flags_append_to_report_and_response(
    client: AsyncClient, auth_headers: dict, monkeypatch
):
    motion_id = await _create_motion_with_drafts(
        client,
        auth_headers,
        [
            (1, "facts", {"facts": "The schedule needs adjusting."}),
            (2, "relief_requested", {"relief": "Please adjust the schedule."}),
        ],
    )
    monkeypatch.setattr(
        llm_endpoint.llm_service,
        "process_complete_motion",
        AsyncMock(
            return_value=_llm_result(
                [(1, "facts", CLEAN_TEXT), (2, "relief_requested", CLEAN_TEXT)]
            )
        ),
    )
    check_text = AsyncMock(return_value=[dict(SEMANTIC_FLAG)])
    monkeypatch.setattr(llm_endpoint.semantic_check_service, "check_text", check_text)

    resp = await client.post(
        "/api/v1/llm/process-motion", json={"motion_id": motion_id}, headers=auth_headers
    )
    assert resp.status_code == 200, resp.text
    # Clean text produces no gate corrections; the reviewer flag is appended
    assert resp.json()["corrections"] == [SEMANTIC_FLAG]

    # ONE reviewer call per motion, over the concatenated gated sections
    check_text.assert_awaited_once()
    merged_text = check_text.await_args.args[0]
    assert merged_text.count(CLEAN_TEXT) == 2

    detail = await _get_detail(client, auth_headers, motion_id)
    assert detail["fact_check"] == {"version": 1, "corrections": [SEMANTIC_FLAG]}
