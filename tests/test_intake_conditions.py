"""
Condition evaluation for the RFO intake service.

Regression for the 2026-07-10 user-story finding F2: '.includes(' was parsed
before '||', so OR-conditions containing includes() always evaluated false —
the Support Details step was silently skipped for users requesting support,
and best_interest_factors was never asked for custody cases.
"""
from app.services.intake import intake_service

SUPPORT_STEP_CONDITION = (
    "relief_categories.includes('child_support') || "
    "relief_categories.includes('spousal_support')"
)
BEST_INTEREST_CONDITION = (
    "relief_categories.includes('custody') || "
    "relief_categories.includes('visitation')"
)


def test_or_of_includes_true_when_either_matches():
    answers = {"relief_categories": ["custody", "child_support"]}
    assert intake_service.evaluate_condition(SUPPORT_STEP_CONDITION, answers) is True
    assert intake_service.evaluate_condition(BEST_INTEREST_CONDITION, answers) is True


def test_or_of_includes_false_when_neither_matches():
    answers = {"relief_categories": ["property"]}
    assert intake_service.evaluate_condition(SUPPORT_STEP_CONDITION, answers) is False
    assert intake_service.evaluate_condition(BEST_INTEREST_CONDITION, answers) is False


def test_single_includes_still_works():
    answers = {"relief_categories": ["custody"]}
    assert intake_service.evaluate_condition(
        "relief_categories.includes('custody')", answers
    ) is True
    assert intake_service.evaluate_condition(
        "relief_categories.includes('property')", answers
    ) is False


def test_support_step_follows_custody_step():
    answers = {"relief_categories": ["custody", "child_support"]}
    next_step = intake_service.get_next_step(3, answers)
    assert next_step is not None
    assert next_step["step"] == 4  # was: skipped straight to 5


def test_best_interest_question_shown_for_custody():
    answers = {"relief_categories": ["custody"]}
    step5 = intake_service.get_step(5)
    question_ids = [q["id"] for q in intake_service.get_applicable_questions(step5, answers)]
    assert "best_interest_factors" in question_ids
