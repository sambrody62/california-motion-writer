"""
Tests for the fact-gate placeholder fill and party-role correction.

Fixtures from the 2026-07-11 real-LLM browser test (findings L1, L15):
the RFO rewrite named the opposing party as Petitioner/declarant, the
FL-320 response was titled "REQUEST FOR ORDER" with "Jacob Delgado
(Respondent)" as Moving Party, and declarations printed
"[PETITIONER'S FULL LEGAL NAME]" while the profile has the name.
"""
from app.services.fact_gate.party_check import check_party_roles, fill_placeholders
from app.services.fact_gate.types import GateContext

RFO_CTX = GateContext(
    motion_kind="rfo_section",
    party_name="Maria Delgado",
    other_party_name="Jacob Delgado",
    is_petitioner=True,
)
# The responding user (Maria) answers Jacob's request for order.
RESPONSE_CTX = GateContext(
    motion_kind="response_section",
    party_name="Maria Delgado",
    other_party_name="Jacob Delgado",
    is_petitioner=False,
)


class TestDefinitionalRoleSwaps:
    def test_numbered_petitioner_definition_corrected(self):
        out, corrections = check_party_roles("2.1 Petitioner is Jacob Delgado.", RFO_CTX)
        assert out == "2.1 Petitioner is Maria Delgado."
        assert corrections[0].type == "party_role"
        assert corrections[0].severity == "corrected"

    def test_role_colon_name_corrected(self):
        out, _ = check_party_roles("Respondent: Maria Delgado", RFO_CTX)
        assert out == "Respondent: Jacob Delgado"

    def test_declaration_of_wrong_declarant_corrected(self):
        text = "the supporting Declaration of Jacob Delgado, filed concurrently herewith."
        out, corrections = check_party_roles(text, RFO_CTX)
        assert "Declaration of Maria Delgado" in out
        assert "Jacob" not in out
        assert len(corrections) == 1

    def test_unknown_name_untouched(self):
        text = "Petitioner is Alex Rivera."
        out, corrections = check_party_roles(text, RFO_CTX)
        assert out == text
        assert corrections == []


class TestAppositives:
    def test_wrong_role_label_corrected(self):
        # In the response context Jacob filed the RFO, so Jacob is the Petitioner.
        out, corrections = check_party_roles(
            "Moving Party: Jacob Delgado (Respondent)", RESPONSE_CTX
        )
        assert out == "Moving Party: Jacob Delgado (Petitioner)"
        assert len(corrections) == 1

    def test_comma_the_role_corrected(self):
        out, _ = check_party_roles(
            "Maria Delgado, the Petitioner, did not receive notice.", RESPONSE_CTX
        )
        assert out == "Maria Delgado, the Respondent, did not receive notice."

    def test_moving_party_label_correct_in_response_section(self):
        # Jacob IS the moving party for a response section — no change.
        text = "Jacob Delgado (Moving Party) filed the request."
        out, corrections = check_party_roles(text, RESPONSE_CTX)
        assert out == text
        assert corrections == []


class TestResponseTitle:
    def test_standalone_rfo_title_corrected_in_response(self):
        text = "REQUEST FOR ORDER\n\n1. I do not consent to the orders requested."
        out, corrections = check_party_roles(text, RESPONSE_CTX)
        assert out.startswith("RESPONSIVE DECLARATION TO REQUEST FOR ORDER\n")
        assert len(corrections) == 1

    def test_title_untouched_in_rfo_section(self):
        text = "REQUEST FOR ORDER\n\n1. Petitioner requests custody orders."
        out, corrections = check_party_roles(text, RFO_CTX)
        assert out == text
        assert corrections == []

    def test_inline_mention_not_retitled(self):
        text = "I received the Request for Order on July 10, 2026."
        out, corrections = check_party_roles(text, RESPONSE_CTX)
        assert out == text
        assert corrections == []


class TestNoOpOnCorrectText:
    def test_correct_text_is_byte_identical(self):
        text = (
            "2.1 Petitioner is Maria Delgado. 2.2 Respondent is Jacob Delgado.\n"
            "The supporting Declaration of Maria Delgado is filed concurrently.\n"
            "Jacob Delgado (Respondent) did not appear."
        )
        out, corrections = check_party_roles(text, RFO_CTX)
        assert out == text
        assert corrections == []

    def test_empty_names_never_alter_text(self):
        text = "Petitioner is Jacob Delgado."
        out, corrections = check_party_roles(text, GateContext())
        assert out == text
        assert corrections == []


class TestFillPlaceholders:
    def test_petitioner_full_legal_name_filled(self):
        out, corrections = fill_placeholders(
            "I, [PETITIONER'S FULL LEGAL NAME], declare as follows:", RFO_CTX
        )
        assert out == "I, Maria Delgado, declare as follows:"
        assert corrections[0].type == "placeholder_filled"
        assert corrections[0].severity == "info"

    def test_respondent_name_filled(self):
        out, _ = fill_placeholders("[RESPONDENT NAME] failed to appear.", RFO_CTX)
        assert out == "Jacob Delgado failed to appear."

    def test_declarant_and_your_name_filled(self):
        out, _ = fill_placeholders(
            "[DECLARANT'S NAME] and [YOUR FULL LEGAL NAME]", RESPONSE_CTX
        )
        assert out == "Maria Delgado and Maria Delgado"

    def test_non_name_placeholders_left_alone(self):
        text = "Hearing set for [HEARING DATE]; amount [TO BE COMPLETED]."
        out, corrections = fill_placeholders(text, RFO_CTX)
        assert out == text
        assert corrections == []

    def test_unknown_profile_name_leaves_placeholder(self):
        text = "[PETITIONER'S FULL LEGAL NAME] declares:"
        out, corrections = fill_placeholders(text, GateContext())
        assert out == text
        assert corrections == []
