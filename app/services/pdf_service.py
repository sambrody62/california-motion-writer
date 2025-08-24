"""
PDF Service for filling official California court forms
"""
import os
import io
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import PyPDF2
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
import json

from app.core.config import settings

class PDFService:
    def __init__(self):
        # Path to blank form templates
        self.forms_path = Path(__file__).parent.parent.parent / "forms"
        
        # Form field mappings for each form type
        self.form_fields = {
            "FL-300": self._get_fl300_fields(),
            "FL-320": self._get_fl320_fields(),
            "FL-311": self._get_fl311_fields(),
            "FL-150": self._get_fl150_fields()
        }
    
    def _get_fl300_fields(self) -> Dict[str, Dict]:
        """Field mappings for FL-300 Request for Order form"""
        return {
            # Page 1 - Header
            "attorney_name": {"page": 0, "x": 100, "y": 720, "type": "text"},
            "attorney_bar": {"page": 0, "x": 400, "y": 720, "type": "text"},
            "attorney_firm": {"page": 0, "x": 100, "y": 700, "type": "text"},
            "attorney_address": {"page": 0, "x": 100, "y": 680, "type": "text"},
            "attorney_phone": {"page": 0, "x": 100, "y": 660, "type": "text"},
            "attorney_email": {"page": 0, "x": 100, "y": 640, "type": "text"},
            "attorney_for": {"page": 0, "x": 100, "y": 620, "type": "text"},
            
            # Court info
            "court_name": {"page": 0, "x": 100, "y": 580, "type": "text"},
            "court_address": {"page": 0, "x": 100, "y": 560, "type": "text"},
            "court_city": {"page": 0, "x": 100, "y": 540, "type": "text"},
            
            # Case caption
            "petitioner_name": {"page": 0, "x": 100, "y": 500, "type": "text"},
            "respondent_name": {"page": 0, "x": 100, "y": 480, "type": "text"},
            "case_number": {"page": 0, "x": 400, "y": 500, "type": "text"},
            
            # Hearing info
            "hearing_date": {"page": 0, "x": 100, "y": 420, "type": "text"},
            "hearing_time": {"page": 0, "x": 250, "y": 420, "type": "text"},
            "hearing_dept": {"page": 0, "x": 350, "y": 420, "type": "text"},
            "hearing_room": {"page": 0, "x": 450, "y": 420, "type": "text"},
            
            # Page 2 - Requests (checkboxes and text fields)
            # Child Custody
            "request_custody": {"page": 1, "x": 50, "y": 650, "type": "checkbox"},
            "legal_custody_petitioner": {"page": 1, "x": 100, "y": 630, "type": "checkbox"},
            "legal_custody_respondent": {"page": 1, "x": 200, "y": 630, "type": "checkbox"},
            "legal_custody_joint": {"page": 1, "x": 300, "y": 630, "type": "checkbox"},
            "physical_custody_petitioner": {"page": 1, "x": 100, "y": 610, "type": "checkbox"},
            "physical_custody_respondent": {"page": 1, "x": 200, "y": 610, "type": "checkbox"},
            "physical_custody_joint": {"page": 1, "x": 300, "y": 610, "type": "checkbox"},
            
            # Child Support
            "request_child_support": {"page": 1, "x": 50, "y": 550, "type": "checkbox"},
            "child_support_amount": {"page": 1, "x": 150, "y": 530, "type": "text"},
            "child_support_payee": {"page": 1, "x": 250, "y": 530, "type": "text"},
            
            # Spousal Support
            "request_spousal_support": {"page": 1, "x": 50, "y": 480, "type": "checkbox"},
            "spousal_support_amount": {"page": 1, "x": 150, "y": 460, "type": "text"},
            "spousal_support_payee": {"page": 1, "x": 250, "y": 460, "type": "text"},
            
            # Attorney Fees
            "request_attorney_fees": {"page": 1, "x": 50, "y": 410, "type": "checkbox"},
            "attorney_fees_amount": {"page": 1, "x": 150, "y": 390, "type": "text"},
            
            # Other orders
            "request_other": {"page": 1, "x": 50, "y": 340, "type": "checkbox"},
            "other_orders_text": {"page": 1, "x": 100, "y": 320, "type": "multiline", "width": 400, "height": 100},
            
            # Page 3+ - Facts and Declarations
            "facts_text": {"page": 2, "x": 72, "y": 700, "type": "multiline", "width": 468, "height": 600},
            
            # Signature
            "signature_date": {"page": -1, "x": 100, "y": 100, "type": "text"},
            "signature_name": {"page": -1, "x": 100, "y": 80, "type": "text"},
            "signature_title": {"page": -1, "x": 100, "y": 60, "type": "text"}
        }
    
    def _get_fl320_fields(self) -> Dict[str, Dict]:
        """Field mappings for FL-320 Response to Request for Order"""
        return {
            # Similar structure to FL-300 but for response
            # Header fields (same as FL-300)
            "attorney_name": {"page": 0, "x": 100, "y": 720, "type": "text"},
            "attorney_bar": {"page": 0, "x": 400, "y": 720, "type": "text"},
            "court_name": {"page": 0, "x": 100, "y": 580, "type": "text"},
            "petitioner_name": {"page": 0, "x": 100, "y": 500, "type": "text"},
            "respondent_name": {"page": 0, "x": 100, "y": 480, "type": "text"},
            "case_number": {"page": 0, "x": 400, "y": 500, "type": "text"},
            
            # Response checkboxes
            "agree_all": {"page": 1, "x": 50, "y": 650, "type": "checkbox"},
            "disagree_all": {"page": 1, "x": 150, "y": 650, "type": "checkbox"},
            "agree_part": {"page": 1, "x": 250, "y": 650, "type": "checkbox"},
            
            # Response text
            "response_text": {"page": 1, "x": 72, "y": 600, "type": "multiline", "width": 468, "height": 500},
            
            # Signature
            "signature_date": {"page": -1, "x": 100, "y": 100, "type": "text"},
            "signature_name": {"page": -1, "x": 100, "y": 80, "type": "text"}
        }
    
    def _get_fl311_fields(self) -> Dict[str, Dict]:
        """Field mappings for FL-311 Child Custody and Visitation Attachment"""
        return {
            # This would map the specific fields on FL-311
            "case_number": {"page": 0, "x": 400, "y": 720, "type": "text"},
            "petitioner_name": {"page": 0, "x": 100, "y": 680, "type": "text"},
            "respondent_name": {"page": 0, "x": 100, "y": 660, "type": "text"},
            # ... additional FL-311 specific fields
        }
    
    def _get_fl150_fields(self) -> Dict[str, Dict]:
        """Field mappings for FL-150 Income and Expense Declaration"""
        return {
            # Income fields
            "employer_name": {"page": 0, "x": 100, "y": 600, "type": "text"},
            "gross_monthly_income": {"page": 0, "x": 100, "y": 550, "type": "text"},
            # ... additional FL-150 specific fields
        }
    
    async def fill_form(
        self,
        form_type: str,
        form_data: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> bytes:
        """Fill out an official form with provided data"""
        
        # Load the blank form template
        template_path = self.forms_path / f"{form_type}.pdf"
        if not template_path.exists():
            raise FileNotFoundError(f"Form template {form_type}.pdf not found")
        
        # Read the template
        with open(template_path, 'rb') as template_file:
            template_pdf = PyPDF2.PdfReader(template_file)
            output_pdf = PyPDF2.PdfWriter()
            
            # Get field mappings for this form
            field_mappings = self.form_fields.get(form_type, {})
            
            # Process each page
            for page_num in range(len(template_pdf.pages)):
                page = template_pdf.pages[page_num]
                
                # Create overlay for this page
                packet = io.BytesIO()
                overlay_canvas = canvas.Canvas(packet, pagesize=letter)
                
                # Fill in fields for this page
                for field_name, field_info in field_mappings.items():
                    if field_name in form_data:
                        # Handle page -1 as last page
                        field_page = field_info["page"]
                        if field_page == -1:
                            field_page = len(template_pdf.pages) - 1
                        
                        if field_page == page_num:
                            self._write_field(
                                overlay_canvas,
                                field_info,
                                form_data[field_name]
                            )
                
                overlay_canvas.save()
                packet.seek(0)
                
                # Merge overlay with template page
                overlay_pdf = PyPDF2.PdfReader(packet)
                if len(overlay_pdf.pages) > 0:
                    overlay_page = overlay_pdf.pages[0]
                    page.merge_page(overlay_page)
                
                output_pdf.add_page(page)
            
            # Save to bytes
            output_buffer = io.BytesIO()
            output_pdf.write(output_buffer)
            output_buffer.seek(0)
            
            # Optionally save to file
            if output_path:
                with open(output_path, 'wb') as output_file:
                    output_file.write(output_buffer.getvalue())
            
            return output_buffer.getvalue()
    
    def _write_field(self, canvas_obj, field_info: Dict, value: Any):
        """Write a field value to the canvas"""
        x = field_info["x"]
        y = field_info["y"]
        field_type = field_info["type"]
        
        if field_type == "text":
            # Single line text
            canvas_obj.drawString(x, y, str(value))
            
        elif field_type == "checkbox":
            # Draw X or checkmark if True
            if value:
                canvas_obj.drawString(x, y, "X")
                
        elif field_type == "multiline":
            # Multi-line text with word wrap
            width = field_info.get("width", 400)
            height = field_info.get("height", 100)
            text = str(value)
            
            # Simple word wrap (you might want to use reportlab's Paragraph for better formatting)
            lines = self._wrap_text(text, width, canvas_obj)
            line_height = 12
            current_y = y
            
            for line in lines:
                if current_y < (y - height):
                    break  # Don't exceed field height
                canvas_obj.drawString(x, current_y, line)
                current_y -= line_height
    
    def _wrap_text(self, text: str, width: float, canvas_obj) -> List[str]:
        """Simple text wrapping"""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            # Approximate width check (you'd want to use stringWidth for accuracy)
            if len(test_line) * 6 > width:  # Rough approximation
                if current_line:
                    lines.append(' '.join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
            else:
                current_line.append(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    async def generate_motion_pdf(
        self,
        motion_type: str,
        motion_data: Dict[str, Any],
        profile_data: Dict[str, Any],
        llm_sections: List[Dict[str, Any]]
    ) -> bytes:
        """Generate complete motion PDF with all sections"""
        
        # Determine which form to use
        form_type = "FL-300" if motion_type == "RFO" else "FL-320"
        
        # Prepare form data
        form_data = {
            # Header information
            "petitioner_name": profile_data.get("party_name", ""),
            "respondent_name": profile_data.get("other_party_name", ""),
            "case_number": profile_data.get("case_number", ""),
            "court_name": f"Superior Court of California",
            "court_address": f"County of {profile_data.get('county', '')}",
            
            # Party representation
            "attorney_for": "In Pro Per" if profile_data.get("is_petitioner") else "In Pro Per",
        }
        
        # Add hearing information if available
        if motion_data.get("hearing_date"):
            form_data["hearing_date"] = motion_data["hearing_date"]
            form_data["hearing_time"] = motion_data.get("hearing_time", "")
            form_data["hearing_dept"] = motion_data.get("department", "")
        
        # Process LLM sections into form fields
        facts_text = ""
        for section in llm_sections:
            if section.get("rewritten_text"):
                facts_text += f"\n\n{section['rewritten_text']}"
        
        form_data["facts_text"] = facts_text.strip()
        
        # Add requests based on motion answers
        all_answers = {}
        for section in llm_sections:
            if section.get("original_answers"):
                all_answers.update(section["original_answers"])
        
        # Map relief categories to form checkboxes
        if "relief_categories" in all_answers:
            categories = all_answers["relief_categories"]
            if "custody" in categories:
                form_data["request_custody"] = True
            if "child_support" in categories:
                form_data["request_child_support"] = True
                if "child_support_amount" in all_answers:
                    form_data["child_support_amount"] = all_answers["child_support_amount"]
            if "spousal_support" in categories:
                form_data["request_spousal_support"] = True
                if "spousal_support_amount" in all_answers:
                    form_data["spousal_support_amount"] = all_answers["spousal_support_amount"]
            if "attorney_fees" in categories:
                form_data["request_attorney_fees"] = True
        
        # Add signature information
        form_data["signature_date"] = datetime.now().strftime("%m/%d/%Y")
        form_data["signature_name"] = profile_data.get("party_name", "")
        form_data["signature_title"] = "Petitioner" if profile_data.get("is_petitioner") else "Respondent"
        
        # Fill the form
        pdf_bytes = await self.fill_form(form_type, form_data)
        
        return pdf_bytes
    
    def validate_form_data(self, form_type: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that required fields are present"""
        required_fields = {
            "FL-300": ["petitioner_name", "respondent_name", "case_number"],
            "FL-320": ["petitioner_name", "respondent_name", "case_number"]
        }
        
        missing_fields = []
        form_requirements = required_fields.get(form_type, [])
        
        for field in form_requirements:
            if field not in form_data or not form_data[field]:
                missing_fields.append(field)
        
        return {
            "valid": len(missing_fields) == 0,
            "missing_fields": missing_fields
        }

# Singleton instance
pdf_service = PDFService()