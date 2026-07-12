"""
Tests for the fact-gate orchestrator: load-bearing pass ordering, the
version-1 report contract, never-raises behavior, flag-only scans, and
idempotence on a fixture containing every failure class from the
2026-07-11 real-LLM browser test.
"""
from datetime import date

from app.services.fact_gate import Correction, GateContext, GateResult, run_fact_gate

CHILDREN = [
    {"name": "Sofia Delgado", "date_of_birth": "2018-03-22"},
    {"name": "Mateo Delgado", "dob": "2020-11-05"},
]

CTX = GateContext(
    motion_kind="rfo_section",
    section_name="Case Information",
    party_name="Maria Delgado",
    other_party_name="Jacob Delgado",
    is_petitioner=True,
    case_number="24FL009812N",
    county="San Diego",
    children=CHILDREN,
    intake_values={
        "monthly_income": "3200",
        "violation_dates": "June 20, 2026",
        "incident_date": "2026-06-14",
    },
    today=date(2026, 7, 11),
)

ALL_CLASSES_TEXT = """### DECLARATION

2.1 Petitioner is **Jacob Delgado**. 2.2 Respondent is [TO BE COMPLETED].

[PETITIONER'S FULL LEGAL NAME] declares as follows:

On or about June 14, 2026, a Saturday, Petitioner and the minor children waited at the designated location for Respondent to arrive for his scheduled visitation. Respondent did not appear. Petitioner and the children waited approximately forty-five (45) minutes before returning home.

Throughout the weekend of June 20–22, 2026, Respondent's cellular telephone was turned off or otherwise unavailable. I attempted to reach Respondent by telephone on multiple occasions.

Order Respondent to pay Petitioner child support of no less than $3,200.00 per month, allocated between Sofia Delgado (age 6) and Mateo Delgado (age 4).

This request complies with San Diego Superior Court Local Rule 5.5.2. Petitioner relies on In re Marriage of Burgess (1996) 13 Cal.4th 25. The Self-Help Center is located at 1100 Union Street. Petitioner will file an Income and Expense Declaration (FL-150) with the court.

| Child | Date of Birth |
|---|---|
| Sofia Delgado | March 22, 2018 |
| Mateo Delgado | November 5, 2020 |
"""


class TestPassOrdering:
    def test_statute_parenthetical_never_reaches_date_pass(self):
        # If the date pass saw "January 1, 2024" it would flag it (unknown
        # date); authority strip must remove the whole parenthetical first.
        text = (
            "Respondent must pay guideline support. "
            "(Family Code section 4055, effective January 1, 2024.) "
            "Petitioner asks for makeup parenting time on June 14, 2026."
        )
        result = run_fact_gate(text, CTX)
        assert "January 1, 2024" not in result.text
        assert "4055" not in result.text
        assert "[TO BE COMPLETED]" not in result.text
        assert [c for c in result.corrections if c.type == "date"] == []
        assert any(c.type == "authority_removed" for c in result.corrections)
        assert "June 14, 2026" in result.text

    def test_markdown_stripped_before_party_names(self):
        # **Jacob Delgado** must not defeat the word-boundary name regex.
        result = run_fact_gate("2.1 Petitioner is **Jacob Delgado**.", CTX)
        assert result.text == "2.1 Petitioner is Maria Delgado."
        types = {c.type for c in result.corrections}
        assert {"markdown", "party_role"} <= types


class TestReportContract:
    def test_report_shape_severities_and_sections(self):
        result = run_fact_gate(ALL_CLASSES_TEXT, CTX)
        report = result.as_report()
        assert report["version"] == 1
        assert report["corrections"]
        allowed_types = {
            "markdown", "authority_removed", "placeholder_filled", "party_role",
            "amount", "date", "age", "upl_flag", "quantifier_flag",
        }
        for item in report["corrections"]:
            assert set(item) == {
                "type", "severity", "section", "original", "replacement", "message",
            }
            assert item["type"] in allowed_types
            assert item["severity"] in {"corrected", "needs_review", "info"}
            assert item["section"] == "Case Information"
            assert len(item["original"]) <= 120
            assert item["message"]

    def test_result_types(self):
        result = run_fact_gate("Plain text.", CTX)
        assert isinstance(result, GateResult)
        assert all(isinstance(c, Correction) for c in result.corrections)


class TestNeverRaises:
    def test_empty_text_empty_ctx(self):
        result = run_fact_gate("", GateContext())
        assert result.text == ""
        assert result.corrections == []

    def test_none_text(self):
        result = run_fact_gate(None, CTX)
        assert result.text == ""

    def test_weird_unicode(self):
        text = "🙂 Café ¿dónde está?    â€ fin\x00"
        result = run_fact_gate(text, CTX)
        assert isinstance(result.text, str)

    def test_garbage_context(self):
        ctx = GateContext(
            children=["junk", {"name": 5, "dob": 7}, None],
            intake_values={"a": {"b": [1, None, {"c": "June 40, 2026"}]}},
            profile_addresses=[None, 12],
        )
        result = run_fact_gate("Some text about $12 on June 20, 2026.", ctx)
        assert isinstance(result.text, str)


class TestFlagOnlyScans:
    def test_quantifier_flag_leaves_text_unchanged(self):
        text = "I attempted to reach Respondent by telephone on multiple occasions."
        result = run_fact_gate(text, CTX)
        assert result.text == text
        flags = [c for c in result.corrections if c.type == "quantifier_flag"]
        assert len(flags) == 1
        assert flags[0].replacement is None
        assert "accurate" in flags[0].message

    def test_upl_phrases_flagged_not_edited(self):
        text = (
            "You should file this motion right away, and you may wish to "
            "consult an attorney about your best option."
        )
        result = run_fact_gate(text, CTX)
        assert result.text == text
        upl = [c for c in result.corrections if c.type == "upl_flag"]
        assert len(upl) >= 2


class TestAllFailureClassesAndIdempotence:
    def test_every_failure_class_handled(self):
        result = run_fact_gate(ALL_CLASSES_TEXT, CTX)
        out = result.text
        # L1 party roles + L15 placeholder
        assert "Petitioner is Maria Delgado" in out
        assert "Maria Delgado declares as follows:" in out
        assert "[PETITIONER'S FULL LEGAL NAME]" not in out
        # L2 invented support amount
        assert "$3,200.00" not in out
        assert "[TO BE COMPLETED] per month" in out
        # L3 ages from DOBs
        assert "(age 8)" in out
        assert "(age 5)" in out
        # L4 range trimmed to the entered date
        assert "June 20–22" not in out
        assert "June 20, 2026" in out
        # L7 authority stripped
        assert "5.5.2" not in out
        assert "Burgess" not in out
        assert "Union Street" not in out
        assert "FL-150" not in out
        # L8 markdown gone; table became labeled lines
        assert "**" not in out and "###" not in out and "|" not in out
        assert "Child: Sofia Delgado; Date of Birth: March 22, 2018" in out
        # honest prose preserved verbatim
        assert (
            "On or about June 14, 2026, a Saturday, Petitioner and the minor "
            "children waited at the designated location" in out
        )
        assert "forty-five (45) minutes" in out
        # flags fired without editing
        assert "multiple occasions" in out
        assert any(c.type == "quantifier_flag" for c in result.corrections)

    def test_gate_is_idempotent(self):
        first = run_fact_gate(ALL_CLASSES_TEXT, CTX)
        second = run_fact_gate(first.text, CTX)
        assert second.text == first.text
        # second run must not correct anything again — only re-flag
        assert {c.type for c in second.corrections} <= {"quantifier_flag", "upl_flag"}
