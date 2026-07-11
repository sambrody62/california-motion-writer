"""
Tests for the fact-gate legal-authority stripper.

Fixtures are the fabricated citations from the 2026-07-11 real-LLM browser
test (finding L7): "San Diego Superior Court Local Rule 5.5.2"/"5.5.3",
"In re Marriage of Burgess", "Family Code section 3027.1", invented
courthouse street addresses, and unrequested FL-150 instructions.
"""
from app.services.fact_gate.authority_strip import address_tokens_from, strip_authority
from app.services.fact_gate.types import GateContext

CTX = GateContext()


def _needs_review(corrections):
    return [c for c in corrections if c.severity == "needs_review"]


class TestCitations:
    def test_local_rule_with_court_prefix_removed(self):
        text = (
            "This complies with San Diego Superior Court Local Rule 5.5.2. "
            "The children reside with Petitioner in San Diego County."
        )
        out, corrections = strip_authority(text, set(), CTX)
        assert "5.5.2" not in out
        assert "Local Rule" not in out
        assert "The children reside with Petitioner in San Diego County." in out
        assert any(c.type == "authority_removed" for c in _needs_review(corrections))
        assert any("5.5.2" in c.original for c in corrections)

    def test_bare_local_rule_removed_sentence_kept(self):
        text = (
            "Filing must conform to Local Rule 5.5.3 and include a declaration "
            "signed under penalty of perjury."
        )
        out, _ = strip_authority(text, set(), CTX)
        assert "5.5.3" not in out
        assert "declaration signed under penalty of perjury" in out

    def test_case_citation_removed(self):
        text = (
            "Petitioner relies on In re Marriage of Burgess (1996) 13 Cal.4th 25. "
            "Respondent missed the exchange."
        )
        out, corrections = strip_authority(text, set(), CTX)
        assert "Burgess" not in out
        assert "Cal.4th" not in out
        assert "Respondent missed the exchange." in out
        assert any("Burgess" in c.original for c in corrections)

    def test_statute_with_connector_removed(self):
        text = "Issue monetary sanctions against Respondent pursuant to Family Code section 3027.1."
        out, corrections = strip_authority(text, set(), CTX)
        assert "3027.1" not in out
        assert "Family Code" not in out
        assert "pursuant to" not in out
        assert out.strip() == "Issue monetary sanctions against Respondent."
        assert any("3027.1" in c.original for c in corrections)

    def test_statute_in_parenthetical_removes_whole_parenthetical(self):
        text = "Respondent must pay guideline support. (Fam. Code § 4055.) The guideline applies here."
        out, _ = strip_authority(text, set(), CTX)
        assert "4055" not in out
        assert "(" not in out
        assert "Respondent must pay guideline support." in out
        assert "The guideline applies here." in out

    def test_rules_of_court_removed(self):
        text = "Service must follow California Rules of Court rule 5.92 in every case filed."
        out, _ = strip_authority(text, set(), CTX)
        assert "5.92" not in out
        assert "Rules of Court" not in out

    def test_clean_text_unchanged_no_corrections(self):
        text = "On June 14, 2026, Respondent did not appear at the exchange."
        out, corrections = strip_authority(text, set(), CTX)
        assert out == text
        assert corrections == []


class TestAddresses:
    def test_unverified_address_removes_whole_sentence(self):
        text = (
            "The Self-Help Center is located at 1100 Union Street. "
            "Petitioner requests makeup parenting time."
        )
        out, corrections = strip_authority(text, set(), CTX)
        assert "1100 Union Street" not in out
        assert "Self-Help Center" not in out
        assert "Petitioner requests makeup parenting time." in out
        assert any("Union" in c.original for c in _needs_review(corrections))

    def test_user_entered_street_survives_with_number(self):
        tokens = address_tokens_from(
            "He never showed at the McDonald's lot on Van Buren Blvd on May 8."
        )
        text = "Respondent failed to appear at 4620 Van Buren Blvd as agreed by the parties."
        out, corrections = strip_authority(text, tokens, CTX)
        assert out == text
        assert corrections == []

    def test_user_entered_street_survives_without_number(self):
        tokens = address_tokens_from("the McDonald's lot on Van Buren Blvd")
        text = "The exchange point is the McDonald's lot on Van Buren Blvd."
        out, corrections = strip_authority(text, tokens, CTX)
        assert out == text
        assert corrections == []


class TestSupportDocumentSentences:
    def test_fl150_sentence_removed_when_no_support_requested(self):
        ctx = GateContext(intake_values={"visitation_details": "missed pickups in June"})
        text = (
            "Petitioner will file an Income and Expense Declaration (FL-150) with this motion. "
            "Respondent missed three exchanges."
        )
        out, corrections = strip_authority(text, set(), ctx)
        assert "FL-150" not in out
        assert "Income and Expense" not in out
        assert "Respondent missed three exchanges." in out
        assert any("FL-150" in c.original for c in _needs_review(corrections))

    def test_fl150_sentence_kept_when_support_requested(self):
        ctx = GateContext(intake_values={"child_support_amount": "500"})
        text = "Petitioner will file an Income and Expense Declaration (FL-150) with this motion."
        out, corrections = strip_authority(text, set(), ctx)
        assert "FL-150" in out
        assert corrections == []

    def test_earnings_assignment_sentence_removed_when_no_support_requested(self):
        ctx = GateContext(intake_values={"custody_details": "week on week off"})
        text = (
            "The court will issue an earnings assignment order to collect payments. "
            "Petitioner asks the court to enforce the existing order."
        )
        out, _ = strip_authority(text, set(), ctx)
        assert "earnings assignment" not in out
        assert "Petitioner asks the court to enforce the existing order." in out
