"""
LLM Service for motion rewriting using Vertex AI
"""
import os
import json
from typing import Awaitable, Callable, Dict, Any, Optional, List
from pathlib import Path

# Conditionally import GCP services
USE_GCP = os.getenv("USE_GCP", "true").lower() == "true"
USE_MOCK_LLM = os.getenv("USE_MOCK_LLM", "false").lower() == "true"
USE_CLAUDE = os.getenv("USE_CLAUDE", "false").lower() == "true"

if USE_GCP and not USE_MOCK_LLM and not USE_CLAUDE:
    try:
        from google.cloud import aiplatform
        from google.cloud.aiplatform import initializer
        from vertexai.generative_models import GenerativeModel, GenerationConfig, SafetySetting, HarmCategory, HarmBlockThreshold
        import vertexai
    except ImportError:
        USE_MOCK_LLM = True
        print("Warning: Vertex AI not available, using mock LLM for local development")
elif not USE_MOCK_LLM and not USE_CLAUDE:
    # USE_GCP=false with no other backend selected — mock is the only option left.
    # Without this, __init__ would call vertexai.init() with vertexai never imported.
    USE_MOCK_LLM = True
    print("Warning: no LLM backend configured (USE_GCP=false), using mock LLM")

from app.core.config import settings
from app.middleware.rate_limit_config import get_token_limit
from app.services.cost_monitoring_service import track_llm_cost, check_budget
from app.services.fact_gate.prompt_guard import build_fact_anchor
import logging

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        # Load prompts
        prompts_path = Path(__file__).parent.parent.parent / "llm-prompts.md"
        try:
            with open(prompts_path, 'r') as f:
                self.prompts_content = f.read()
        except FileNotFoundError:
            print(f"Warning: {prompts_path} not found, using default prompts")
            self.prompts_content = ""

        self.claude_backend = None
        if USE_MOCK_LLM:
            print("Using mock LLM for local development")
            self.model = None
            self.generation_config = None
            self.safety_settings = None
        elif USE_CLAUDE:
            from app.services.claude_llm_service import ClaudeLLMService

            self.claude_backend = ClaudeLLMService(self._get_system_prompt())
            self.model = None
            self.generation_config = None
            self.safety_settings = None
            self.operation_configs = {}
        else:
            # Initialize Vertex AI
            vertexai.init(
                project=settings.PROJECT_ID,
                location=settings.VERTEX_AI_LOCATION
            )

            # Initialize model
            self.model = GenerativeModel(
                model_name=settings.VERTEX_AI_MODEL,
                system_instruction=self._get_system_prompt()
            )

            # Generation config with smart limits
            self.generation_config = GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=6000,  # Reduced from 8192 for cost control
            )

            # Dynamic configs for different operations
            self.operation_configs = {
                "chat_response": GenerationConfig(
                    temperature=0.8,
                    top_p=0.95,
                    max_output_tokens=1024
                ),
                "section_rewrite": GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=3000
                ),
                "declaration": GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=4000
                ),
                "complete_motion": GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    max_output_tokens=6000
                )
            }

            # Safety settings - Allow legal content
            self.safety_settings = [
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                    threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                    threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                    threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
                ),
                SafetySetting(
                    category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                    threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH
                )
            ]
    
    def _get_system_prompt(self) -> str:
        """Extract system prompt from prompts file"""
        return """You are a legal writing assistant specializing in California family law motions. Your role is to help self-represented litigants create clear, professional, and legally appropriate court documents.

IMPORTANT CONSTRAINTS:
- You provide writing assistance only, NOT legal advice
- All output must comply with California Rules of Court
- Use formal, respectful court language
- Be factual and avoid inflammatory language
- Maintain consistency with user-provided facts
- Never fabricate facts or evidence"""
    
    def _build_rfo_prompt(
        self,
        section_name: str,
        user_input: str,
        context: Dict[str, Any]
    ) -> str:
        """Build RFO rewrite prompt"""
        prompt = f"""Task: Rewrite this Request for Order (RFO) section for a California family court.

Context:
- Motion Type: Request for Order (FL-300)
- Section: {section_name}
- Party Role: {context.get('party_role', 'Petitioner')}
- County: {context.get('county', 'California')}

User's Draft Input:
{user_input}

Supporting Facts:
- Case Number: {context.get('case_number', 'To be assigned')}
- Children: {json.dumps(context.get('children_info', []))}
- Current Orders: {context.get('existing_orders', 'None specified')}
- Changed Circumstances: {context.get('changed_circumstances', 'As described')}

{build_fact_anchor(context)}

Instructions:
1. Rewrite in formal court language appropriate for California family court
2. Organize into clear, numbered paragraphs
3. Start each factual assertion with specific dates when possible
4. Use "Petitioner/Respondent" not "I/me" (except in declarations)
5. Do NOT cite any statute, rule of court, case, or courthouse address. Do NOT reference other forms or filing fees.
6. Maintain professional, neutral tone
7. Focus on best interests of children (if applicable)
8. Keep concise and clear

Style Guidelines:
- Use active voice
- Short, clear sentences (max 25 words when possible)
- One point per paragraph
- Chronological order for facts
- Legal conclusions must follow factual basis

REDLINES (Never Include):
- Legal advice or strategy
- Speculation about other party's motives
- Inflammatory or emotional language
- Unsubstantiated claims
- References to settlement discussions
- Hearsay without proper foundation"""
        
        return prompt
    
    def _build_declaration_prompt(self, user_narrative: str, declarant_name: str) -> str:
        """Build declaration rewrite prompt"""
        prompt = f"""Task: Convert informal narrative into proper legal declaration for California court.

User's Story:
{user_narrative}

Instructions:
1. Begin with: "I, {declarant_name}, declare as follows:"
2. Convert to first person testimony
3. Number each paragraph
4. Include only facts within personal knowledge
5. Add foundation for documents mentioned
6. Organize chronologically or by topic
7. End with penalty of perjury statement

Required Declaration Ending:
"I declare under penalty of perjury under the laws of the State of California that the foregoing is true and correct. Executed on [date] at [city], California."

Style Requirements:
- Present tense for current situations
- Past tense for events
- Specific dates and times
- Names and relationships clearly stated
- Documents referenced with exhibit letters"""
        
        return prompt
    
    def _build_best_interests_prompt(
        self,
        custody_request: str,
        children_details: List[Dict]
    ) -> str:
        """Build best interests analysis prompt"""
        prompt = f"""Task: Enhance this custody/visitation request with best interests factors.

User's Request:
{custody_request}

Children's Information:
{json.dumps(children_details)}

Instructions:
Rewrite incorporating California's best interests factors:

1. Health, Safety, and Welfare
   - Physical safety concerns
   - Medical needs
   - Educational stability

2. Stability and Continuity
   - Maintaining current routines
   - School and community ties
   - Sibling relationships

3. Child's Preference (if age appropriate)
   - Note: Only if child is of sufficient age and capacity

4. Parental Fitness
   - Ability to provide for needs
   - History of involvement
   - Co-parenting ability

Format each factor as separate paragraph with supporting facts."""
        
        return prompt
    
    async def _generate(
        self,
        prompt: str,
        operation: str,
        user_id: Optional[str] = None
    ) -> tuple:
        """Generate via the configured backend. Returns (text, tokens, model_name)."""
        if self.claude_backend is not None:
            return await self.claude_backend.generate(prompt, operation, user_id)

        config = self.operation_configs.get(operation, self.generation_config)
        response = self.model.generate_content(
            prompt,
            generation_config=config,
            safety_settings=self.safety_settings
        )
        text = response.text if response.text else ""
        tokens = len(prompt.split()) + len(text.split())
        return text, tokens, settings.VERTEX_AI_MODEL

    async def rewrite_rfo_section(
        self,
        section_name: str,
        user_answers: Dict[str, Any],
        context: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rewrite an RFO section using LLM with cost controls"""
        try:
            # Check emergency shutdown
            if os.getenv("EMERGENCY_SHUTDOWN", "false").lower() == "true":
                return {
                    "success": False,
                    "error": "Service temporarily unavailable due to budget limits",
                    "rewritten_text": "",
                    "tokens_used": 0
                }

            # Combine user answers into narrative
            user_input = self._format_answers_to_narrative(user_answers)

            # Build prompt
            prompt = self._build_rfo_prompt(section_name, user_input, context)

            # Estimate tokens and check budget
            estimated_tokens = len(prompt.split()) * 2  # Conservative estimate
            budget_ok, budget_msg = await check_budget(
                estimated_tokens,
                "section_rewrite",
                user_id
            )

            if not budget_ok:
                logger.warning(f"Budget limit reached: {budget_msg}")
                return {
                    "success": False,
                    "error": budget_msg,
                    "rewritten_text": "",
                    "tokens_used": 0
                }

            # Get appropriate token limit
            token_limit = get_token_limit("section_rewrite")

            if USE_MOCK_LLM:
                # Mock mode passes the user's own words through unchanged — this text
                # lands in filing-ready PDFs, so it must never contain placeholder copy.
                rewritten_text = user_input
                tokens_used = len(prompt.split()) + len(rewritten_text.split())
                model_name = "mock-llm"
            else:
                rewritten_text, tokens_used, model_name = await self._generate(
                    prompt, "section_rewrite", user_id
                )

                # Track usage for cost monitoring
                await track_llm_cost(
                    operation="section_rewrite",
                    tokens=tokens_used,
                    user_id=user_id
                )

            return {
                "success": True,
                "rewritten_text": rewritten_text,
                "tokens_used": tokens_used,
                "model": model_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rewritten_text": "",
                "tokens_used": 0
            }
    
    async def rewrite_declaration(
        self,
        narrative: str,
        declarant_name: str,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rewrite narrative as formal declaration with cost controls"""
        try:
            # Check emergency shutdown
            if os.getenv("EMERGENCY_SHUTDOWN", "false").lower() == "true":
                return {
                    "success": False,
                    "error": "Service temporarily unavailable due to budget limits",
                    "rewritten_text": "",
                    "tokens_used": 0
                }

            prompt = self._build_declaration_prompt(narrative, declarant_name)

            # Check budget
            estimated_tokens = len(prompt.split()) * 2
            budget_ok, budget_msg = await check_budget(
                estimated_tokens,
                "declaration",
                user_id
            )

            if not budget_ok:
                return {
                    "success": False,
                    "error": budget_msg,
                    "rewritten_text": "",
                    "tokens_used": 0
                }

            if USE_MOCK_LLM:
                # Mock mode wraps the user's narrative in the standard declaration
                # skeleton — no placeholder copy, since this can land in a filed PDF.
                rewritten_text = f"""I, {declarant_name}, declare as follows:

{narrative}

I declare under penalty of perjury under the laws of the State of California that the foregoing is true and correct.


_____________________________
{declarant_name}"""
                tokens_used = len(prompt.split()) + len(rewritten_text.split())
                model_name = "mock-llm"
            else:
                rewritten_text, tokens_used, model_name = await self._generate(
                    prompt, "declaration", user_id
                )

                # Track usage
                await track_llm_cost(
                    operation="declaration",
                    tokens=tokens_used,
                    user_id=user_id
                )

            return {
                "success": True,
                "rewritten_text": rewritten_text,
                "tokens_used": tokens_used,
                "model": model_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "rewritten_text": "",
                "tokens_used": 0
            }
    
    async def enhance_best_interests(
        self,
        custody_request: str,
        children_info: List[Dict]
    ) -> Dict[str, Any]:
        """Enhance custody request with best interests factors"""
        try:
            prompt = self._build_best_interests_prompt(custody_request, children_info)

            if USE_MOCK_LLM:
                enhanced_text = f"""{custody_request}

The following California best interests factors support this request:

1. Health, safety, and welfare of the children.
2. Stability and continuity in the children's daily routine.
3. Each parent's ability to provide appropriate care."""
                tokens_used = len(prompt.split()) + len(enhanced_text.split())
                model_name = "mock-llm"
            else:
                enhanced_text, tokens_used, model_name = await self._generate(
                    prompt, "best_interests"
                )

            return {
                "success": True,
                "enhanced_text": enhanced_text,
                "tokens_used": tokens_used,
                "model": model_name
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "enhanced_text": "",
                "tokens_used": 0
            }
    
    async def process_complete_motion(
        self,
        motion_type: str,
        all_drafts: List[Dict[str, Any]],
        profile_data: Dict[str, Any],
        should_abort: Optional[Callable[[], Awaitable[bool]]] = None
    ) -> Dict[str, Any]:
        """Process complete motion through LLM for all sections"""
        results = []
        total_tokens = 0
        aborted = False

        # Build context from profile and answers
        context = {
            "party_role": "Petitioner" if profile_data.get("is_petitioner") else "Respondent",
            "county": profile_data.get("county", "California"),
            "case_number": profile_data.get("case_number", ""),
            "children_info": profile_data.get("children_info", []),
            "party_name": profile_data.get("party_name", ""),
            "other_party_name": profile_data.get("other_party_name", "")
        }
        
        # Process each draft section
        for draft in all_drafts:
            # Stop paying for sections nobody is waiting on (finding L18)
            if should_abort and await should_abort():
                aborted = True
                break
            section_name = draft.get("step_name", "")
            answers = draft.get("question_data", {})
            
            # Add answers to context for next sections
            context.update(answers)
            
            # Rewrite section
            result = await self.rewrite_rfo_section(section_name, answers, context)
            
            results.append({
                "step_number": draft.get("step_number"),
                "section": section_name,
                "original_answers": answers,
                "rewritten_text": result.get("rewritten_text", ""),
                "success": result.get("success", False),
                "error": result.get("error")
            })
            
            total_tokens += result.get("tokens_used", 0)
        
        return {
            "motion_type": motion_type,
            "sections": results,
            "total_tokens": total_tokens,
            "model": self._backend_model_name(),
            "aborted": aborted,
            "success": all(r.get("success") for r in results)
        }

    def _backend_model_name(self) -> str:
        if USE_MOCK_LLM:
            return "mock-llm"
        if self.claude_backend is not None:
            from app.services.claude_llm_service import DRAFTING_MODEL
            return DRAFTING_MODEL
        return settings.VERTEX_AI_MODEL
    
    def _format_answers_to_narrative(self, answers: Dict[str, Any]) -> str:
        """Convert Q&A answers to narrative text"""
        narrative_parts = []
        
        for key, value in answers.items():
            if value is None or value == "":
                continue
            
            # Format based on type
            if isinstance(value, bool):
                narrative_parts.append(f"{key.replace('_', ' ').title()}: {'Yes' if value else 'No'}")
            elif isinstance(value, list):
                if value:  # Only if list is not empty
                    narrative_parts.append(f"{key.replace('_', ' ').title()}: {', '.join(str(v) for v in value)}")
            elif isinstance(value, dict):
                # Handle complex objects
                narrative_parts.append(f"{key.replace('_', ' ').title()}: {json.dumps(value)}")
            else:
                # Simple string/number values
                narrative_parts.append(f"{value}")
        
        return "\n\n".join(narrative_parts)
    
    def validate_output(self, text: str) -> Dict[str, Any]:
        """Validate LLM output for quality and compliance"""
        issues = []
        
        # Check for prohibited content
        prohibited_phrases = [
            "I am not a lawyer",
            "seek legal advice",
            "this is legal advice",
            "consult an attorney"
        ]
        
        for phrase in prohibited_phrases:
            if phrase.lower() in text.lower():
                issues.append(f"Contains prohibited phrase: '{phrase}'")
        
        # Check for minimum content
        if len(text.split()) < 50:
            issues.append("Output too short (less than 50 words)")
        
        # Check for maximum content
        if len(text.split()) > 5000:
            issues.append("Output too long (more than 5000 words)")
        
        # Check for proper formatting
        if "RFO" in text or "FL-300" in text:
            if not any(char.isdigit() for char in text[:100]):
                issues.append("Missing numbered paragraphs")

        # UPL guard (PRD compliance C3): generated documents must never give
        # legal advice — flag advice-like phrasing for regeneration/review
        advice_phrases = [
            "you should",
            "i recommend",
            "i advise",
            "i suggest",
            "your best option",
            "the best thing to do",
            "you need to file",
        ]
        upl_flags = [
            f"Advice-like phrasing (UPL risk): '{phrase}'"
            for phrase in advice_phrases
            if phrase in text.lower()
        ]
        issues.extend(upl_flags)

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "upl_flags": upl_flags
        }

    async def enhance_declaration(
        self,
        text: str,
        formal: bool = True,
        legal_tone: bool = True,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhance a declaration by delegating to rewrite_declaration."""
        result = await self.rewrite_declaration(
            narrative=text,
            declarant_name="Declarant",
            user_id=user_id
        )
        # Expose result under 'enhanced_text' key for callers that expect it
        result["enhanced_text"] = result.get("rewritten_text", "")
        return result

# Singleton instance
llm_service = LLMService()