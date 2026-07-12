"""
Tests for PDF service functionality
"""
import pytest
import pytest_asyncio
from unittest.mock import patch, MagicMock, mock_open
import io
from pathlib import Path

from app.services.pdf_service import PDFService


@pytest_asyncio.fixture
async def pdf_service():
    """Create a PDF service instance for testing."""
    return PDFService()


class TestPDFService:
    """Test PDF service functionality."""

    def test_init(self, pdf_service: PDFService):
        """Test PDFService initialization."""
        assert pdf_service is not None
        assert hasattr(pdf_service, 'forms_path')
        assert hasattr(pdf_service, 'form_fields')
        assert 'FL-300' in pdf_service.form_fields
        assert 'FL-320' in pdf_service.form_fields

    def test_fl300_field_mappings(self, pdf_service: PDFService):
        """Test FL-300 form field mappings."""
        fl300_fields = pdf_service._get_fl300_fields()

        # Test essential fields exist
        required_fields = [
            'petitioner_name', 'respondent_name', 'case_number',
            'court_name', 'hearing_date', 'facts_text'
        ]

        for field in required_fields:
            assert field in fl300_fields
            assert 'page' in fl300_fields[field]
            assert 'x' in fl300_fields[field]
            assert 'y' in fl300_fields[field]
            assert 'type' in fl300_fields[field]

        # Test checkbox fields
        checkbox_fields = ['request_custody', 'request_child_support']
        for field in checkbox_fields:
            if field in fl300_fields:
                assert fl300_fields[field]['type'] == 'checkbox'

        # Test multiline fields
        multiline_fields = ['facts_text', 'other_orders_text']
        for field in multiline_fields:
            if field in fl300_fields:
                assert fl300_fields[field]['type'] == 'multiline'

    def test_fl320_field_mappings(self, pdf_service: PDFService):
        """Test FL-320 form field mappings."""
        fl320_fields = pdf_service._get_fl320_fields()

        required_fields = [
            'petitioner_name', 'respondent_name', 'case_number',
            'court_name', 'response_text'
        ]

        for field in required_fields:
            assert field in fl320_fields

        # Test response checkboxes
        response_fields = ['agree_all', 'disagree_all', 'agree_part']
        for field in response_fields:
            assert field in fl320_fields
            assert fl320_fields[field]['type'] == 'checkbox'

    @patch('builtins.open', new_callable=mock_open, read_data=b'mock_pdf_content')
    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    @patch('app.services.pdf_service.PyPDF2.PdfWriter')
    @patch('app.services.pdf_service.canvas.Canvas')
    async def test_fill_form_success(
        self,
        mock_canvas,
        mock_writer,
        mock_reader,
        mock_file,
        pdf_service: PDFService
    ):
        """Test successful form filling."""
        # Setup mocks
        mock_page = MagicMock()
        mock_reader.return_value.pages = [mock_page]
        mock_writer_instance = MagicMock()
        mock_writer.return_value = mock_writer_instance

        # Mock canvas
        mock_canvas_instance = MagicMock()
        mock_canvas.return_value = mock_canvas_instance

        # Mock file path existence
        with patch.object(Path, 'exists', return_value=True):
            form_data = {
                'petitioner_name': 'John Doe',
                'respondent_name': 'Jane Doe',
                'case_number': 'FL-2024-001'
            }

            result = await pdf_service.fill_form('FL-300', form_data)

            assert isinstance(result, bytes)
            mock_writer_instance.write.assert_called_once()

    @patch.object(Path, 'exists', return_value=False)
    async def test_fill_form_template_not_found(self, mock_exists, pdf_service: PDFService):
        """Test form filling when template doesn't exist."""
        form_data = {'petitioner_name': 'John Doe'}

        with pytest.raises(FileNotFoundError):
            await pdf_service.fill_form('FL-300', form_data)

    def test_write_field_text(self, pdf_service: PDFService):
        """Test writing text fields."""
        mock_canvas = MagicMock()
        field_info = {'x': 100, 'y': 200, 'type': 'text'}

        pdf_service._write_field(mock_canvas, field_info, 'Test Value')

        mock_canvas.drawString.assert_called_once_with(100, 200, 'Test Value')

    def test_write_field_checkbox_true(self, pdf_service: PDFService):
        """Test writing checkbox fields when True."""
        mock_canvas = MagicMock()
        field_info = {'x': 100, 'y': 200, 'type': 'checkbox'}

        pdf_service._write_field(mock_canvas, field_info, True)

        mock_canvas.drawString.assert_called_once_with(100, 200, 'X')

    def test_write_field_checkbox_false(self, pdf_service: PDFService):
        """Test writing checkbox fields when False."""
        mock_canvas = MagicMock()
        field_info = {'x': 100, 'y': 200, 'type': 'checkbox'}

        pdf_service._write_field(mock_canvas, field_info, False)

        mock_canvas.drawString.assert_not_called()

    def test_write_field_multiline(self, pdf_service: PDFService):
        """Test writing multiline text fields."""
        mock_canvas = MagicMock()
        field_info = {
            'x': 100, 'y': 200, 'type': 'multiline',
            'width': 400, 'height': 100
        }

        pdf_service._write_field(mock_canvas, field_info, 'Line 1\nLine 2\nLine 3')

        # Should be called multiple times for multiple lines
        assert mock_canvas.drawString.call_count >= 1

    def test_wrap_text(self):
        """Text wrapping moved to pdf_text_utils (accurate stringWidth-based)."""
        from app.services.pdf_text_utils import wrap_text_accurate

        text = "This is a very long line of text that should be wrapped to multiple lines"
        lines = wrap_text_accurate(text, 100)

        assert isinstance(lines, list)
        assert len(lines) > 1
        assert all(isinstance(line, str) for line in lines)

    async def test_generate_motion_pdf(self, pdf_service: PDFService):
        """Test generating complete motion PDF."""
        motion_data = {
            'hearing_date': '2024-01-15',
            'hearing_time': '9:00 AM',
            'department': 'Dept. 1'
        }

        profile_data = {
            'party_name': 'John Doe',
            'other_party_name': 'Jane Doe',
            'case_number': 'FL-2024-001',
            'county': 'Los Angeles',
            'is_petitioner': True
        }

        llm_sections = [
            {
                'rewritten_text': 'This is the facts section',
                'original_answers': {
                    'relief_categories': ['custody', 'child_support'],
                    'child_support_amount': '$500'
                }
            }
        ]

        # Mock the fill_form method to avoid file system dependencies
        with patch.object(pdf_service, 'fill_form') as mock_fill_form:
            mock_fill_form.return_value = b'mock_pdf_bytes'

            result = await pdf_service.generate_motion_pdf(
                'RFO', motion_data, profile_data, llm_sections
            )

            assert result == b'mock_pdf_bytes'
            mock_fill_form.assert_called_once()

            # Verify form data was properly prepared
            call_args = mock_fill_form.call_args
            form_type, form_data = call_args[0]

            assert form_type == 'FL-300'
            assert form_data['petitioner_name'] == 'John Doe'
            assert form_data['respondent_name'] == 'Jane Doe'
            assert form_data['case_number'] == 'FL-2024-001'
            assert form_data['hearing_date'] == '2024-01-15'
            assert 'facts section' in form_data['facts_text']
            assert form_data['request_custody'] is True
            assert form_data['request_child_support'] is True

    def test_validate_form_data_valid(self, pdf_service: PDFService):
        """Test form data validation with valid data."""
        form_data = {
            'petitioner_name': 'John Doe',
            'respondent_name': 'Jane Doe',
            'case_number': 'FL-2024-001'
        }

        result = pdf_service.validate_form_data('FL-300', form_data)

        assert result['valid'] is True
        assert result['missing_fields'] == []

    def test_validate_form_data_missing_fields(self, pdf_service: PDFService):
        """Test form data validation with missing fields."""
        form_data = {
            'petitioner_name': 'John Doe',
            # Missing respondent_name and case_number
        }

        result = pdf_service.validate_form_data('FL-300', form_data)

        assert result['valid'] is False
        assert 'respondent_name' in result['missing_fields']
        assert 'case_number' in result['missing_fields']

    def test_validate_form_data_unknown_form(self, pdf_service: PDFService):
        """Test form data validation for unknown form type."""
        form_data = {'test_field': 'test_value'}

        result = pdf_service.validate_form_data('UNKNOWN-FORM', form_data)

        assert result['valid'] is True  # No required fields defined
        assert result['missing_fields'] == []

    def test_form_fields_structure(self, pdf_service: PDFService):
        """Test that all form field definitions have required structure."""
        for form_type, fields in pdf_service.form_fields.items():
            assert isinstance(fields, dict)

            for field_name, field_info in fields.items():
                assert isinstance(field_info, dict)
                assert 'page' in field_info
                assert 'x' in field_info
                assert 'y' in field_info
                assert 'type' in field_info

                # Validate field types
                assert field_info['type'] in ['text', 'checkbox', 'multiline']

                # Validate coordinates
                assert isinstance(field_info['x'], (int, float))
                assert isinstance(field_info['y'], (int, float))

                # Multiline fields should have width and height
                if field_info['type'] == 'multiline':
                    assert 'width' in field_info
                    assert 'height' in field_info

    @patch('app.services.pdf_service.PyPDF2.PdfReader')
    async def test_fill_form_with_page_mapping(self, mock_reader, pdf_service: PDFService):
        """Test form filling with proper page mapping."""
        # Create multiple mock pages
        mock_pages = [MagicMock(), MagicMock(), MagicMock()]
        mock_reader.return_value.pages = mock_pages

        # Mock path exists
        with patch.object(Path, 'exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=b'mock_pdf')), \
             patch('app.services.pdf_service.PyPDF2.PdfWriter') as mock_writer, \
             patch('app.services.pdf_service.canvas.Canvas'):

            form_data = {
                'petitioner_name': 'John Doe',  # Page 0
                'facts_text': 'Test facts',     # Page 2
                'signature_date': '01/01/2024'  # Page -1 (last page)
            }

            await pdf_service.fill_form('FL-300', form_data)

            # Verify that writer was called with correct number of pages
            mock_writer_instance = mock_writer.return_value
            assert mock_writer_instance.add_page.call_count == len(mock_pages)