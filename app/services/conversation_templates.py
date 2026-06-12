"""
Conversation prompt templates for different scenarios
"""
import json
from typing import Dict, List, Optional, Any
from enum import Enum

class ConversationType(Enum):
    """Types of conversations"""
    GREETING = "greeting"
    CUSTODY_FILING = "custody_filing"
    SUPPORT_MODIFICATION = "support_modification"
    VIOLATION_REPORT = "violation_report"
    RESPONSE_TO_MOTION = "response_to_motion"
    INFORMATION_GATHERING = "information_gathering"
    CLARIFICATION = "clarification"
    CONFIRMATION = "confirmation"
    ERROR_RECOVERY = "error_recovery"

class ConversationTemplates:
    """Manages conversation templates for different scenarios"""

    def __init__(self):
        self.templates = self._initialize_templates()

    def _initialize_templates(self) -> Dict[ConversationType, Dict]:
        """Initialize all conversation templates"""

        templates = {}

        # Greeting templates
        templates[ConversationType.GREETING] = {
            "initial": [
                "Hello! I'm here to help you with California family court motions. What brings you here today?",
                "Welcome! I can assist you with filing motions, responding to court papers, or answering questions about the family court process. How can I help?",
                "Hi there! I'm your California family court assistant. Are you looking to file a new motion or respond to existing papers?"
            ],
            "returning_user": [
                "Welcome back, {name}! How can I assist you today?",
                "Hello again! I see you have case {case_number}. What would you like to work on?",
                "Good to see you again! Would you like to continue with your {motion_type} or start something new?"
            ],
            "quick_replies": [
                "File a new motion",
                "Respond to papers",
                "Check my previous work",
                "I have a question"
            ]
        }

        # Custody filing templates
        templates[ConversationType.CUSTODY_FILING] = {
            "opening": "I can help you with custody matters. Let me understand your situation better.",
            "questions_sequence": [
                {
                    "question": "Are you looking to establish a new custody order or modify an existing one?",
                    "quick_replies": ["New custody order", "Modify existing order", "Not sure"]
                },
                {
                    "question": "What's your current custody arrangement?",
                    "help": "For example: 'Joint legal and physical custody' or 'Mother has sole custody, father has weekend visitation'"
                },
                {
                    "question": "What changes are you requesting and why?",
                    "help": "Please describe what you want changed and the reason (change in circumstances)"
                },
                {
                    "question": "How will this change benefit the children?",
                    "help": "Courts focus on the best interests of the children"
                }
            ],
            "confirmation": "I have the information I need about your custody request. Let me summarize what you've told me..."
        }

        # Support modification templates
        templates[ConversationType.SUPPORT_MODIFICATION] = {
            "opening": "I'll help you with modifying support orders. Let's gather the necessary information.",
            "questions_sequence": [
                {
                    "question": "What type of support are you looking to modify?",
                    "quick_replies": ["Child support", "Spousal support", "Both"]
                },
                {
                    "question": "What is the current support amount?",
                    "validation": "number",
                    "format": "$X,XXX per month"
                },
                {
                    "question": "What amount are you requesting?",
                    "validation": "number",
                    "format": "$X,XXX per month"
                },
                {
                    "question": "What significant change has occurred that justifies this modification?",
                    "examples": ["Job loss", "Income increase", "Change in custody", "Medical expenses"]
                }
            ],
            "confirmation": "I understand you need to modify support from ${current} to ${requested} due to {reason}."
        }

        # Violation report templates
        templates[ConversationType.VIOLATION_REPORT] = {
            "opening": "I understand someone has violated a court order. This is serious. Let me help you document this properly.",
            "urgency_check": {
                "question": "Is this an emergency situation requiring immediate court intervention?",
                "quick_replies": ["Yes, it's an emergency", "No, but it's serious", "I'm not sure"]
            },
            "questions_sequence": [
                {
                    "question": "Which court order was violated?",
                    "help": "Please describe the specific order (e.g., 'Custody order dated 1/15/2024')"
                },
                {
                    "question": "When did the violation occur?",
                    "validation": "date"
                },
                {
                    "question": "Please describe exactly what happened.",
                    "help": "Be specific with dates, times, and facts"
                },
                {
                    "question": "Do you have any evidence of the violation?",
                    "quick_replies": ["Yes", "No", "Some"]
                },
                {
                    "question": "What evidence do you have?",
                    "condition": "previous_answer == 'Yes' or previous_answer == 'Some'",
                    "examples": ["Text messages", "Emails", "Photos", "Witness statements"]
                }
            ],
            "confirmation": "I've documented the violation of {order} that occurred on {date}. This is important information for your filing."
        }

        # Response to motion templates
        templates[ConversationType.RESPONSE_TO_MOTION] = {
            "opening": "I'll help you respond to the court papers you received. Having the papers with you will be helpful.",
            "questions_sequence": [
                {
                    "question": "Do you have the papers with you now?",
                    "quick_replies": ["Yes", "No, but I know what they say", "I need to get them"]
                },
                {
                    "question": "What type of motion did you receive?",
                    "quick_replies": ["Request for Order (FL-300)", "Custody modification", "Support modification", "Other/Not sure"]
                },
                {
                    "question": "When were you served with these papers?",
                    "validation": "date",
                    "help": "This is important for calculating your response deadline"
                },
                {
                    "question": "Do you agree with what they're asking for?",
                    "quick_replies": ["Yes, I agree", "No, I disagree", "I agree with some parts", "I need help understanding"]
                }
            ],
            "confirmation": "You need to respond to {motion_type} by {deadline}. Let's prepare your response."
        }

        # Information gathering templates
        templates[ConversationType.INFORMATION_GATHERING] = {
            "request_missing": "I need a bit more information about {field}.",
            "clarification_needed": "Just to clarify, when you said '{original}', did you mean {clarification}?",
            "validation_failed": "I need to make sure I have {field} in the right format. Could you provide it as {format}?",
            "optional_info": "This is optional, but it would help if you could tell me {field}.",
            "sensitive_info": "I need to ask about {topic}. This information is important for your filing and will be kept confidential."
        }

        # Clarification templates
        templates[ConversationType.CLARIFICATION] = {
            "ambiguous_intent": [
                "I want to make sure I understand correctly. Are you trying to {option1} or {option2}?",
                "Let me clarify - you mentioned {topic}. Could you tell me more about what you need?",
                "I see you're dealing with {issue}. What specific help do you need with this?"
            ],
            "incomplete_answer": [
                "Could you provide a bit more detail about {topic}?",
                "I need to understand {aspect} better. Could you elaborate?",
                "That's helpful. Can you also tell me about {missing_info}?"
            ],
            "format_correction": [
                "I need the {field} in a specific format. For example: {example}",
                "Could you provide the date as MM/DD/YYYY?",
                "Please provide the amount as a number (like 1500 or $1,500)"
            ]
        }

        # Confirmation templates
        templates[ConversationType.CONFIRMATION] = {
            "summary_intro": "Let me summarize what you've told me to make sure I have everything correct:",
            "section_headers": {
                "parties": "📋 **Parties**",
                "case_info": "📁 **Case Information**",
                "request": "📝 **What You're Requesting**",
                "reason": "❓ **Reason for Request**",
                "children": "👨‍👩‍👧‍👦 **Children**",
                "support": "💰 **Support**",
                "evidence": "📎 **Evidence**"
            },
            "confirmation_prompt": "Does everything look correct?",
            "quick_replies": ["Yes, that's correct", "No, I need to change something", "I want to add more information"],
            "ready_to_proceed": "Great! I have all the information I need. I'll now prepare your forms. This will just take a moment."
        }

        # Error recovery templates
        templates[ConversationType.ERROR_RECOVERY] = {
            "misunderstanding": [
                "I apologize, I didn't quite understand that. Let me try asking differently.",
                "Sorry, I'm a bit confused. Let's take a step back.",
                "I want to make sure I'm helping you correctly. Could you rephrase that?"
            ],
            "technical_error": [
                "I encountered a technical issue, but don't worry - your information is saved. Let's continue.",
                "There was a small hiccup, but we can keep going. Where were we?",
                "I had trouble processing that, but let's try again."
            ],
            "validation_error": [
                "That doesn't seem quite right. {specific_error}. Could you check and try again?",
                "I need this information in a specific format. {format_help}",
                "The {field} you provided doesn't match our records. Could you verify it?"
            ],
            "fallback": "I'm having trouble understanding. Would you like to speak with a human assistant or try explaining differently?"
        }

        return templates

    def get_template(
        self,
        conversation_type: ConversationType,
        template_key: str = None
    ) -> Any:
        """
        Get a specific template

        Args:
            conversation_type: Type of conversation
            template_key: Specific template key within the type

        Returns:
            Template content (string, list, or dict)
        """
        if conversation_type not in self.templates:
            return None

        template = self.templates[conversation_type]

        if template_key:
            return template.get(template_key)

        return template

    def get_greeting(
        self,
        is_returning: bool = False,
        user_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get appropriate greeting

        Args:
            is_returning: Whether this is a returning user
            user_data: User profile data for personalization

        Returns:
            Greeting message and quick replies
        """
        greeting_template = self.templates[ConversationType.GREETING]

        if is_returning and user_data:
            templates = greeting_template["returning_user"]
            # Format with user data
            greeting = templates[0].format(
                name=user_data.get("name", ""),
                case_number=user_data.get("case_number", ""),
                motion_type=user_data.get("last_motion_type", "motion")
            )
        else:
            templates = greeting_template["initial"]
            greeting = templates[0]

        return {
            "message": greeting,
            "quick_replies": greeting_template["quick_replies"]
        }

    def get_questions_for_motion(
        self,
        motion_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get question sequence for a specific motion type

        Args:
            motion_type: Type of motion

        Returns:
            List of question dictionaries
        """
        type_mapping = {
            "custody": ConversationType.CUSTODY_FILING,
            "support": ConversationType.SUPPORT_MODIFICATION,
            "violation": ConversationType.VIOLATION_REPORT,
            "response": ConversationType.RESPONSE_TO_MOTION
        }

        conversation_type = type_mapping.get(motion_type)
        if not conversation_type:
            return []

        template = self.templates.get(conversation_type, {})
        return template.get("questions_sequence", [])

    def format_confirmation(
        self,
        collected_data: Dict[str, Any]
    ) -> str:
        """
        Format a confirmation message with collected data

        Args:
            collected_data: All collected information

        Returns:
            Formatted confirmation message
        """
        confirmation = self.templates[ConversationType.CONFIRMATION]

        # Build summary
        parts = [confirmation["summary_intro"]]

        # Add sections based on available data
        if "party_name" in collected_data or "other_party_name" in collected_data:
            parts.append(f"\n{confirmation['section_headers']['parties']}")
            parts.append(f"You: {collected_data.get('party_name', 'Not provided')}")
            parts.append(f"Other party: {collected_data.get('other_party_name', 'Not provided')}")

        if "case_number" in collected_data:
            parts.append(f"\n{confirmation['section_headers']['case_info']}")
            parts.append(f"Case number: {collected_data['case_number']}")

        if "requested_arrangement" in collected_data or "requested_amount" in collected_data:
            parts.append(f"\n{confirmation['section_headers']['request']}")
            if "requested_arrangement" in collected_data:
                parts.append(f"Custody: {collected_data['requested_arrangement']}")
            if "requested_amount" in collected_data:
                parts.append(f"Support: {collected_data['requested_amount']}")

        if "reason" in collected_data or "change_reason" in collected_data:
            parts.append(f"\n{confirmation['section_headers']['reason']}")
            parts.append(collected_data.get('reason', collected_data.get('change_reason', '')))

        parts.append(f"\n{confirmation['confirmation_prompt']}")

        return "\n".join(parts)

    def get_error_response(
        self,
        error_type: str = "misunderstanding"
    ) -> str:
        """
        Get appropriate error recovery response

        Args:
            error_type: Type of error

        Returns:
            Error recovery message
        """
        error_templates = self.templates[ConversationType.ERROR_RECOVERY]
        responses = error_templates.get(error_type, error_templates["fallback"])

        if isinstance(responses, list):
            return responses[0]  # Return first option
        return responses

# Singleton instance
conversation_templates = ConversationTemplates()