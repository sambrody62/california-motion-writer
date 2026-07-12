"""
OpenAI LLM Service for local development with API key
"""
import os
import json
from typing import Dict, Any, Optional
import openai
from openai import OpenAI

class OpenAILLMService:
    def __init__(self):
        # Get API key from environment variable
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")  # or "gpt-4"

    def generate_response(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """Generate response using OpenAI API"""
        try:
            # Build messages for chat completion
            messages = [
                {
                    "role": "system",
                    "content": """You are a legal writing assistant specializing in California family law.
                    Help users understand what forms they need and create a legal strategy.
                    Be helpful but do not provide legal advice."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            # Fallback to mock response
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