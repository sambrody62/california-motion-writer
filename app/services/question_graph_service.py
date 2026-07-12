"""
Dynamic question dependency graph for intelligent conversation flow
"""
import json
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QuestionType(Enum):
    """Types of questions in the conversation"""
    REQUIRED = "required"  # Must be answered
    OPTIONAL = "optional"  # Nice to have
    CONDITIONAL = "conditional"  # Asked based on previous answers
    CLARIFICATION = "clarification"  # Asked to clarify ambiguous answers

@dataclass
class Question:
    """Represents a question in the conversation flow"""
    id: str
    text: str
    field_name: str  # Maps to form field
    question_type: QuestionType
    data_type: str  # text, date, number, boolean, choice
    choices: Optional[List[str]] = None
    depends_on: Optional[Dict[str, Any]] = None  # Conditions for asking
    validates: Optional[str] = None  # Regex or validation rule
    examples: Optional[List[str]] = None
    help_text: Optional[str] = None
    priority: int = 50  # 0-100, higher = more important

class QuestionGraph:
    """Manages dynamic question flow based on dependencies and context"""

    def __init__(self):
        self.questions = {}
        self.question_sets = {}
        self._load_question_definitions()

    def _load_question_definitions(self):
        """Load predefined question sets for different motion types"""

        # Custody modification questions
        self.question_sets["custody_modification"] = [
            Question(
                id="custody_current",
                text="What is your current custody arrangement?",
                field_name="current_custody_arrangement",
                question_type=QuestionType.REQUIRED,
                data_type="text",
                examples=["Joint legal and physical custody", "Sole custody to mother, visitation to father"],
                priority=90
            ),
            Question(
                id="custody_requested",
                text="What custody arrangement are you requesting?",
                field_name="requested_custody_arrangement",
                question_type=QuestionType.REQUIRED,
                data_type="text",
                examples=["50/50 physical custody", "Sole legal custody"],
                priority=90
            ),
            Question(
                id="custody_reason",
                text="Why are you requesting this change?",
                field_name="change_reason",
                question_type=QuestionType.REQUIRED,
                data_type="text",
                help_text="Describe the significant change in circumstances",
                priority=85
            ),
            Question(
                id="child_preference",
                text="Has the child expressed a preference? If so, what?",
                field_name="child_preference",
                question_type=QuestionType.CONDITIONAL,
                data_type="text",
                depends_on={"child_age": {">=": 14}},
                priority=60
            ),
            Question(
                id="safety_concerns",
                text="Are there any safety concerns?",
                field_name="safety_concerns",
                question_type=QuestionType.REQUIRED,
                data_type="boolean",
                priority=95
            ),
            Question(
                id="safety_details",
                text="Please describe the safety concerns",
                field_name="safety_concern_details",
                question_type=QuestionType.CONDITIONAL,
                data_type="text",
                depends_on={"safety_concerns": True},
                priority=95
            )
        ]

        # Support modification questions
        self.question_sets["support_modification"] = [
            Question(
                id="support_current",
                text="What is the current support amount?",
                field_name="current_support_amount",
                question_type=QuestionType.REQUIRED,
                data_type="number",
                validates=r"^\$?\d+(\.\d{2})?$",
                examples=["$1,500", "1500.00"],
                priority=90
            ),
            Question(
                id="support_requested",
                text="What support amount are you requesting?",
                field_name="requested_support_amount",
                question_type=QuestionType.REQUIRED,
                data_type="number",
                validates=r"^\$?\d+(\.\d{2})?$",
                priority=90
            ),
            Question(
                id="income_change",
                text="Has there been a change in income?",
                field_name="income_changed",
                question_type=QuestionType.REQUIRED,
                data_type="boolean",
                priority=85
            ),
            Question(
                id="income_details",
                text="Describe the income change",
                field_name="income_change_details",
                question_type=QuestionType.CONDITIONAL,
                data_type="text",
                depends_on={"income_changed": True},
                examples=["Lost job in March", "New job with 20% pay increase"],
                priority=85
            )
        ]

        # Violation report questions
        self.question_sets["violation_report"] = [
            Question(
                id="order_violated",
                text="Which court order was violated?",
                field_name="violated_order",
                question_type=QuestionType.REQUIRED,
                data_type="text",
                examples=["Custody order dated 1/15/2024", "Support order"],
                priority=95
            ),
            Question(
                id="violation_date",
                text="When did the violation occur?",
                field_name="violation_date",
                question_type=QuestionType.REQUIRED,
                data_type="date",
                validates=r"^\d{1,2}/\d{1,2}/\d{4}$",
                priority=90
            ),
            Question(
                id="violation_description",
                text="Describe what happened",
                field_name="violation_details",
                question_type=QuestionType.REQUIRED,
                data_type="text",
                priority=85
            ),
            Question(
                id="violation_pattern",
                text="Has this happened before?",
                field_name="repeated_violation",
                question_type=QuestionType.REQUIRED,
                data_type="boolean",
                priority=80
            ),
            Question(
                id="violation_evidence",
                text="Do you have evidence of the violation?",
                field_name="has_evidence",
                question_type=QuestionType.REQUIRED,
                data_type="boolean",
                priority=75
            ),
            Question(
                id="evidence_description",
                text="What evidence do you have?",
                field_name="evidence_details",
                question_type=QuestionType.CONDITIONAL,
                data_type="text",
                depends_on={"has_evidence": True},
                examples=["Text messages", "Witness statements", "Photos"],
                priority=75
            )
        ]

        # General questions for all motions
        self.question_sets["general"] = [
            Question(
                id="case_number",
                text="What is your case number?",
                field_name="case_number",
                question_type=QuestionType.OPTIONAL,
                data_type="text",
                validates=r"^[A-Z0-9-]+$",
                priority=30
            ),
            Question(
                id="hearing_requested",
                text="Are you requesting a hearing?",
                field_name="hearing_requested",
                question_type=QuestionType.REQUIRED,
                data_type="boolean",
                priority=70
            ),
            Question(
                id="emergency_order",
                text="Is this an emergency that needs immediate attention?",
                field_name="is_emergency",
                question_type=QuestionType.REQUIRED,
                data_type="boolean",
                priority=100
            )
        ]

    def get_next_question(
        self,
        motion_type: str,
        answered: Dict[str, Any],
        profile_data: Dict[str, Any] = None
    ) -> Optional[Question]:
        """
        Get the next question to ask based on what's been answered

        Args:
            motion_type: Type of motion being filed
            answered: Dictionary of already answered questions
            profile_data: User profile data to skip questions

        Returns:
            Next Question to ask, or None if complete
        """
        # Get relevant question sets
        questions = []
        if motion_type in self.question_sets:
            questions.extend(self.question_sets[motion_type])
        questions.extend(self.question_sets["general"])

        # Filter out already answered questions
        unanswered = []
        for q in questions:
            # Skip if already answered
            if q.field_name in answered:
                continue

            # Skip if available in profile
            if profile_data and q.field_name in profile_data:
                continue

            # Check dependencies
            if q.depends_on:
                if not self._check_dependencies(q.depends_on, answered):
                    continue

            unanswered.append(q)

        # Sort by priority and return highest
        if unanswered:
            unanswered.sort(key=lambda x: x.priority, reverse=True)
            return unanswered[0]

        return None

    def _check_dependencies(self, depends_on: Dict, answered: Dict) -> bool:
        """Check if dependencies are met for a conditional question"""
        for field, condition in depends_on.items():
            if field not in answered:
                return False

            value = answered[field]

            # Handle different condition types
            if isinstance(condition, bool):
                if value != condition:
                    return False
            elif isinstance(condition, dict):
                # Handle operators like >=, <=, ==
                for op, threshold in condition.items():
                    if op == ">=" and value < threshold:
                        return False
                    elif op == "<=" and value > threshold:
                        return False
                    elif op == "==" and value != threshold:
                        return False
                    elif op == "!=" and value == threshold:
                        return False
            elif value != condition:
                return False

        return True

    def get_required_fields(self, motion_type: str) -> List[str]:
        """Get list of required fields for a motion type"""
        required = []

        if motion_type in self.question_sets:
            for q in self.question_sets[motion_type]:
                if q.question_type == QuestionType.REQUIRED:
                    required.append(q.field_name)

        # Add general required fields
        for q in self.question_sets["general"]:
            if q.question_type == QuestionType.REQUIRED:
                required.append(q.field_name)

        return required

    def validate_completeness(
        self,
        motion_type: str,
        answered: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Check if all required questions are answered

        Returns:
            (is_complete, list_of_missing_fields)
        """
        required = self.get_required_fields(motion_type)
        missing = [field for field in required if field not in answered]

        return len(missing) == 0, missing

    def get_question_by_field(self, field_name: str, motion_type: str = None) -> Optional[Question]:
        """Get a question by its field name"""
        # Search in motion-specific questions first
        if motion_type and motion_type in self.question_sets:
            for q in self.question_sets[motion_type]:
                if q.field_name == field_name:
                    return q

        # Search in general questions
        for q in self.question_sets["general"]:
            if q.field_name == field_name:
                return q

        return None

    def generate_summary(self, answered: Dict[str, Any]) -> str:
        """Generate a summary of answered questions"""
        summary_parts = []

        # Group by categories
        categories = {
            "Basic Information": ["case_number", "is_emergency", "hearing_requested"],
            "Custody Details": ["current_custody_arrangement", "requested_custody_arrangement", "change_reason"],
            "Support Details": ["current_support_amount", "requested_support_amount", "income_change_details"],
            "Violation Details": ["violated_order", "violation_date", "violation_details"],
            "Safety Concerns": ["safety_concerns", "safety_concern_details"]
        }

        for category, fields in categories.items():
            category_items = []
            for field in fields:
                if field in answered and answered[field]:
                    # Make field name human-readable
                    field_label = field.replace("_", " ").title()
                    value = answered[field]

                    # Format boolean values
                    if isinstance(value, bool):
                        value = "Yes" if value else "No"

                    category_items.append(f"• {field_label}: {value}")

            if category_items:
                summary_parts.append(f"**{category}**")
                summary_parts.extend(category_items)
                summary_parts.append("")

        return "\n".join(summary_parts)

# Singleton instance
question_graph = QuestionGraph()