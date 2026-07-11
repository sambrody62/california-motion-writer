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
