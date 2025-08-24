"""
RFO Intake service for guided Q&A flow
"""
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

class IntakeService:
    def __init__(self):
        # Load RFO questions from JSON file
        questions_path = Path(__file__).parent.parent.parent / "rfo-questions.json"
        with open(questions_path, 'r') as f:
            self.questions_data = json.load(f)
        self.rfo_flow = self.questions_data["rfo_intake_flow"]
    
    def get_all_steps(self) -> List[Dict]:
        """Get all intake steps with their questions"""
        return self.rfo_flow["steps"]
    
    def get_step(self, step_number: int) -> Optional[Dict]:
        """Get a specific step by number"""
        steps = self.rfo_flow["steps"]
        for step in steps:
            if step["step"] == step_number:
                return step
        return None
    
    def evaluate_condition(self, condition: str, answers: Dict[str, Any]) -> bool:
        """Evaluate whether a conditional question/step should be shown"""
        if not condition:
            return True
        
        # Simple condition evaluation
        # Examples: "has_existing_case == true", "relief_categories.includes('custody')"
        try:
            if ".includes(" in condition:
                # Handle array includes condition
                parts = condition.split(".includes(")
                field_name = parts[0]
                value = parts[1].strip(")'\"")
                field_value = answers.get(field_name, [])
                return value in field_value if isinstance(field_value, list) else False
            elif "==" in condition:
                # Handle equality condition
                parts = condition.split("==")
                field_name = parts[0].strip()
                expected_value = parts[1].strip().strip("'\"")
                actual_value = answers.get(field_name)
                
                # Convert string booleans to actual booleans
                if expected_value == "true":
                    expected_value = True
                elif expected_value == "false":
                    expected_value = False
                    
                return str(actual_value).lower() == str(expected_value).lower()
            elif "||" in condition:
                # Handle OR conditions
                sub_conditions = condition.split("||")
                return any(self.evaluate_condition(sub.strip(), answers) for sub in sub_conditions)
            
            return True
        except:
            # If condition evaluation fails, show the question/step
            return True
    
    def get_next_step(self, current_step: int, answers: Dict[str, Any]) -> Optional[Dict]:
        """Get the next applicable step based on answers"""
        steps = self.rfo_flow["steps"]
        
        # Find the next step that meets conditions
        for step in steps:
            if step["step"] > current_step:
                # Check if step has a condition
                if "condition" in step:
                    if self.evaluate_condition(step["condition"], answers):
                        return step
                else:
                    return step
        
        return None
    
    def get_applicable_questions(self, step: Dict, answers: Dict[str, Any]) -> List[Dict]:
        """Get only the questions that should be shown based on conditions"""
        applicable_questions = []
        
        for question in step.get("questions", []):
            if "condition" in question:
                if self.evaluate_condition(question["condition"], answers):
                    applicable_questions.append(question)
            else:
                applicable_questions.append(question)
        
        return applicable_questions
    
    def validate_answers(self, step: Dict, answers: Dict[str, Any]) -> Dict[str, str]:
        """Validate answers for a given step"""
        errors = {}
        questions = step.get("questions", [])
        
        for question in questions:
            q_id = question["id"]
            
            # Skip conditional questions that don't apply
            if "condition" in question:
                if not self.evaluate_condition(question["condition"], answers):
                    continue
            
            # Check required fields
            if question.get("required", False):
                if q_id not in answers or answers[q_id] is None or answers[q_id] == "":
                    errors[q_id] = f"{question['text']} is required"
                    continue
            
            # Type-specific validation
            if q_id in answers and answers[q_id] is not None:
                value = answers[q_id]
                
                if question["type"] == "number":
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors[q_id] = "Must be a valid number"
                
                elif question["type"] == "checkbox_group":
                    if not isinstance(value, list):
                        errors[q_id] = "Must select at least one option"
                    elif question.get("min_selections"):
                        if len(value) < question["min_selections"]:
                            errors[q_id] = f"Must select at least {question['min_selections']} option(s)"
                
                elif question["type"] == "text" and "validation" in question:
                    # Handle pattern validation
                    if question["validation"].startswith("pattern:"):
                        import re
                        pattern = question["validation"].replace("pattern:", "")
                        if not re.match(pattern, str(value)):
                            errors[q_id] = f"Invalid format. Expected format: {question.get('placeholder', pattern)}"
                
                elif question["type"] == "textarea" and "max_length" in question:
                    if len(str(value)) > question["max_length"]:
                        errors[q_id] = f"Maximum {question['max_length']} characters allowed"
        
        return errors
    
    def get_required_attachments(self, relief_categories: List[str]) -> List[str]:
        """Get list of required attachments based on relief requested"""
        attachments = []
        rules = self.rfo_flow.get("validation_rules", {}).get("required_attachments", {})
        
        for category in relief_categories:
            if category in rules:
                attachments.extend(rules[category])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_attachments = []
        for item in attachments:
            if item not in seen:
                seen.add(item)
                unique_attachments.append(item)
        
        return unique_attachments
    
    def calculate_progress(self, completed_steps: List[int], answers: Dict[str, Any]) -> float:
        """Calculate completion progress percentage"""
        all_steps = self.rfo_flow["steps"]
        applicable_steps = []
        
        # Determine which steps apply based on conditions
        for step in all_steps:
            if "condition" in step:
                if self.evaluate_condition(step["condition"], answers):
                    applicable_steps.append(step["step"])
            else:
                applicable_steps.append(step["step"])
        
        if not applicable_steps:
            return 0.0
        
        completed_applicable = [s for s in completed_steps if s in applicable_steps]
        return (len(completed_applicable) / len(applicable_steps)) * 100

# Singleton instance
intake_service = IntakeService()