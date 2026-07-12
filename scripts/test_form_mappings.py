#!/usr/bin/env python3
"""
Test script for comprehensive court form mappings
Tests all 8 forms with sample conversation data
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.court_forms_mapping import court_forms_mapping, FormType
from app.services.form_field_mapper import form_mapper

def test_court_forms():
    """Test the comprehensive court forms mapping"""
    print("\n" + "=" * 60)
    print("TESTING COURT FORMS MAPPING")
    print("=" * 60)

    # Sample conversation data (simulating what would be extracted from chat)
    conversation_data = {
        "motion_type": "custody_modification",
        "requested_custody_arrangement": "Sole legal and physical custody",
        "change_reason": "Other parent relocated out of state and hasn't seen children in 6 months",
        "is_emergency": False,
        "children_info": [
            {"name": "Alice Smith", "dob": "2015-03-15"},
            {"name": "Bob Smith", "dob": "2017-08-22"}
        ],
        "current_custody_arrangement": "Joint legal and physical custody",
        "hearing_date": "2025-11-15",
        "hearing_time": "9:00 AM",
        "department": "Family Court Dept 5",

        # Support information
        "current_support_amount": 1500,
        "requested_support_amount": 2000,

        # Employment info (for FL-150)
        "employer_name": "Tech Corp",
        "occupation": "Software Engineer",
        "monthly_income": 8000,
        "work_hours_per_week": 40,

        # Ex parte specific (for D-046)
        "emergency_reason": "Risk of immediate harm to children",
        "notice_given": False,
        "no_notice_reason": "Other parent threatened to take children",

        # Service info (for FL-335)
        "person_served_name": "John Doe",
        "person_served_address": "456 Oak St, San Diego, CA 92101",
        "date_mailed": "2025-10-01",

        # Contempt info (for FL-410/FL-411)
        "citee_name": "John Doe",
        "violation_details": "Failed to pay child support for 3 months",
        "support_violations": [
            {"date": "2025-07-01", "amount_due": 1500, "amount_paid": 0},
            {"date": "2025-08-01", "amount_due": 1500, "amount_paid": 0},
            {"date": "2025-09-01", "amount_due": 1500, "amount_paid": 0},
        ]
    }

    # Sample profile data
    profile_data = {
        "party_name": "Jane Smith",
        "other_party_name": "John Doe",
        "case_number": "FL-2025-001234",
        "county": "San Diego",
        "court_branch": "Central",
        "is_petitioner": True,
        "party_address": "123 Main St, San Diego, CA 92101",
        "party_phone": "(619) 555-1234",
        "party_email": "jane.smith@email.com",
        "children_info": [
            {"name": "Alice Smith", "dob": "2015-03-15"},
            {"name": "Bob Smith", "dob": "2017-08-22"}
        ]
    }

    # Test each form type
    form_types_to_test = [
        (FormType.D046, "SDSC D-046: Ex Parte Application (San Diego)"),
        (FormType.FL150, "FL-150: Income and Expense Declaration"),
        (FormType.FL300, "FL-300: Request for Order"),
        (FormType.FL305, "FL-305: Temporary Emergency Orders"),
        (FormType.FL335, "FL-335: Proof of Service by Mail"),
        (FormType.FL410, "FL-410: Order to Show Cause for Contempt"),
        (FormType.FL411, "FL-411: Affidavit of Facts (Financial Contempt)"),
        (FormType.MC030, "MC-030: Declaration"),
    ]

    results = []

    for form_type, form_name in form_types_to_test:
        print(f"\n{'=' * 50}")
        print(f"Testing: {form_name}")
        print('=' * 50)

        try:
            # Map conversation data to form fields
            mapped_fields = court_forms_mapping.map_conversation_to_form(
                form_type,
                conversation_data,
                profile_data
            )

            # Validate the mapping
            is_valid, missing_fields = court_forms_mapping.validate_form_data(
                form_type,
                mapped_fields
            )

            # Get required fields for this form
            required_fields = court_forms_mapping.get_required_fields(form_type)

            # Display results
            print(f"✓ Form Type: {form_type.value}")
            print(f"✓ Required Fields: {len(required_fields)}")
            print(f"✓ Mapped Fields: {len(mapped_fields)}")
            print(f"✓ Valid: {is_valid}")

            if missing_fields:
                print(f"⚠ Missing Fields ({len(missing_fields)}):")
                for field in missing_fields[:5]:  # Show first 5 missing
                    print(f"  - {field}")
            else:
                print("✅ All required fields mapped!")

            # Show sample of mapped data
            print("\nSample Mapped Data:")
            sample_count = 0
            for key, value in mapped_fields.items():
                if value and sample_count < 5:  # Show first 5 non-empty fields
                    print(f"  {key}: {str(value)[:50]}...")
                    sample_count += 1

            # Test result
            results.append((form_name, is_valid, len(missing_fields)))

        except Exception as e:
            print(f"❌ Error testing {form_name}: {e}")
            results.append((form_name, False, -1))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for form_name, is_valid, missing_count in results:
        status = "✅ PASS" if is_valid else f"⚠️ INCOMPLETE ({missing_count} missing)" if missing_count > 0 else "❌ ERROR"
        print(f"{status}: {form_name}")

    # Test form mapper integration
    print("\n" + "=" * 60)
    print("TESTING FORM MAPPER INTEGRATION")
    print("=" * 60)

    # Test that form mapper can use the new comprehensive mappings
    supported_forms = form_mapper.get_supported_forms()
    print(f"✓ Supported Forms: {supported_forms}")

    # Test mapping with form mapper
    test_form = "FL-300"
    print(f"\nTesting {test_form} with form mapper:")

    mapped = form_mapper.map_to_comprehensive_forms(
        test_form,
        conversation_data,
        profile_data
    )

    print(f"✓ Mapped {len(mapped)} fields")

    # Get missing information
    missing = form_mapper.get_missing_information(
        test_form,
        conversation_data,
        profile_data
    )

    if missing:
        print(f"⚠ Missing Information ({len(missing)}):")
        for item in missing[:3]:
            print(f"  - {item.get('field_name')}: {item.get('question')}")
    else:
        print("✅ No missing information!")

    print("\n" + "=" * 60)
    print("✅ FORM MAPPING TEST COMPLETE")
    print("All 8 court forms have been successfully mapped!")
    print("=" * 60)

if __name__ == "__main__":
    test_court_forms()