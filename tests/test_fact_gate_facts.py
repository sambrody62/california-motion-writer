"""
Tests for the fact-gate allowed-facts builder and the amount/date/age
verification passes.

Fixtures are the fabrications from the 2026-07-11 real-LLM browser test:
the $3,200 income-turned-support demand (L2), children's ages 6/4 vs DOB
truth 8/5 (L3), and the un-entered "June 22" range extension (L4).
"""
from datetime import date
from decimal import Decimal

from app.services.fact_gate.allowed_facts import build_allowed_facts
from app.services.fact_gate.fact_check import check_ages, check_amounts, check_dates
from app.services.fact_gate.party_check import fill_placeholders
from app.services.fact_gate.types import GateContext

TODAY = date(2026, 7, 11)
CHILDREN = [
    {"name": "Sofia Delgado", "date_of_birth": "2018-03-22"},
    {"name": "Mateo Delgado", "dob": "2020-11-05"},
]


def _ctx(**overrides):
    defaults = dict(
        party_name="Maria Delgado",
        other_party_name="Jacob Delgado",
        today=TODAY,
    )
    defaults.update(overrides)
    return GateContext(**defaults)


class TestAllowedFactsAmounts:
    def test_bare_numeric_from_money_key(self):
        facts = build_allowed_facts(_ctx(intake_values={"monthly_income": "3200"}))
        assert facts.amounts[Decimal("3200")] == {"monthly_income"}
        # normalization: $3,200.00 is the same Decimal
        assert Decimal("3200.00") in facts.amounts

    def test_dollar_strings_inside_text_any_key(self):
        facts = build_allowed_facts(
            _ctx(intake_values={"story": "I paid $45.50 for gas and $1,200 in rent."})
        )
        assert facts.amounts[Decimal("45.50")] == {"story"}
        assert facts.amounts[Decimal("1200")] == {"story"}

    def test_bare_numeric_without_money_key_ignored(self):
        facts = build_allowed_facts(_ctx(intake_values={"case_notes": "3200"}))
        assert Decimal("3200") not in facts.amounts

    def test_numeric_types_from_money_key(self):
        facts = build_allowed_facts(_ctx(intake_values={"support_amount": 500}))
        assert facts.amounts[Decimal("500")] == {"support_amount"}


class TestAllowedFactsDates:
    def test_scalar_formats_and_text_scan(self):
        facts = build_allowed_facts(_ctx(intake_values={
            "hearing_date": "2026-06-14",
            "story": "He missed June 20, 2026 and 6/21/2026; we agreed on June 14.",
        }))
        assert (2026, 6, 14) in facts.dates
        assert (2026, 6, 20) in facts.dates
        assert (2026, 6, 21) in facts.dates
        assert (6, 14) in facts.month_days

    def test_yearless_not_added_for_full_dates(self):
        facts = build_allowed_facts(_ctx(intake_values={"d": "June 20, 2026"}))
        assert (2026, 6, 20) in facts.dates
        assert (6, 20) not in facts.month_days

    def test_children_dobs_included(self):
        facts = build_allowed_facts(_ctx(children=CHILDREN))
        assert (2018, 3, 22) in facts.dates
        assert (2020, 11, 5) in facts.dates
        assert (3, 22) in facts.month_days  # DOBs allowed year-less too


class TestAllowedFactsAges:
    def test_ages_computed_from_dobs_as_of_today(self):
        facts = build_allowed_facts(_ctx(children=CHILDREN))
        assert facts.ages == {"sofia": 8, "mateo": 5}

    def test_malformed_children_do_not_raise(self):
        children = [{}, {"name": "X"}, {"name": "", "dob": "bad"}, "junk", None]
        facts = build_allowed_facts(_ctx(children=children))
        assert facts.ages == {}


class TestAllowedFactsAddressTokens:
    def test_tokens_from_profile_and_intake_text(self):
        facts = build_allowed_facts(_ctx(
            profile_addresses=["4620 Mission Ave, San Diego, CA"],
            intake_values={"description": "the McDonald's lot on Van Buren Blvd"},
        ))
        assert "mission" in facts.address_tokens
        assert {"van", "buren"} <= facts.address_tokens
        assert "ave" not in facts.address_tokens

    def test_empty_context_builds_empty_facts(self):
        facts = build_allowed_facts(GateContext())
        assert facts.amounts == {}
        assert facts.dates == set()
        assert facts.ages == {}
        assert facts.address_tokens == set()


class TestCheckAmounts:
    def test_income_amount_in_support_sentence_blocked(self):
        # The real L2 failure: $3,200 was the user's own monthly income.
        facts = build_allowed_facts(_ctx(intake_values={"monthly_income": "3200"}))
        text = (
            "Order Respondent to pay Petitioner child support of no less than "
            "$3,200.00 per month, allocated between Sofia Delgado and Mateo Delgado."
        )
        out, corrections = check_amounts(text, facts)
        assert "$3,200.00" not in out
        assert "[TO BE COMPLETED] per month" in out
        assert corrections[0].type == "amount"
        assert corrections[0].severity == "needs_review"
        assert "income" in corrections[0].message

    def test_support_sourced_amount_in_support_sentence_preserved(self):
        facts = build_allowed_facts(_ctx(intake_values={"spousal_support_amount": "500"}))
        text = "Petitioner requests spousal support of $500 per month."
        out, corrections = check_amounts(text, facts)
        assert out == text
        assert corrections == []

    def test_unknown_amount_blocked(self):
        facts = build_allowed_facts(_ctx(intake_values={"monthly_income": "3200"}))
        out, corrections = check_amounts("The filing fee is $435.", facts)
        assert "$435" not in out
        assert "[TO BE COMPLETED]" in out
        assert corrections[0].severity == "needs_review"

    def test_known_amount_outside_support_sentence_preserved(self):
        facts = build_allowed_facts(_ctx(intake_values={"monthly_income": "3200"}))
        text = "Petitioner earns $3,200.00 per month as a dental assistant."
        out, corrections = check_amounts(text, facts)
        assert out == text
        assert corrections == []


class TestCheckDates:
    def test_range_trimmed_to_entered_endpoint(self):
        # The real L4 failure: only June 20 was entered; June 22 never was.
        facts = build_allowed_facts(_ctx(intake_values={"violation_dates": "June 20, 2026"}))
        text = (
            "Throughout the weekend of June 20–22, 2026, Respondent's cellular "
            "telephone was turned off or otherwise unavailable."
        )
        out, corrections = check_dates(text, facts)
        assert "June 20, 2026" in out
        assert "22" not in out
        assert corrections[0].type == "date"
        assert corrections[0].severity == "needs_review"

    def test_entered_date_preserved_across_formats(self):
        # ISO in intake matches long-form in output.
        facts = build_allowed_facts(_ctx(intake_values={"incident_date": "2026-06-14"}))
        text = (
            "On or about June 14, 2026, a Saturday, Petitioner and the minor "
            "children waited at the designated location."
        )
        out, corrections = check_dates(text, facts)
        assert out == text
        assert corrections == []

    def test_unknown_date_blocked(self):
        facts = build_allowed_facts(_ctx(intake_values={"incident_date": "2026-06-14"}))
        out, corrections = check_dates("The hearing is set for August 14, 2026.", facts)
        assert "August 14, 2026" not in out
        assert "[TO BE COMPLETED]" in out
        assert corrections[0].severity == "needs_review"

    def test_fully_unknown_range_blocked(self):
        facts = build_allowed_facts(_ctx(intake_values={}))
        out, _ = check_dates("He was away June 20-22, 2026 without notice.", facts)
        assert "June 20" not in out
        assert "[TO BE COMPLETED]" in out

    def test_dob_always_allowed(self):
        facts = build_allowed_facts(_ctx(children=CHILDREN))
        text = "Sofia Delgado was born on March 22, 2018."
        out, corrections = check_dates(text, facts)
        assert out == text
        assert corrections == []

    def test_yearless_intake_date_allows_dated_output(self):
        facts = build_allowed_facts(_ctx(intake_values={"story": "it happened on June 14"}))
        out, corrections = check_dates("The exchange failed on June 14, 2026.", facts)
        assert corrections == []
        assert "June 14, 2026" in out


class TestCheckAges:
    def _facts(self, children=CHILDREN):
        return build_allowed_facts(_ctx(children=children))

    def test_years_old_corrected_from_dob(self):
        out, corrections = check_ages("Sofia is 6 years old.", self._facts())
        assert out == "Sofia is 8 years old."
        assert corrections[0].type == "age"
        assert corrections[0].severity == "corrected"

    def test_paren_age_corrected(self):
        out, _ = check_ages("Mateo Delgado (age 4) attends preschool.", self._facts())
        assert "(age 5)" in out

    def test_age_seven_corrected_to_eight(self):
        out, _ = check_ages("Sofia (age 7) attends Jefferson Elementary.", self._facts())
        assert "(age 8)" in out

    def test_bare_paren_number_after_name_corrected(self):
        out, _ = check_ages("The children are Sofia (6) and Mateo (4).", self._facts())
        assert "Sofia (8)" in out
        assert "Mateo (5)" in out

    def test_correct_age_untouched(self):
        text = "Sofia is 8 years old."
        out, corrections = check_ages(text, self._facts())
        assert out == text
        assert corrections == []

    def test_no_name_single_child_corrected(self):
        facts = self._facts(children=[CHILDREN[0]])
        out, _ = check_ages("The minor child is age 7.", facts)
        assert "age 8" in out

    def test_no_name_multiple_children_flag_only(self):
        text = "The children are age 7."
        out, corrections = check_ages(text, self._facts())
        assert out == text
        assert len(corrections) == 1
        assert corrections[0].replacement is None

    def test_duration_years_not_treated_as_age(self):
        text = "The parties separated over 3 years ago, and Sofia lives with Petitioner."
        out, corrections = check_ages(text, self._facts())
        assert out == text
        assert corrections == []

    def test_number_paren_without_child_name_untouched(self):
        text = "Petitioner waited approximately forty-five (45) minutes before leaving."
        out, corrections = check_ages(text, self._facts())
        assert out == text
        assert corrections == []


class TestPlaceholderFilledFromProfile:
    def test_petitioner_full_legal_name_filled(self):
        out, corrections = fill_placeholders(
            "[PETITIONER'S FULL LEGAL NAME] declares under penalty of perjury:",
            _ctx(),
        )
        assert out == "Maria Delgado declares under penalty of perjury:"
        assert corrections[0].type == "placeholder_filled"
