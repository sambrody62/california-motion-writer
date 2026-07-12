"""
build_fact_anchor injects authoritative party/children/fact lines into
section prompts, and _build_rfo_prompt must carry the anchor while dropping
the instruction that invited Family Code citations (finding L7 hardening —
the post-generation fact gate remains the enforcement).
"""
from datetime import date

from app.services.fact_gate.prompt_guard import build_fact_anchor
from app.services.claude_llm_service import UPL_GUARDRAILS
from app.services.llm_service import LLMService

CONTEXT = {
    "party_role": "Petitioner",
    "party_name": "Maria Delgado",
    "other_party_name": "Jacob Delgado",
    "county": "San Diego",
    "case_number": "24FL009812N",
    "children_info": [
        {"name": "Sofia Delgado", "birthdate": "2018-03-22"},
        {"name": "Mateo Delgado", "birthdate": "2020-11-05"},
    ],
}


class TestBuildFactAnchor:
    def test_party_lines_for_petitioner(self):
        anchor = build_fact_anchor(CONTEXT)
        assert "Petitioner is Maria Delgado." in anchor
        assert "Respondent is Jacob Delgado." in anchor
        assert "drafting for the Petitioner" in anchor
        assert "declarant is Maria Delgado" in anchor

    def test_party_lines_for_respondent(self):
        anchor = build_fact_anchor({**CONTEXT, "party_role": "Respondent"})
        assert "Petitioner is Jacob Delgado." in anchor
        assert "Respondent is Maria Delgado." in anchor
        assert "drafting for the Respondent" in anchor
        assert "declarant is Maria Delgado" in anchor

    def test_children_ages_computed_from_dobs(self):
        anchor = build_fact_anchor(CONTEXT, today=date(2026, 7, 11))
        assert "Sofia Delgado (age 8)" in anchor
        assert "Mateo Delgado (age 5)" in anchor

    def test_child_without_dob_listed_without_age(self):
        context = {**CONTEXT, "children_info": [{"name": "Sofia Delgado"}]}
        anchor = build_fact_anchor(context)
        assert "Sofia Delgado" in anchor
        assert "(age" not in anchor

    def test_fact_and_plain_text_rules_always_present(self):
        anchor = build_fact_anchor({})
        assert "[TO BE COMPLETED]" in anchor
        assert "plain text only" in anchor
        assert "no markdown" in anchor

    def test_no_party_names_no_party_line(self):
        assert "Petitioner is" not in build_fact_anchor({})


class TestRfoPromptHardened:
    def test_prompt_contains_anchor(self):
        prompt = LLMService()._build_rfo_prompt("facts", "My input", CONTEXT)
        assert "Petitioner is Maria Delgado." in prompt
        assert "plain text only" in prompt

    def test_prompt_drops_code_section_instruction_for_no_authority_rule(self):
        prompt = LLMService()._build_rfo_prompt("facts", "My input", CONTEXT)
        assert "Family Code sections where appropriate" not in prompt
        assert "Do NOT cite any statute" in prompt


class TestUplGuardrailsMirror:
    def test_guardrails_include_no_authority_and_plain_text(self):
        assert "Do NOT cite any statute" in UPL_GUARDRAILS
        assert "plain text only" in UPL_GUARDRAILS
