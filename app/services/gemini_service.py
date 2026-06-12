"""
Google Gemini AI Service for California Motion Writer
"""
import os
from typing import Dict, Any, Optional, List
import google.generativeai as genai
from app.core.config import settings

# Configure Gemini with API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

class GeminiService:
    """Service for Google Gemini AI interactions"""

    def __init__(self):
        """Initialize Gemini service"""
        self.api_key = GOOGLE_API_KEY

        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")

        # Use Gemini 1.5 Flash for fast responses
        self.model = genai.GenerativeModel('gemini-1.5-flash')

        # Use Gemini 1.5 Pro for complex tasks
        self.pro_model = genai.GenerativeModel('gemini-1.5-pro')

        print("✅ Gemini Service initialized with API key")

    async def rewrite_rfo_section(
        self,
        section_name: str,
        user_answers: Dict[str, Any],
        context: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rewrite an RFO section using Gemini"""
        try:
            # Build prompt
            prompt = f"""You are a legal writing assistant specializing in California family law.
            Rewrite the following section for a Request for Order (RFO) motion.

            Section: {section_name}
            User Information: {user_answers}
            Context: {context}

            Provide a professional, clear, and legally appropriate response.
            Focus on facts and avoid emotional language.
            Format for a California family court.
            """

            # Generate response
            response = self.model.generate_content(prompt)

            return {
                "success": True,
                "rewritten_text": response.text,
                "model": "gemini-1.5-flash",
                "tokens_used": 0  # Gemini doesn't provide token count easily
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rewritten_text": ""
            }

    async def rewrite_declaration(
        self,
        narrative: str,
        declarant_name: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rewrite narrative as formal declaration"""
        try:
            prompt = f"""You are a legal writing assistant. Convert the following narrative into a formal legal declaration for California family court.

            Declarant: {declarant_name}
            Narrative: {narrative}

            Format as numbered paragraphs starting with "I, {declarant_name}, declare as follows:"
            Include only factual statements, no opinions or emotions.
            End with a declaration under penalty of perjury under California law.
            """

            # Use Pro model for more complex legal writing
            response = self.pro_model.generate_content(prompt)

            return {
                "success": True,
                "rewritten_text": response.text,
                "model": "gemini-1.5-pro"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rewritten_text": ""
            }

    async def enhance_best_interests(
        self,
        custody_request: str,
        children_info: List[Dict]
    ) -> Dict[str, Any]:
        """Enhance custody request with best interests factors"""
        try:
            children_details = "\n".join([
                f"- {child.get('name', 'Child')}, age {child.get('age', 'unknown')}"
                for child in children_info
            ])

            prompt = f"""You are a California family law assistant. Enhance this custody request by incorporating California's best interests of the child factors.

            Custody Request: {custody_request}
            Children:
            {children_details}

            Include relevant factors from California Family Code § 3011:
            1. Health, safety, and welfare of the child
            2. History of abuse by one parent
            3. Nature and amount of contact with both parents
            4. Habitual or continual use of alcohol or drugs

            Write in a professional, fact-based manner suitable for court filing.
            """

            response = self.model.generate_content(prompt)

            return {
                "success": True,
                "enhanced_text": response.text,
                "model": "gemini-1.5-flash"
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "enhanced_text": ""
            }

    async def process_complete_motion(
        self,
        motion_type: str,
        all_answers: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process complete motion with all sections"""
        try:
            prompt = f"""You are a California family law assistant. Create a complete {motion_type} motion based on:

            User Profile: {user_profile}
            Answers: {all_answers}

            Generate professional legal content for:
            1. Introduction and procedural history
            2. Statement of facts
            3. Legal argument
            4. Conclusion and prayer for relief

            Follow California court formatting requirements.
            Use clear, professional legal language.
            """

            # Use Pro model for complete motion generation
            response = self.pro_model.generate_content(prompt)

            return {
                "success": True,
                "complete_motion": response.text,
                "model": "gemini-1.5-pro",
                "sections": self._parse_sections(response.text)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "complete_motion": ""
            }

    def _parse_sections(self, text: str) -> Dict[str, str]:
        """Parse generated text into sections"""
        sections = {}
        current_section = "introduction"
        current_content = []

        for line in text.split('\n'):
            if any(keyword in line.lower() for keyword in ['introduction', 'procedural history']):
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "introduction"
                current_content = [line]
            elif 'statement of facts' in line.lower() or 'facts' in line.lower():
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "facts"
                current_content = [line]
            elif 'legal argument' in line.lower() or 'argument' in line.lower():
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "argument"
                current_content = [line]
            elif 'conclusion' in line.lower() or 'prayer' in line.lower():
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                current_section = "conclusion"
                current_content = [line]
            else:
                current_content.append(line)

        # Add last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def validate_output(self, text: str) -> Dict[str, Any]:
        """Validate generated text"""
        issues = []

        # Check minimum length (50 words)
        word_count = len(text.split())
        if word_count < 50:
            issues.append("Output too short (less than 50 words)")

        # Check for inappropriate content
        inappropriate_terms = ['legal advice', 'I am not a lawyer', 'consult an attorney']
        for term in inappropriate_terms:
            if term.lower() in text.lower():
                issues.append(f"Contains disclaimer: '{term}'")

        # Check for California-specific language
        ca_terms = ['California', 'Family Code', 'FL-']
        has_ca_reference = any(term in text for term in ca_terms)
        if not has_ca_reference and word_count > 100:
            issues.append("Missing California-specific references")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "word_count": word_count
        }

# Create a singleton instance
gemini_service = GeminiService() if GOOGLE_API_KEY else None