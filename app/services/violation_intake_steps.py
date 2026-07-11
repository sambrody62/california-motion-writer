"""
Transform the flat form-config intakeQuestions map into the 3-step wizard
shape ViolationIntake.tsx renders.

Regression L5 (2026-07-11 real-LLM browser test): /violations/intake-questions
returned the raw config map, and the frontend's step/questions[] parser crashed
#/violation/intake to a blank screen for every user.
"""
from typing import Any, Dict, List

# (step_name, description, question ids in render order)
_STEP_LAYOUT = [
    (
        "Order & Urgency",
        "Tell us which court order was violated and whether this is an emergency.",
        ["violationType", "urgency"],
    ),
    (
        "What Happened",
        "Describe the violation and the evidence you have.",
        ["violationDates", "violationDescription", "evidence"],
    ),
    (
        "Resolution & Requested Relief",
        "Tell us about resolution attempts, prior violations, and what you want the court to do.",
        [
            "attemptedResolution",
            "resolutionDescription",
            "priorViolations",
            "priorViolationsDescription",
            "requestedRelief",
        ],
    ),
]

# Config question type → frontend ViolationQuestionField type
_TYPE_MAP = {
    "select": "select",
    "boolean": "radio",
    "dateList": "text",
    "textarea": "textarea",
    "multiSelect": "checkbox",
}

# followUp textarea id → the boolean config question it follows.
# The urgency followUp is dropped deliberately: ViolationIntakeRequest has no
# field for it, so rendering it would silently discard sworn user input.
_FOLLOW_UP_PARENTS = {
    "resolutionDescription": "attemptedResolution",
    "priorViolationsDescription": "priorViolations",
}

# The frontend splits this answer on commas (toArray in ViolationIntake.tsx).
_DATE_LIST_HELP = "List each date separated by commas (e.g. 2026-06-06, 2026-06-13)."
_FOLLOW_UP_HELP = "Only needed if you answered Yes above."


def _build_question(question_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
    mapped_type = _TYPE_MAP[config["type"]]
    question: Dict[str, Any] = {
        "id": question_id,
        "type": mapped_type,
        "label": config["question"],
        "required": bool(config.get("required", False)),
    }
    if config["type"] == "boolean":
        question["options"] = ["Yes", "No"]
    elif "options" in config:
        question["options"] = list(config["options"])
    if config["type"] == "dateList":
        question["help_text"] = _DATE_LIST_HELP
    return question


def _build_follow_up(question_id: str, follow_up: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": question_id,
        "type": "textarea",
        "label": follow_up["question"],
        "required": False,
        "help_text": _FOLLOW_UP_HELP,
    }


def build_wizard_steps(intake_questions: Dict[str, Any]) -> Dict[str, Any]:
    """Flat config map → {"step1": {step_number, step_name, description, questions}, ...}"""
    steps: Dict[str, Any] = {}
    for number, (name, description, question_ids) in enumerate(_STEP_LAYOUT, start=1):
        questions: List[Dict[str, Any]] = []
        for question_id in question_ids:
            parent_id = _FOLLOW_UP_PARENTS.get(question_id)
            if parent_id is not None:
                follow_up = intake_questions[parent_id]["followUp"]
                questions.append(_build_follow_up(question_id, follow_up))
            else:
                questions.append(_build_question(question_id, intake_questions[question_id]))
        steps[f"step{number}"] = {
            "step_number": number,
            "step_name": name,
            "description": description,
            "questions": questions,
        }
    return steps
