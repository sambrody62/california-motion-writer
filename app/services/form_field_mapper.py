"""
Service to map conversation data to form fields for PDF generation
"""
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Import the comprehensive court forms mapping
try:
    from app.services.court_forms_mapping import court_forms_mapping, FormType
    HAS_COURT_FORMS = True
except ImportError:
    HAS_COURT_FORMS = False
    logger.warning("Court forms mapping not available, using legacy mappings")

class FormFieldMapper:
    """Maps conversational data to specific form fields"""

    def __init__(self):
        # Use new comprehensive mappings if available, otherwise fall back to legacy
        if HAS_COURT_FORMS:
            self.court_forms = court_forms_mapping
        else:
            self.court_forms = None

        # Define form field mappings for each form type
        self.form_mappings = self._initialize_form_mappings()

    def _initialize_form_mappings(self) -> Dict:
        """Initialize mappings between conversation fields and PDF form fields"""

        mappings = {}

        # FL-300 (Request for Order) field mappings
        mappings["FL-300"] = {
            "petitioner_name": ["party_name", "your_name", "petitioner"],
            "respondent_name": ["other_party_name", "ex_name", "respondent"],
            "case_number": ["case_number", "case_no"],
            "request_emergency_orders": ["is_emergency", "emergency_order"],

            # Custody section
            "child_custody_requested": ["requested_custody_arrangement", "custody_request"],
            "legal_custody_to": ["legal_custody_request"],
            "physical_custody_to": ["physical_custody_request"],
            "visitation_schedule": ["requested_visitation", "visitation_request"],

            # Support section
            "child_support_requested": ["child_support", "support_request"],
            "spousal_support_requested": ["spousal_support"],
            "current_support_amount": ["current_support_amount", "existing_support"],
            "requested_support_amount": ["requested_support_amount", "new_support"],

            # Other orders
            "property_control": ["property_orders"],
            "attorney_fees": ["attorney_fee_request"],
            "other_relief": ["other_requests", "additional_orders"]
        }

        # FL-320 (Response to Request for Order)
        mappings["FL-320"] = {
            "petitioner_name": ["other_party_name", "petitioner"],
            "respondent_name": ["party_name", "your_name", "respondent"],
            "case_number": ["case_number"],

            "agree_to_request": ["agree_with_request", "consent"],
            "disagree_to_request": ["disagree", "contest"],
            "request_different_order": ["counter_request", "alternative_proposal"],

            "response_reasons": ["response_explanation", "disagreement_reasons"],
            "counter_proposal": ["alternative_request", "different_orders"]
        }

        # FL-311 (Child Custody and Visitation Application)
        mappings["FL-311"] = {
            "children_names": ["children_info.names", "child_names"],
            "children_birthdates": ["children_info.birthdates", "child_dobs"],
            "current_living_with": ["current_custody", "children_residence"],

            "requested_legal_custody": ["legal_custody_request"],
            "requested_physical_custody": ["physical_custody_request"],
            "visitation_proposal": ["visitation_schedule", "parenting_plan"],

            "best_interest_factors": ["best_interest_reasons", "custody_reasons"],
            "child_preference": ["child_preference", "child_wishes"],
            "safety_concerns": ["safety_concerns", "domestic_violence"]
        }

        # MC-030 (Declaration)
        mappings["MC-030"] = {
            "declarant_name": ["party_name", "your_name"],
            "declaration_facts": ["declaration_text", "statement", "facts"],
            "exhibits_referenced": ["exhibits", "attachments"],
            "date_signed": ["signature_date", "date"],
            "location_signed": ["signature_location", "city", "county"]
        }

        return mappings

    def map_conversation_to_form(
        self,
        form_type: str,
        conversation_data: Dict[str, Any],
        profile_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Map conversation data to specific form fields

        Args:
            form_type: Type of form (FL-300, FL-320, etc.)
            conversation_data: Data extracted from conversation
            profile_data: User profile data to supplement

        Returns:
            Dictionary with form field names as keys
        """
        if form_type not in self.form_mappings:
            logger.warning(f"No mapping found for form type: {form_type}")
            return {}

        form_fields = {}
        mapping = self.form_mappings[form_type]

        # Combine data sources (conversation takes priority)
        combined_data = {}
        if profile_data:
            combined_data.update(profile_data)
        combined_data.update(conversation_data)

        # Map each form field
        for form_field, possible_sources in mapping.items():
            value = self._extract_field_value(possible_sources, combined_data)
            if value is not None:
                form_fields[form_field] = value

        # Post-process and validate
        form_fields = self._post_process_fields(form_type, form_fields)

        return form_fields

    def _extract_field_value(
        self,
        possible_sources: List[str],
        data: Dict[str, Any]
    ) -> Any:
        """Extract field value from possible source fields"""

        for source in possible_sources:
            # Handle nested fields (e.g., "children_info.names")
            if "." in source:
                parts = source.split(".")
                value = data
                for part in parts:
                    if isinstance(value, dict) and part in value:
                        value = value[part]
                    else:
                        value = None
                        break
                if value is not None:
                    return value
            else:
                # Direct field lookup
                if source in data:
                    return data[source]

        return None

    def _post_process_fields(
        self,
        form_type: str,
        fields: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post-process fields for specific form requirements"""

        # Format dates
        for key, value in fields.items():
            if "date" in key.lower() and value:
                fields[key] = self._format_date(value)

        # Format money amounts
        for key, value in fields.items():
            if "amount" in key.lower() and value:
                fields[key] = self._format_money(value)

        # Handle checkboxes (convert booleans)
        for key, value in fields.items():
            if isinstance(value, bool):
                fields[key] = "X" if value else ""

        # Form-specific processing
        if form_type == "FL-300":
            fields = self._process_fl300_fields(fields)
        elif form_type == "FL-320":
            fields = self._process_fl320_fields(fields)

        return fields

    def _format_date(self, date_value: Any) -> str:
        """Format date for form fields"""
        if isinstance(date_value, datetime):
            return date_value.strftime("%m/%d/%Y")
        elif isinstance(date_value, str):
            # Try to parse and reformat
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"]:
                try:
                    dt = datetime.strptime(date_value, fmt)
                    return dt.strftime("%m/%d/%Y")
                except ValueError:
                    continue
        return str(date_value)

    def _format_money(self, amount: Any) -> str:
        """Format money amounts for form fields"""
        if isinstance(amount, (int, float)):
            return f"${amount:,.2f}"
        elif isinstance(amount, str):
            # Clean and format
            cleaned = re.sub(r'[^\d.]', '', amount)
            try:
                num = float(cleaned)
                return f"${num:,.2f}"
            except ValueError:
                return amount
        return str(amount)

    def _process_fl300_fields(self, fields: Dict) -> Dict:
        """Special processing for FL-300 form"""

        # Combine custody fields if separate
        if "legal_custody_to" in fields and "physical_custody_to" in fields:
            if fields["legal_custody_to"] == fields["physical_custody_to"]:
                fields["sole_custody_to"] = fields["legal_custody_to"]
            else:
                fields["joint_custody"] = True

        # Set emergency checkbox if needed
        if fields.get("request_emergency_orders"):
            fields["emergency_orders_checkbox"] = "X"

        return fields

    def _process_fl320_fields(self, fields: Dict) -> Dict:
        """Special processing for FL-320 form"""

        # Set appropriate response checkboxes
        if fields.get("agree_to_request"):
            fields["agree_checkbox"] = "X"
        if fields.get("disagree_to_request"):
            fields["disagree_checkbox"] = "X"
        if fields.get("request_different_order"):
            fields["different_order_checkbox"] = "X"

        return fields

    def validate_required_fields(
        self,
        form_type: str,
        form_fields: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all required fields are present

        Returns:
            (is_valid, list_of_missing_required_fields)
        """
        required_fields = self._get_required_fields(form_type)
        missing = []

        for field in required_fields:
            if field not in form_fields or not form_fields[field]:
                missing.append(field)

        return len(missing) == 0, missing

    def _get_required_fields(self, form_type: str) -> List[str]:
        """Get list of required fields for a form type"""

        required = {
            "FL-300": [
                "petitioner_name",
                "respondent_name",
                "case_number"
                # At least one type of order must be requested
            ],
            "FL-320": [
                "petitioner_name",
                "respondent_name",
                "case_number"
                # Must indicate agree/disagree
            ],
            "FL-311": [
                "children_names",
                "children_birthdates",
                "requested_legal_custody",
                "requested_physical_custody"
            ],
            "MC-030": [
                "declarant_name",
                "declaration_facts",
                "date_signed"
            ]
        }

        return required.get(form_type, [])

    def get_missing_information(
        self,
        form_type: str,
        conversation_data: Dict[str, Any],
        profile_data: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """
        Identify what information is still needed for the form

        Returns:
            List of dictionaries with field_name and question to ask
        """
        # Use new comprehensive mapping if available
        if HAS_COURT_FORMS and self.court_forms:
            return self._get_missing_with_court_forms(form_type, conversation_data, profile_data or {})

        # Fall back to legacy method
        required = self._get_required_fields(form_type)
        mapped = self.map_conversation_to_form(form_type, conversation_data, profile_data or {})

        missing = []
        for field in required:
            if field not in mapped or not mapped[field]:
                missing.append({
                    "field_name": field,
                    "question": self._get_question_for_field(field)
                })

        return missing

    def _get_question_for_field(self, field_name: str) -> str:
        """Generate a question for a missing field"""

        questions = {
            "petitioner_name": "What is the petitioner's full legal name?",
            "respondent_name": "What is the respondent's full legal name?",
            "case_number": "What is your case number?",
            "children_names": "What are the full names of the children?",
            "children_birthdates": "What are the birthdates of the children?",
            "requested_custody_arrangement": "What custody arrangement are you requesting?",
            "current_support_amount": "What is the current support amount?",
            "requested_support_amount": "What support amount are you requesting?",
            "declaration_facts": "What facts do you need to declare?",
            "date_signed": "What is today's date?",
            "declarant_name": "What is your full legal name?"
        }

        return questions.get(field_name, f"Please provide: {field_name.replace('_', ' ').title()}")

    def _get_missing_with_court_forms(
        self,
        form_type: str,
        conversation_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Use comprehensive court forms mapping to identify missing information"""

        # Convert string form type to enum
        form_type_enum = self._get_form_type_enum(form_type)
        if not form_type_enum:
            return []

        # Use the comprehensive mapping
        mapped_data = self.court_forms.map_conversation_to_form(
            form_type_enum,
            conversation_data,
            profile_data
        )

        # Validate and get missing fields
        is_valid, missing_fields = self.court_forms.validate_form_data(
            form_type_enum,
            mapped_data
        )

        # Convert missing fields to questions
        missing = []
        form_fields = self.court_forms.form_definitions.get(form_type_enum, {})

        for field_name in missing_fields:
            field_def = form_fields.get(field_name)
            if field_def:
                missing.append({
                    "field_name": field_name,
                    "question": field_def.description or self._get_question_for_field(field_name),
                    "field_type": field_def.field_type,
                    "required": field_def.required
                })

        return missing

    def _get_form_type_enum(self, form_type_str: str):
        """Convert string form type to FormType enum"""
        if not HAS_COURT_FORMS:
            return None

        # Map string representations to enum values
        form_map = {
            "FL-300": FormType.FL300,
            "FL-150": FormType.FL150,
            "FL-305": FormType.FL305,
            "FL-335": FormType.FL335,
            "FL-410": FormType.FL410,
            "FL-411": FormType.FL411,
            "MC-030": FormType.MC030,
            "D-046": FormType.D046,
            "SDSC D-046": FormType.D046,
        }

        return form_map.get(form_type_str)

    def map_to_comprehensive_forms(
        self,
        form_type: str,
        conversation_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Map data using comprehensive court forms mapping"""

        if not HAS_COURT_FORMS or not self.court_forms:
            # Fall back to legacy mapping
            return self.map_conversation_to_form(form_type, conversation_data, profile_data)

        form_type_enum = self._get_form_type_enum(form_type)
        if not form_type_enum:
            # Fall back to legacy mapping
            return self.map_conversation_to_form(form_type, conversation_data, profile_data)

        # Use comprehensive mapping
        return self.court_forms.map_conversation_to_form(
            form_type_enum,
            conversation_data,
            profile_data
        )

    def get_supported_forms(self) -> List[str]:
        """Get list of all supported court forms"""

        forms = []

        # Add legacy forms
        forms.extend(["FL-300", "FL-320", "FL-311", "FL-150", "MC-030"])

        # Add comprehensive forms if available
        if HAS_COURT_FORMS and self.court_forms:
            comprehensive_forms = ["D-046", "FL-305", "FL-335", "FL-410", "FL-411"]
            forms.extend(comprehensive_forms)

        # Remove duplicates and sort
        return sorted(list(set(forms)))

# Singleton instance
form_mapper = FormFieldMapper()