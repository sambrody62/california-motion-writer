"""
Vertex AI LLM Service for GCP integration
"""
import os
import json
from typing import Dict, Any, Optional
from vertexai import init
from vertexai.generative_models import GenerativeModel, ChatSession
import vertexai.preview.generative_models as generative_models

class VertexLLMService:
    def __init__(self):
        # Initialize Vertex AI with project and location
        project = os.getenv("GOOGLE_CLOUD_PROJECT", "california-motion-writer")
        location = os.getenv("VERTEX_AI_LOCATION", "us-central1")

        init(project=project, location=location)

        # Use Gemini 1.5 Pro model
        self.model = GenerativeModel("gemini-1.5-pro-001")

        # Safety settings
        self.safety_settings = {
            generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }

        # Generation config
        self.generation_config = {
            "max_output_tokens": 2048,
            "temperature": 0.7,
            "top_p": 0.95,
        }

    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using Vertex AI"""
        try:
            # Build the full prompt with system context
            full_prompt = f"""You are a legal writing assistant specializing in California family law.
            Help users understand what forms they need and create a legal strategy.
            Be helpful but do not provide legal advice.

            User Query: {prompt}"""

            # Generate response
            responses = self.model.generate_content(
                contents=[full_prompt],
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                stream=False
            )

            # Extract text from response
            if responses and responses.text:
                return responses.text
            else:
                return "I apologize, but I couldn't generate a proper response. Please try rephrasing your question."

        except Exception as e:
            print(f"Error calling Vertex AI: {e}")
            return f"Error generating response: {str(e)}"

    def analyze_case(self, case_description: str) -> Dict[str, Any]:
        """Analyze a case and recommend forms"""
        prompt = f"""
        Analyze this California family law case and provide:
        1. A brief legal situation analysis
        2. Recommended legal strategy
        3. Which California court forms are needed (from: FL-300, FL-320, FL-305, FL-150, FL-335, FL-410, FL-411, MC-030)
        4. Timeline recommendations
        5. Key considerations
        6. Next steps

        Case Description:
        {case_description}

        Provide a structured response with clear sections.
        """

        response = self.generate_response(prompt)

        # Parse response to extract forms (simple pattern matching)
        forms = []
        form_codes = ['FL-300', 'FL-320', 'FL-305', 'FL-150', 'FL-335', 'FL-410', 'FL-411', 'MC-030']
        for code in form_codes:
            if code in response:
                forms.append(code)

        if not forms:
            forms = ['FL-300']  # Default to Request for Order

        return {
            "analysis": response,
            "recommended_forms": forms,
            "raw_response": response
        }

    def create_chat_session(self) -> ChatSession:
        """Create a new chat session for conversational interactions"""
        return self.model.start_chat(history=[])

    def send_chat_message(self, session: ChatSession, message: str) -> str:
        """Send a message in an existing chat session"""
        try:
            response = session.send_message(
                message,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            return response.text if response and response.text else "Unable to generate response."
        except Exception as e:
            print(f"Error in chat session: {e}")
            return f"Error: {str(e)}"