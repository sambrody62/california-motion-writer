"""
merge_intake_values must ignore the blank re-registered fields that later
wizard steps save over earlier real answers (871cafa regression family;
confirmed live in browser-test3.db on 2026-07-11: blanks poisoned the gate's
intake merge, false-positiving on genuine facts).
"""
from app.services.fact_gate.types import merge_intake_values

# Verbatim per-step question_data shapes stored by the live run
STEP_2 = {"order_types": {"custody": True, "visitation": True, "support": False}}
STEP_3 = {"order_types": {"custody": False, "visitation": False, "support": False}}
STEP_4 = {"has_children": None, "current_custody": "", "monthly_income": "3200"}
STEP_5 = {
    "monthly_income": "",
    "facts_summary": "On June 14, 2026 Respondent kept the children overnight.",
}
STEP_6 = {"facts_summary": ""}


def test_live_run_shapes_keep_the_real_answers():
    merged = merge_intake_values([STEP_2, STEP_3, STEP_4, STEP_5, STEP_6])
    assert merged["order_types"] == {"custody": True, "visitation": True}
    assert merged["monthly_income"] == "3200"
    assert merged["facts_summary"] == STEP_5["facts_summary"]
    # blank-only fields never make it into the ground truth
    assert "has_children" not in merged
    assert "current_custody" not in merged


def test_blank_values_are_skipped():
    merged = merge_intake_values(
        [{"a": "real"}, {"a": ""}, {"a": None}, {"a": "   "}, {"b": None}]
    )
    assert merged == {"a": "real"}


def test_genuine_reanswer_on_a_later_step_still_wins():
    merged = merge_intake_values(
        [{"monthly_income": "3200"}, {"monthly_income": "3500"}]
    )
    assert merged == {"monthly_income": "3500"}


def test_checkbox_groups_union_their_truthy_leaves():
    merged = merge_intake_values(
        [
            {"order_types": {"custody": True, "support": False}},
            {"order_types": {"visitation": True, "custody": False}},
        ]
    )
    assert merged["order_types"] == {"custody": True, "visitation": True}


def test_all_false_group_does_not_erase_an_earlier_group():
    merged = merge_intake_values([STEP_2, STEP_3])
    assert merged["order_types"] == {"custody": True, "visitation": True}


def test_all_false_group_with_no_earlier_group_is_omitted():
    merged = merge_intake_values([STEP_3])
    assert merged == {}


def test_non_dict_entries_are_ignored():
    merged = merge_intake_values([None, "junk", {"a": 1}])
    assert merged == {"a": 1}


def test_inputs_are_not_mutated():
    earlier = {"order_types": {"custody": True, "support": False}}
    later = {"order_types": {"visitation": True}}
    merge_intake_values([earlier, later])
    assert earlier == {"order_types": {"custody": True, "support": False}}
    assert later == {"order_types": {"visitation": True}}
