"""
Enhanced PDF Service V2 - Advanced features for court forms
Includes multi-page text flow, barcode generation, validation, version tracking, and service copies
"""
import os
import io
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from pathlib import Path
import PyPDF2
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black, blue, red
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import json
import logging
import hashlib
import textwrap
import re
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import court forms mapping
try:
    from app.services.court_forms_mapping import court_forms_mapping, FormType
    HAS_COURT_FORMS = True
except ImportError:
    HAS_COURT_FORMS = False
    logger.warning("Court forms mapping not available")


class DocumentVersion:
    """Track document versions for edits"""
    def __init__(self, version_id: str, timestamp: datetime, content_hash: str, changes: List[str], form_data: Dict[str, Any]):
        self.version_id = version_id
        self.timestamp = timestamp
        self.content_hash = content_hash
        self.changes = changes
        self.form_data = form_data


class EnhancedPDFServiceV2:
    """Enhanced PDF service with advanced features"""

    def __init__(self):
        # Path to blank form templates
        self.forms_path = Path(__file__).parent.parent.parent / "forms"
        self.output_path = Path(__file__).parent.parent.parent / "output"

        # Ensure output directory exists
        self.output_path.mkdir(exist_ok=True)

        # Initialize styles
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

        # Version tracking storage
        self.document_versions = {}

        # Form overflow tracking
        self.overflow_pages = {}

    def _init_custom_styles(self):
        """Initialize custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CourtHeader',
            parent=self.styles['Heading1'],
            fontSize=14,
            alignment=1,  # Center
            spaceAfter=12
        ))

        self.styles.add(ParagraphStyle(
            name='CaseCaption',
            parent=self.styles['Normal'],
            fontSize=11,
            leftIndent=0,
            rightIndent=0
        ))

        self.styles.add(ParagraphStyle(
            name='ContinuationText',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=36,
            rightIndent=36
        ))

    def fill_form_with_overflow(
        self,
        form_type: str,
        form_data: Dict[str, Any],
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Fill a court form with multi-page text overflow support

        Args:
            form_type: Type of form
            form_data: Dictionary of field values
            output_filename: Optional output filename

        Returns:
            Result dictionary with success status and file path
        """
        try:
            # Validate form data first
            validation_result = self.validate_form(form_type, form_data)
            if not validation_result['valid']:
                logger.warning(f"Form validation issues: {validation_result}")

            # Track version
            doc_id = f"{form_type}_{form_data.get('case_number', 'unknown')}"
            version_id = self.track_version(doc_id, form_data, ["Initial creation"])

            # Generate output filename if not provided
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"{form_type}_{timestamp}_{version_id}.pdf"

            output_path = self.output_path / output_filename

            # Process form with overflow handling
            writer = PdfWriter()
            overflow_texts = {}

            # Fill main form
            main_form = self._fill_form_with_overflow_detection(form_type, form_data)
            writer.add_page(main_form['page'])

            if main_form.get('overflow'):
                overflow_texts = main_form['overflow']

            # Create continuation pages if needed
            if overflow_texts:
                page_num = 2
                for field_name, overflow_text in overflow_texts.items():
                    continuation_page = self._create_continuation_page(
                        overflow_text, form_type, field_name, page_num
                    )
                    writer.add_page(continuation_page)
                    page_num += 1

            # Add filing codes
            self._add_codes_to_writer(
                writer,
                form_data.get('case_number', 'UNKNOWN'),
                form_type,
                version_id
            )

            # Save PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            return {
                "success": True,
                "file_path": str(output_path),
                "file_name": output_filename,
                "form_type": form_type,
                "version_id": version_id,
                "pages": len(writer.pages),
                "validation": validation_result
            }

        except Exception as e:
            logger.error(f"Error filling form with overflow: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _fill_form_with_overflow_detection(
        self,
        form_type: str,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Fill form and detect overflow text"""

        # Create form page
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        overflow_fields = {}

        # Process each field
        for field_name, field_value in form_data.items():
            if isinstance(field_value, str) and len(field_value) > 200:
                # Long text field - handle overflow
                field_text, overflow_text = self._handle_long_text(field_value, 200)

                # Draw truncated text on form
                self._draw_field_on_form(can, field_name, field_text, form_type)

                # Store overflow for continuation pages
                if overflow_text:
                    overflow_fields[field_name] = overflow_text
            else:
                # Normal field
                self._draw_field_on_form(can, field_name, field_value, form_type)

        can.save()
        packet.seek(0)

        return {
            'page': PdfReader(packet).pages[0],
            'overflow': overflow_fields
        }

    def _handle_long_text(self, text: str, max_chars: int = 200) -> Tuple[str, Optional[str]]:
        """
        Handle long text with overflow to continuation pages

        Args:
            text: The text to fit
            max_chars: Maximum characters for the field

        Returns:
            Tuple of (text for field, overflow text)
        """
        if len(text) <= max_chars:
            return text, None

        # Find word boundary for clean break
        break_point = text.rfind(' ', 0, max_chars - 20)  # Leave room for continuation marker
        if break_point == -1:
            break_point = max_chars - 20

        field_text = text[:break_point] + " [See Attachment]"
        overflow_text = text[break_point:].strip()

        return field_text, overflow_text

    def _create_continuation_page(
        self,
        overflow_text: str,
        form_type: str,
        field_name: str,
        page_num: int
    ) -> Any:
        """
        Create a continuation page for overflow text

        Args:
            overflow_text: Text that didn't fit
            form_type: Type of form being continued
            field_name: Name of the field being continued
            page_num: Page number for this continuation

        Returns:
            PDF page with continuation text
        """
        packet = io.BytesIO()
        canvas_obj = canvas.Canvas(packet, pagesize=letter)
        width, height = letter

        # Header
        canvas_obj.setFont("Helvetica-Bold", 12)
        canvas_obj.drawString(72, height - 72, f"{form_type} - ATTACHMENT {page_num - 1}")

        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(72, height - 90, f"Continuation of: {field_name.replace('_', ' ').title()}")

        # Draw continuation text with word wrap
        canvas_obj.setFont("Helvetica", 11)
        text_object = canvas_obj.beginText(72, height - 120)

        # Word wrap the text
        lines = self._wrap_text(overflow_text, 80)  # 80 chars per line
        for line in lines:
            text_object.textLine(line)

        canvas_obj.drawText(text_object)

        # Footer
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.drawString(72, 72, f"Page {page_num}")
        canvas_obj.drawRightString(width - 72, 72, f"{form_type} Attachment")

        canvas_obj.save()
        packet.seek(0)

        return PdfReader(packet).pages[0]

    def _wrap_text(self, text: str, width: int) -> List[str]:
        """Wrap text to specified width"""
        return textwrap.wrap(text, width=width)

    def _draw_field_on_form(self, canvas_obj, field_name: str, field_value: Any, form_type: str):
        """Draw a field value on the form canvas"""
        # Simplified field positioning (would be form-specific in real implementation)
        field_positions = self._get_field_positions(form_type)

        if field_name in field_positions:
            pos = field_positions[field_name]
            x, y = pos['x'], pos['y']

            if pos.get('type') == 'checkbox' and field_value:
                canvas_obj.drawString(x, y, 'X')
            elif pos.get('type') == 'radio' and field_value:
                canvas_obj.circle(x + 3, y + 3, 3, fill=1)
            else:
                canvas_obj.drawString(x, y, str(field_value)[:pos.get('max_len', 50)])

    def _get_field_positions(self, form_type: str) -> Dict[str, Dict]:
        """Get field positions for form type"""
        # This would contain detailed mappings for each form
        positions = {
            "FL-300": {
                "petitioner_name": {"x": 150, "y": 650, "type": "text", "max_len": 40},
                "respondent_name": {"x": 150, "y": 630, "type": "text", "max_len": 40},
                "case_number": {"x": 450, "y": 650, "type": "text", "max_len": 20},
                "declaration_text": {"x": 72, "y": 500, "type": "text", "max_len": 200},
            },
            "MC-030": {
                "declarant_name": {"x": 150, "y": 650, "type": "text", "max_len": 40},
                "declaration_text": {"x": 72, "y": 550, "type": "text", "max_len": 200},
            }
        }
        return positions.get(form_type, {})

    def _generate_filing_barcode(self, case_number: str, document_type: str, version: str) -> Image:
        """Generate a barcode for court filing"""
        barcode_data = f"{case_number}-{document_type}-{version}-{datetime.now().strftime('%Y%m%d')}"

        # Generate Code128 barcode
        buffer = io.BytesIO()
        Code128(barcode_data, writer=ImageWriter()).write(buffer)
        buffer.seek(0)

        return Image.open(buffer)

    def _generate_qr_code(self, data: Dict[str, Any]) -> Image:
        """Generate QR code for document metadata"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Create compact JSON representation
        qr_data = json.dumps({
            'case': data.get('case_number', ''),
            'type': data.get('form_type', ''),
            'date': datetime.now().isoformat(),
            'version': data.get('version', '1.0')
        })

        qr.add_data(qr_data)
        qr.make(fit=True)

        return qr.make_image(fill_color="black", back_color="white")

    def _add_codes_to_writer(self, writer: PdfWriter, case_number: str, form_type: str, version_id: str):
        """Add barcode and QR code to PDF writer's first page"""
        try:
            # Generate codes
            barcode = self._generate_filing_barcode(case_number, form_type, version_id)
            qr_code = self._generate_qr_code({
                'case_number': case_number,
                'form_type': form_type,
                'version': version_id
            })

            # Create overlay with codes
            packet = io.BytesIO()
            canvas_obj = canvas.Canvas(packet, pagesize=letter)

            # Add barcode at top right
            barcode_buffer = io.BytesIO()
            barcode.save(barcode_buffer, format='PNG')
            barcode_buffer.seek(0)
            canvas_obj.drawImage(ImageReader(barcode_buffer), 400, 700, width=150, height=50)

            # Add QR code at bottom right
            qr_buffer = io.BytesIO()
            qr_code.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            canvas_obj.drawImage(ImageReader(qr_buffer), 500, 50, width=75, height=75)

            canvas_obj.save()
            packet.seek(0)

            # Merge with first page
            overlay = PdfReader(packet)
            if len(writer.pages) > 0:
                writer.pages[0].merge_page(overlay.pages[0])

        except Exception as e:
            logger.error(f"Error adding filing codes: {e}")

    def validate_form(self, form_type: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate form data before PDF generation

        Args:
            form_type: Type of form to validate
            form_data: Form field data

        Returns:
            Validation results with errors and warnings
        """
        errors = []
        warnings = []
        required_fields = []

        # Get required fields for form type
        if HAS_COURT_FORMS:
            form_type_enum = self._get_form_type_enum(form_type)
            if form_type_enum:
                required_fields = court_forms_mapping.get_required_fields(form_type_enum)

        # Check required fields
        for field in required_fields:
            if field not in form_data or not form_data[field]:
                errors.append(f"Required field missing: {field}")

        # Validate field formats
        for field, value in form_data.items():
            if value:
                # Date validation
                if 'date' in field.lower():
                    if not self._validate_date(value):
                        errors.append(f"Invalid date format for {field}: {value}")

                # Email validation
                if 'email' in field.lower():
                    if not self._validate_email(value):
                        errors.append(f"Invalid email format for {field}: {value}")

                # Phone validation
                if 'phone' in field.lower():
                    if not self._validate_phone(value):
                        warnings.append(f"Phone number may be incorrectly formatted: {value}")

                # Case number validation
                if 'case_number' in field.lower():
                    if not self._validate_case_number(value):
                        warnings.append(f"Case number format may be incorrect: {value}")

        # Check for conflicting information
        if 'is_emergency' in form_data and form_data.get('is_emergency'):
            if 'hearing_date' not in form_data:
                warnings.append("Emergency filing selected but no hearing date provided")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'field_count': len(form_data),
            'required_count': len(required_fields),
            'completion_percentage': (len([f for f in required_fields if f in form_data]) / len(required_fields) * 100) if required_fields else 100
        }

    def _validate_date(self, date_str: str) -> bool:
        """Validate date format"""
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
            r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
            r'^\d{2}-\d{2}-\d{4}$'   # MM-DD-YYYY
        ]
        return any(re.match(pattern, str(date_str)) for pattern in patterns)

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(email)))

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone format"""
        cleaned = re.sub(r'[^0-9]', '', str(phone))
        return len(cleaned) == 10 or len(cleaned) == 11

    def _validate_case_number(self, case_number: str) -> bool:
        """Validate case number format"""
        patterns = [
            r'^[A-Z]{2}-\d{4}-\d{6}$',  # FL-2024-001234
            r'^\d{2}[A-Z]{1}\d{6}$',     # 24D001234
            r'^[A-Z]{2}\d{6}$'           # FL001234
        ]
        return any(re.match(pattern, str(case_number)) for pattern in patterns)

    def _get_form_type_enum(self, form_type: str):
        """Convert string form type to enum"""
        if not HAS_COURT_FORMS:
            return None

        form_map = {
            "FL-300": FormType.FL300,
            "FL-150": FormType.FL150,
            "FL-305": FormType.FL305,
            "FL-335": FormType.FL335,
            "FL-410": FormType.FL410,
            "FL-411": FormType.FL411,
            "MC-030": FormType.MC030,
            "D-046": FormType.D046,
        }
        return form_map.get(form_type)

    def track_version(self, document_id: str, form_data: Dict[str, Any], changes: List[str] = None) -> str:
        """
        Track document version for edits

        Args:
            document_id: Unique document identifier
            form_data: Current form data
            changes: List of changes made

        Returns:
            Version ID
        """
        # Generate content hash
        content_str = json.dumps(form_data, sort_keys=True)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()[:16]

        # Create version ID
        version_id = f"v{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Store version
        if document_id not in self.document_versions:
            self.document_versions[document_id] = []

        version = DocumentVersion(
            version_id=version_id,
            timestamp=datetime.now(),
            content_hash=content_hash,
            changes=changes or [],
            form_data=form_data.copy()
        )

        self.document_versions[document_id].append(version)

        logger.info(f"Tracked version {version_id} for document {document_id}")
        return version_id

    def get_version_history(self, document_id: str) -> List[Dict[str, Any]]:
        """Get version history for a document"""
        if document_id not in self.document_versions:
            return []

        history = []
        for version in self.document_versions[document_id]:
            history.append({
                'version_id': version.version_id,
                'timestamp': version.timestamp.isoformat(),
                'changes': version.changes,
                'hash': version.content_hash
            })

        return history

    def get_version_diff(self, document_id: str, version1: str, version2: str) -> Dict[str, Any]:
        """
        Get differences between two document versions

        Args:
            document_id: Document ID
            version1: First version ID
            version2: Second version ID

        Returns:
            Diff information
        """
        if document_id not in self.document_versions:
            return {'error': 'Document not found'}

        versions = self.document_versions[document_id]
        v1 = next((v for v in versions if v.version_id == version1), None)
        v2 = next((v for v in versions if v.version_id == version2), None)

        if not v1 or not v2:
            return {'error': 'Version not found'}

        # Find field differences
        field_diffs = []
        all_fields = set(v1.form_data.keys()) | set(v2.form_data.keys())

        for field in all_fields:
            val1 = v1.form_data.get(field)
            val2 = v2.form_data.get(field)

            if val1 != val2:
                field_diffs.append({
                    'field': field,
                    'old_value': val1,
                    'new_value': val2
                })

        return {
            'version1': version1,
            'version2': version2,
            'timestamp1': v1.timestamp.isoformat(),
            'timestamp2': v2.timestamp.isoformat(),
            'changes1': v1.changes,
            'changes2': v2.changes,
            'content_changed': v1.content_hash != v2.content_hash,
            'field_differences': field_diffs
        }

    def generate_service_copy(self, pdf_path: str, service_type: str = 'personal') -> Dict[str, Any]:
        """
        Generate service copy of document

        Args:
            pdf_path: Path to original PDF
            service_type: Type of service (personal, mail, electronic)

        Returns:
            Status and path to service copy
        """
        try:
            reader = PdfReader(pdf_path)
            writer = PdfWriter()

            # Add service stamp to each page
            for page_num, page in enumerate(reader.pages):
                packet = io.BytesIO()
                canvas_obj = canvas.Canvas(packet, pagesize=letter)

                # Add service stamp
                canvas_obj.setFont("Helvetica-Bold", 10)
                canvas_obj.setFillColorRGB(1, 0, 0)  # Red color

                if service_type == 'personal':
                    stamp_text = "COPY - FOR SERVICE ONLY"
                elif service_type == 'mail':
                    stamp_text = "COPY - SERVICE BY MAIL"
                else:
                    stamp_text = "COPY - ELECTRONIC SERVICE"

                canvas_obj.drawString(400, 750, stamp_text)

                # Add service date
                canvas_obj.setFont("Helvetica", 8)
                canvas_obj.drawString(400, 735, f"Date: {datetime.now().strftime('%m/%d/%Y')}")

                canvas_obj.save()
                packet.seek(0)

                overlay = PdfReader(packet)
                page.merge_page(overlay.pages[0])
                writer.add_page(page)

            # Save service copy
            output_path = pdf_path.replace('.pdf', f'_service_{service_type}.pdf')
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)

            logger.info(f"Generated service copy: {output_path}")

            return {
                'status': 'success',
                'message': f'{service_type.capitalize()} service copy generated',
                'path': output_path,
                'pages': len(reader.pages)
            }

        except Exception as e:
            logger.error(f"Error generating service copy: {str(e)}")
            return {
                'status': 'error',
                'message': f'Failed to generate service copy: {str(e)}'
            }

    def create_enhanced_packet(
        self,
        forms: List[Dict[str, Any]],
        case_info: Dict[str, Any],
        packet_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an enhanced packet with all advanced features

        Args:
            forms: List of form dictionaries with type and data
            case_info: Case information for cover sheet
            packet_name: Optional packet name

        Returns:
            Result with packet path
        """
        try:
            if not packet_name:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                packet_name = f"motion_packet_{timestamp}.pdf"

            packet_path = self.output_path / packet_name
            writer = PdfWriter()

            # Add cover sheet
            cover = self._create_enhanced_cover_sheet(forms, case_info)
            writer.add_page(cover)

            # Process each form
            form_files = []
            for form_spec in forms:
                form_result = self.fill_form_with_overflow(
                    form_spec['type'],
                    form_spec['data']
                )

                if form_result['success']:
                    form_files.append(form_result['file_path'])

                    # Add form pages to packet
                    form_reader = PdfReader(form_result['file_path'])
                    for page in form_reader.pages:
                        writer.add_page(page)

            # Add filing checklist
            checklist = self._create_enhanced_filing_checklist(forms, case_info)
            writer.add_page(checklist)

            # Save packet
            with open(packet_path, 'wb') as output:
                writer.write(output)

            # Generate service copies
            service_copy_result = self.generate_service_copy(str(packet_path), 'mail')

            return {
                'success': True,
                'packet_path': str(packet_path),
                'packet_name': packet_name,
                'forms_included': len(forms),
                'total_pages': len(writer.pages),
                'service_copy': service_copy_result.get('path') if service_copy_result['status'] == 'success' else None
            }

        except Exception as e:
            logger.error(f"Error creating enhanced packet: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _create_enhanced_cover_sheet(self, forms: List[Dict], case_info: Dict) -> Any:
        """Create enhanced cover sheet with case information"""
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 72, "COURT FILING PACKET")

        # Case information
        c.setFont("Helvetica", 11)
        c.drawString(72, height - 120, f"Case Number: {case_info.get('case_number', 'TBD')}")
        c.drawString(72, height - 140, f"Petitioner: {case_info.get('petitioner_name', '')}")
        c.drawString(72, height - 160, f"Respondent: {case_info.get('respondent_name', '')}")
        c.drawString(72, height - 180, f"Prepared: {datetime.now().strftime('%B %d, %Y')}")

        # Forms included
        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, height - 220, "Documents Included:")

        c.setFont("Helvetica", 10)
        y = height - 240
        for i, form in enumerate(forms, 1):
            form_type = form.get('type', 'Unknown')
            c.drawString(90, y, f"{i}. {form_type}")
            y -= 20

        # Instructions
        y -= 30
        c.setFont("Helvetica-Bold", 11)
        c.drawString(72, y, "Important Filing Instructions:")

        c.setFont("Helvetica", 9)
        instructions = [
            "• Review all documents for accuracy before filing",
            "• Sign and date all signature pages",
            "• Make 3 copies: 1 for court, 1 for other party, 1 for your records",
            "• File original with court clerk",
            "• Serve copy on other party within required timeframe",
            "• File proof of service with court"
        ]

        y -= 20
        for instruction in instructions:
            c.drawString(90, y, instruction)
            y -= 15

        c.save()
        packet.seek(0)

        return PdfReader(packet).pages[0]

    def _create_enhanced_filing_checklist(self, forms: List[Dict], case_info: Dict) -> Any:
        """Create enhanced filing checklist"""
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        width, height = letter

        # Title
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredString(width/2, height - 72, "PRE-FILING CHECKLIST")

        # Case info
        c.setFont("Helvetica", 10)
        c.drawString(72, height - 100, f"Case: {case_info.get('case_number', 'TBD')}")

        # Checklist categories
        y = height - 130

        categories = [
            ("Document Preparation", [
                "All forms completed accurately",
                "Case number on every page",
                "Dates filled in correctly",
                "All required fields completed",
                "Attachments referenced properly"
            ]),
            ("Signatures", [
                "All signature lines signed",
                "Dates next to signatures",
                "Attorney signature (if applicable)",
                "Verification/declaration signed"
            ]),
            ("Supporting Documents", [
                "Income and Expense Declaration (if support requested)",
                "Property declarations attached",
                "Exhibits properly marked",
                "Proof of service forms ready"
            ]),
            ("Filing Requirements", [
                "Filing fee ready or fee waiver",
                "Correct number of copies made",
                "Envelopes for service",
                "Hearing date confirmed"
            ])
        ]

        for category, items in categories:
            c.setFont("Helvetica-Bold", 11)
            c.drawString(72, y, category)
            y -= 15

            c.setFont("Helvetica", 9)
            for item in items:
                c.drawString(90, y, f"□ {item}")
                y -= 13

            y -= 10

        # Footer
        c.setFont("Helvetica-Oblique", 8)
        c.drawString(72, 72, "This checklist is for reference only. Consult local rules for specific requirements.")

        c.save()
        packet.seek(0)

        return PdfReader(packet).pages[0]


# Singleton instance
enhanced_pdf_service_v2 = EnhancedPDFServiceV2()