"""
Comprehensive help system with examples, tutorials, and contextual assistance
"""
from typing import Dict, List, Any, Optional
from enum import Enum
import json

class HelpCategory(Enum):
    """Categories of help content"""
    GETTING_STARTED = "getting_started"
    FORMS = "forms"
    FILING = "filing"
    DEADLINES = "deadlines"
    LEGAL_TERMS = "legal_terms"
    TROUBLESHOOTING = "troubleshooting"
    EXAMPLES = "examples"
    TIPS = "tips"


class HelpTopic:
    """Individual help topic"""

    def __init__(self, topic_id: str, title: str, category: HelpCategory):
        self.topic_id = topic_id
        self.title = title
        self.category = category
        self.content = ""
        self.examples = []
        self.related_topics = []
        self.keywords = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            'topic_id': self.topic_id,
            'title': self.title,
            'category': self.category.value,
            'content': self.content,
            'examples': self.examples,
            'related_topics': self.related_topics,
            'keywords': self.keywords
        }


class LegalGlossary:
    """Legal term glossary"""

    def __init__(self):
        self.terms = self._initialize_glossary()

    def _initialize_glossary(self) -> Dict[str, Dict[str, str]]:
        """Initialize legal terms dictionary"""
        return {
            "petitioner": {
                "definition": "The person who starts a court case by filing a petition or request with the court.",
                "example": "If you file for divorce, you are the petitioner.",
                "related": ["respondent", "party"]
            },
            "respondent": {
                "definition": "The person who must respond to a court case started by someone else.",
                "example": "If your spouse files for divorce, you are the respondent.",
                "related": ["petitioner", "party"]
            },
            "request_for_order": {
                "definition": "A formal request asking the court to make orders about child custody, support, or other family law issues.",
                "abbreviation": "RFO",
                "example": "You file an RFO to change your custody schedule.",
                "related": ["motion", "order"]
            },
            "ex_parte": {
                "definition": "Emergency court orders made without notifying the other party first, used only in urgent situations.",
                "example": "Ex parte orders for immediate danger to children.",
                "related": ["emergency_order", "temporary_order"]
            },
            "declaration": {
                "definition": "A written statement made under penalty of perjury, used as evidence in court.",
                "example": "Your declaration explains why you need the court orders.",
                "related": ["affidavit", "testimony"]
            },
            "service": {
                "definition": "The legal process of delivering court documents to the other party.",
                "example": "You must serve the other party with your filed documents.",
                "related": ["proof_of_service", "notice"]
            },
            "contempt": {
                "definition": "Willful disobedience of a court order, punishable by fines or jail.",
                "example": "Not paying court-ordered child support can lead to contempt.",
                "related": ["violation", "enforcement"]
            },
            "custody": {
                "definition": "The legal right to make decisions about children (legal custody) and have them live with you (physical custody).",
                "types": ["legal_custody", "physical_custody", "joint_custody", "sole_custody"],
                "related": ["visitation", "parenting_time"]
            },
            "child_support": {
                "definition": "Money paid by one parent to the other for children's living expenses.",
                "example": "Monthly payments for food, housing, and clothing.",
                "related": ["guideline_support", "support_modification"]
            },
            "spousal_support": {
                "definition": "Money paid by one spouse to support the other after separation.",
                "also_known_as": "alimony",
                "related": ["temporary_support", "permanent_support"]
            },
            "discovery": {
                "definition": "The legal process of getting information from the other party.",
                "types": ["interrogatories", "depositions", "document_requests"],
                "related": ["disclosure", "evidence"]
            },
            "mediation": {
                "definition": "A process where a neutral third party helps parents reach agreements.",
                "example": "Court-ordered mediation for custody disputes.",
                "related": ["settlement", "negotiation"]
            },
            "stipulation": {
                "definition": "A written agreement between parties that becomes a court order.",
                "example": "Parents agree on custody changes without a hearing.",
                "related": ["agreement", "consent_order"]
            },
            "jurisdiction": {
                "definition": "The court's legal authority to make decisions in your case.",
                "example": "California courts have jurisdiction if children lived here 6 months.",
                "related": ["venue", "uccjea"]
            },
            "best_interests": {
                "definition": "The legal standard for making decisions about children.",
                "factors": ["health", "safety", "welfare", "stability"],
                "related": ["custody", "visitation"]
            }
        }

    def get_term(self, term: str) -> Optional[Dict[str, str]]:
        """Get definition for a legal term"""
        # Normalize term (remove spaces, lowercase)
        normalized = term.lower().replace(' ', '_').replace('-', '_')
        return self.terms.get(normalized)

    def search_terms(self, keyword: str) -> List[Dict[str, Any]]:
        """Search for terms containing keyword"""
        results = []
        keyword_lower = keyword.lower()

        for term_key, term_data in self.terms.items():
            # Check if keyword appears in term, definition, or example
            if (keyword_lower in term_key or
                keyword_lower in term_data.get('definition', '').lower() or
                keyword_lower in term_data.get('example', '').lower()):

                results.append({
                    'term': term_key.replace('_', ' ').title(),
                    'definition': term_data.get('definition'),
                    'example': term_data.get('example')
                })

        return results


class FilingTips:
    """Filing tips and best practices"""

    def __init__(self):
        self.tips = self._initialize_tips()

    def _initialize_tips(self) -> Dict[str, List[str]]:
        """Initialize filing tips by category"""
        return {
            "before_filing": [
                "Always make 3 copies: one for court, one for other party, one for yourself",
                "Check your local court's filing hours and requirements",
                "Bring payment for filing fees or approved fee waiver",
                "Review all forms for completeness and accuracy",
                "Sign and date all required signature lines"
            ],
            "at_courthouse": [
                "Arrive early - filing can take 30-60 minutes",
                "Bring photo ID and case number if you have one",
                "Ask clerk to stamp all your copies",
                "Get a receipt for any fees paid",
                "Ask about next steps and deadlines"
            ],
            "after_filing": [
                "Serve the other party within required timeframe (usually 16 court days before hearing)",
                "File proof of service with the court",
                "Calendar all important dates and deadlines",
                "Prepare for your hearing - organize documents and practice what to say",
                "Consider mediation if required or available"
            ],
            "common_mistakes": [
                "Not serving papers in time - this can cancel your hearing",
                "Forgetting to file proof of service - court needs proof other party was notified",
                "Missing required forms - each request type needs specific forms",
                "Incorrect case number - double-check on all pages",
                "Not keeping copies - never give away your only copy"
            ],
            "emergency_filings": [
                "Call court first to confirm ex parte calendar days/times",
                "Prepare declaration explaining the emergency clearly",
                "Bring evidence supporting immediate danger or harm",
                "Be ready to explain why you couldn't give notice",
                "Expect to wait - bring essentials for potentially long wait"
            ],
            "document_preparation": [
                "Type or print clearly in blue or black ink",
                "Use legal-size paper if required by your court",
                "Don't use correction fluid - cross out mistakes with single line",
                "Attach exhibits in order with exhibit tags",
                "Number all pages if filing multiple documents"
            ]
        }

    def get_tips(self, category: str) -> List[str]:
        """Get tips for a specific category"""
        return self.tips.get(category, [])

    def get_all_tips(self) -> Dict[str, List[str]]:
        """Get all filing tips"""
        return self.tips


class HelpSystemService:
    """Main help system service"""

    def __init__(self):
        self.topics = self._initialize_help_topics()
        self.glossary = LegalGlossary()
        self.filing_tips = FilingTips()
        self.contextual_help = self._initialize_contextual_help()

    def _initialize_help_topics(self) -> Dict[str, HelpTopic]:
        """Initialize help topics"""
        topics = {}

        # Getting Started
        getting_started = HelpTopic("getting_started", "Getting Started", HelpCategory.GETTING_STARTED)
        getting_started.content = """
        Welcome to the California Motion Writer! Here's how to get started:

        1. **Create Your Profile**: Save your basic information to avoid re-entering it
        2. **Choose Your Motion Type**: Select what you're trying to accomplish
        3. **Answer Questions**: Our chatbot will guide you through the necessary information
        4. **Review and Edit**: Check your answers before generating documents
        5. **Generate PDFs**: Create professional court documents ready for filing
        """
        getting_started.examples = [
            "To request custody changes, select 'Modify Custody Order'",
            "For emergency situations, choose 'Emergency Ex Parte Order'"
        ]
        getting_started.keywords = ["start", "begin", "new", "first time"]
        topics["getting_started"] = getting_started

        # Form Types
        form_types = HelpTopic("form_types", "Understanding Court Forms", HelpCategory.FORMS)
        form_types.content = """
        Common California family law forms:

        - **FL-300**: Request for Order - Main form for asking court to make orders
        - **FL-320**: Response to Request for Order - Respond when served with RFO
        - **FL-150**: Income and Expense Declaration - Required for support requests
        - **FL-305**: Temporary Emergency Orders - For urgent situations
        - **MC-030**: Declaration - Written statement under penalty of perjury
        """
        form_types.related_topics = ["fl300_guide", "fl150_guide"]
        form_types.keywords = ["forms", "fl-300", "fl-320", "which form"]
        topics["form_types"] = form_types

        # Deadlines
        deadlines = HelpTopic("deadlines", "Important Deadlines", HelpCategory.DEADLINES)
        deadlines.content = """
        Critical deadlines in family court:

        - **Service**: Serve papers at least 16 court days before hearing
        - **Response to RFO**: File response at least 9 court days before hearing
        - **Proof of Service**: File at least 5 court days before hearing
        - **Ex Parte Notice**: Give notice by 10 AM the court day before (unless true emergency)
        - **Income & Expense Declaration**: Must be current within 3 months
        """
        deadlines.examples = [
            "If hearing is March 20, serve by March 1 (counting only court days)"
        ]
        deadlines.keywords = ["deadline", "when", "how long", "time limit"]
        topics["deadlines"] = deadlines

        return topics

    def _initialize_contextual_help(self) -> Dict[str, str]:
        """Initialize contextual help for specific UI elements"""
        return {
            "case_number": "Your case number is on all court documents. Format: FL-2024-123456",
            "hearing_date": "The date the judge will hear your case. Found on court notice.",
            "declaration_text": "Write facts, not opinions. Be specific with dates and events.",
            "emergency_reason": "Explain immediate danger or irreparable harm that can't wait.",
            "service_address": "Current address where other party can be served with documents.",
            "income_information": "Include all income sources: wages, bonuses, investments, etc.",
            "custody_request": "Be specific: days, times, holidays, vacation schedules.",
            "support_amount": "Calculate using California guideline calculator or recent paystubs."
        }

    def get_help_topic(self, topic_id: str) -> Optional[HelpTopic]:
        """Get a specific help topic"""
        return self.topics.get(topic_id)

    def search_help(self, query: str) -> List[HelpTopic]:
        """Search help topics by keyword"""
        results = []
        query_lower = query.lower()

        for topic in self.topics.values():
            # Check title, content, and keywords
            if (query_lower in topic.title.lower() or
                query_lower in topic.content.lower() or
                any(query_lower in keyword for keyword in topic.keywords)):

                results.append(topic)

        return results

    def get_contextual_help(self, field_name: str) -> Optional[str]:
        """Get contextual help for a specific field"""
        return self.contextual_help.get(field_name)

    def get_quick_answers(self) -> Dict[str, str]:
        """Get common questions and quick answers"""
        return {
            "How long do I have to respond?": "Usually 9 court days before the hearing date.",
            "Do I need a lawyer?": "You can represent yourself (pro per) but may want legal advice.",
            "What if I can't afford filing fees?": "Request a fee waiver (Form FW-001).",
            "Where do I file?": "File in the county where your case is or where children live.",
            "Can I change my filed documents?": "Yes, file an amended version before the hearing.",
            "What should I wear to court?": "Business casual - no shorts, tank tops, or hats.",
            "Can I bring someone for support?": "Yes, but they usually can't speak for you.",
            "What if I need an interpreter?": "Request one in advance using Form INT-300."
        }

    def get_example_scenarios(self) -> List[Dict[str, str]]:
        """Get example scenarios with solutions"""
        return [
            {
                "scenario": "Ex moved out of state with children",
                "solution": "File FL-300 for custody modification and possible FL-305 for emergency orders",
                "tips": "Document the move, show established ties to California, propose visitation plan"
            },
            {
                "scenario": "Haven't received child support in 3 months",
                "solution": "File FL-410 (contempt) and FL-411 (affidavit) with payment history",
                "tips": "Gather bank statements, keep communication records, calculate total owed"
            },
            {
                "scenario": "Lost job, can't pay current support",
                "solution": "File FL-300 immediately for support modification with FL-150",
                "tips": "Don't wait - file as soon as income changes, provide termination letter"
            }
        ]


# Singleton instance
help_system = HelpSystemService()