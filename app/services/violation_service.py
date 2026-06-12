"""
Service for handling San Diego Family Court violation filings
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import logging

from app.services.pdf_service import PDFService
from app.services.llm_service import LLMService
from app.models.motion import Motion, MotionType

logger = logging.getLogger(__name__)

class ViolationFilingService:
    """Handle violation filing forms and workflows for San Diego County"""

    def __init__(self):
        self.pdf_service = PDFService()
        self.llm_service = LLMService()
        self.forms_dir = Path("forms/san-diego-violation")
        self.config = self._load_config()

    def _load_config(self) -> Dict:
        """Load the violation filing configuration"""
        config_path = self.forms_dir / "form-config.json"
        if config_path.exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        return {}

    def determine_filing_track(self, intake_data: Dict) -> str:
        """
        Determine which filing track to use based on intake answers

        Returns: 'emergency', 'regular', or 'contempt'
        """
        is_emergency = intake_data.get("urgency", False)
        violation_type = intake_data.get("violationType", "")
        requested_relief = intake_data.get("requestedRelief", [])

        # Emergency track if urgent or restraining order violation
        if is_emergency or violation_type == "Restraining Order":
            return "emergency"

        # Contempt track if specifically requesting contempt finding
        if "Find party in contempt" in requested_relief:
            return "contempt"

        # Default to regular track
        return "regular"

    def get_required_forms(self, track: str) -> List[Dict]:
        """Get list of required forms for the filing track"""
        forms = []
        track_config = None

        # Find the track configuration
        for t in self.config.get("violationFiling", {}).get("tracks", []):
            if t["id"] == track:
                track_config = t
                break

        if not track_config:
            return forms

        # Get form details for required forms
        all_forms = self.config.get("violationFiling", {}).get("forms", [])
        for form_id in track_config.get("requiredForms", []):
            form = next((f for f in all_forms if f["id"] == form_id), None)
            if form:
                forms.append({
                    "id": form["id"],
                    "name": form["name"],
                    "description": form["description"],
                    "fileName": form["fileName"],
                    "required": True
                })

        # Add optional forms
        for form_id in track_config.get("optionalForms", []):
            form = next((f for f in all_forms if f["id"] == form_id), None)
            if form:
                forms.append({
                    "id": form["id"],
                    "name": form["name"],
                    "description": form["description"],
                    "fileName": form["fileName"],
                    "required": False
                })

        return forms

    def prepare_declaration(self, intake_data: Dict) -> str:
        """
        Prepare the declaration text for MC-030 based on intake data
        """
        declaration_parts = []

        # Header
        declaration_parts.append("DECLARATION IN SUPPORT OF REQUEST FOR ORDER\n")

        # Basic violation information
        violation_type = intake_data.get("violationType", "court order")
        violation_dates = intake_data.get("violationDates", [])
        violation_desc = intake_data.get("violationDescription", "")

        declaration_parts.append(f"1. VIOLATION OF {violation_type.upper()} ORDER")
        declaration_parts.append(f"\nThe Respondent has violated the court's {violation_type} order as follows:\n")

        # Add violation dates
        if violation_dates:
            declaration_parts.append("Dates of violation:")
            for date in violation_dates:
                declaration_parts.append(f"  - {date}")
            declaration_parts.append("")

        # Add detailed description
        declaration_parts.append("2. DETAILS OF VIOLATION\n")
        declaration_parts.append(violation_desc)
        declaration_parts.append("")

        # Evidence
        evidence = intake_data.get("evidence", [])
        if evidence:
            declaration_parts.append("3. EVIDENCE\n")
            declaration_parts.append("I have the following evidence of the violation:")
            for item in evidence:
                declaration_parts.append(f"  - {item}")
            declaration_parts.append("")

        # Prior violations
        if intake_data.get("priorViolations"):
            prior_desc = intake_data.get("priorViolationsDescription", "")
            declaration_parts.append("4. HISTORY OF VIOLATIONS\n")
            declaration_parts.append("This is not the first violation by the Respondent.")
            declaration_parts.append(prior_desc)
            declaration_parts.append("")

        # Attempted resolution
        if intake_data.get("attemptedResolution"):
            resolution_desc = intake_data.get("resolutionDescription", "")
            declaration_parts.append("5. ATTEMPTS TO RESOLVE\n")
            declaration_parts.append("I attempted to resolve this matter without court intervention:")
            declaration_parts.append(resolution_desc)
            declaration_parts.append("")

        # Requested relief
        requested_relief = intake_data.get("requestedRelief", [])
        if requested_relief:
            declaration_parts.append("6. REQUESTED RELIEF\n")
            declaration_parts.append("I respectfully request the court:")
            for relief in requested_relief:
                declaration_parts.append(f"  - {relief}")
            declaration_parts.append("")

        # Footer
        declaration_parts.append("\nI declare under penalty of perjury under the laws of the State of California ")
        declaration_parts.append("that the foregoing is true and correct.")

        return "\n".join(declaration_parts)

    async def process_violation_filing(
        self,
        user_id: str,
        intake_data: Dict,
        profile_data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Process a complete violation filing

        Returns dict with:
        - track: Filing track determined
        - forms: List of forms to complete
        - declaration: Generated declaration text
        - instructions: Next steps for filing
        """
        try:
            # Determine filing track
            track = self.determine_filing_track(intake_data)

            # Get required forms
            forms = self.get_required_forms(track)

            # Prepare declaration
            declaration_text = self.prepare_declaration(intake_data)

            # Enhance declaration with LLM
            enhanced_declaration = await self.llm_service.enhance_declaration(
                declaration_text,
                formal=True,
                legal_tone=True
            )

            # Get track configuration for instructions
            track_config = next(
                (t for t in self.config.get("violationFiling", {}).get("tracks", [])
                 if t["id"] == track),
                None
            )

            # Prepare filing instructions
            instructions = self._generate_filing_instructions(
                track,
                track_config,
                intake_data
            )

            # Determine courthouse based on user location or preference
            courthouse = self._determine_courthouse(profile_data)

            return {
                "success": True,
                "track": track,
                "trackName": track_config.get("name", track.title()) if track_config else track.title(),
                "timeline": track_config.get("timeline", "Unknown") if track_config else "Unknown",
                "forms": forms,
                "declaration": enhanced_declaration.get("enhanced_text", declaration_text),
                "courthouse": courthouse,
                "instructions": instructions,
                "filingFee": self._get_filing_fee(track),
                "serviceRequirements": self._get_service_requirements(track)
            }

        except Exception as e:
            logger.error(f"Error processing violation filing: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _generate_filing_instructions(
        self,
        track: str,
        track_config: Optional[Dict],
        intake_data: Dict
    ) -> List[str]:
        """Generate step-by-step filing instructions"""
        instructions = []

        if track == "emergency":
            instructions.extend([
                "1. Complete all forms TODAY - this is time-sensitive",
                "2. Notify opposing party by 10 AM the day before filing (or explain why notice wasn't given)",
                "3. Make 3 copies of all documents",
                "4. File at the courthouse clerk's office",
                "5. Get hearing date (usually within 24-48 hours)",
                "6. Attend hearing - judge will decide immediately"
            ])
        elif track == "regular":
            instructions.extend([
                "1. Complete all required forms",
                "2. Make 3 copies of all documents",
                "3. File original with court clerk",
                "4. Pay filing fee (or request fee waiver)",
                "5. Get hearing date (3-6 weeks out)",
                "6. Serve opposing party within 5 days",
                "7. File proof of service",
                "8. Prepare for hearing"
            ])
        elif track == "contempt":
            instructions.extend([
                "1. Complete FL-410 with detailed violation information",
                "2. Attach all evidence of violation",
                "3. File with court clerk",
                "4. Court reviews and issues FL-411 if approved",
                "5. PERSONALLY serve opposing party (mail not acceptable)",
                "6. File proof of personal service",
                "7. Prepare for contempt hearing (quasi-criminal proceeding)",
                "8. Opposing party may face jail time if found in contempt"
            ])

        return instructions

    def _determine_courthouse(self, profile_data: Optional[Dict]) -> Dict:
        """Determine which courthouse to file at based on user location"""
        courthouses = self.config.get("violationFiling", {}).get("courthouses", [])

        # Default to Central Division
        default = courthouses[0] if courthouses else {
            "name": "Central Division",
            "address": "1100 Union St., San Diego, CA 92101"
        }

        if not profile_data:
            return default

        # Logic to determine courthouse based on zip code or city
        city = profile_data.get("city", "").lower()
        zip_code = profile_data.get("zipCode", "")

        # Simple mapping - can be enhanced
        if "el cajon" in city or zip_code.startswith("920"):
            return courthouses[1] if len(courthouses) > 1 else default
        elif "vista" in city or "oceanside" in city or zip_code.startswith("920"):
            return courthouses[2] if len(courthouses) > 2 else default
        elif "chula vista" in city or "national city" in city:
            return courthouses[3] if len(courthouses) > 3 else default

        return default

    def _get_filing_fee(self, track: str) -> str:
        """Get filing fee information"""
        fees = {
            "emergency": "$60-90 (Ex Parte fee)",
            "regular": "$60 (Request for Order)",
            "contempt": "$60 (Order to Show Cause)"
        }
        return fees.get(track, "$60")

    def _get_service_requirements(self, track: str) -> Dict:
        """Get service requirements for the track"""
        requirements = {
            "emergency": {
                "method": "Personal or phone notice",
                "timeline": "By 10 AM day before filing",
                "proofRequired": True
            },
            "regular": {
                "method": "Personal service or mail",
                "timeline": "16 court days before hearing",
                "proofRequired": True
            },
            "contempt": {
                "method": "PERSONAL SERVICE ONLY",
                "timeline": "At least 10 days before hearing",
                "proofRequired": True,
                "note": "Mail service NOT acceptable for contempt"
            }
        }
        return requirements.get(track, {})