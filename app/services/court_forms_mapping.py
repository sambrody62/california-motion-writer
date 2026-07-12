"""
Court Forms Field Mapping Service
Maps conversation data to specific California court form fields
"""
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

class FormType(Enum):
    """Enum for all supported California court forms"""
    D046 = "SDSC D-046"  # Ex Parte Application and Order - Family Law (San Diego)
    FL150 = "FL-150"     # Income and Expense Declaration
    FL300 = "FL-300"     # Request for Order
    FL305 = "FL-305"     # Temporary Emergency (Ex Parte) Orders
    FL335 = "FL-335"     # Proof of Service by Mail
    FL410 = "FL-410"     # Order to Show Cause and Affidavit for Contempt
    FL411 = "FL-411"     # Affidavit of Facts Constituting Contempt (Financial)
    MC030 = "MC-030"     # Declaration (General)

@dataclass
class FormField:
    """Represents a field in a court form"""
    field_id: str
    field_name: str
    field_type: str  # text, checkbox, date, number, choice
    required: bool
    page_number: int
    description: str = ""
    options: List[str] = None

class CourtFormsMapping:
    """Comprehensive mapping for all 8 California court forms"""

    def __init__(self):
        self.form_definitions = self._initialize_form_definitions()

    def _initialize_form_definitions(self) -> Dict[FormType, Dict[str, FormField]]:
        """Initialize field definitions for all forms"""
        return {
            FormType.D046: self._get_d046_fields(),
            FormType.FL150: self._get_fl150_fields(),
            FormType.FL300: self._get_fl300_fields(),
            FormType.FL305: self._get_fl305_fields(),
            FormType.FL335: self._get_fl335_fields(),
            FormType.FL410: self._get_fl410_fields(),
            FormType.FL411: self._get_fl411_fields(),
            FormType.MC030: self._get_mc030_fields(),
        }

    def _get_d046_fields(self) -> Dict[str, FormField]:
        """SDSC D-046: Ex Parte Application and Order - San Diego specific"""
        return {
            # Header Information
            "attorney_name": FormField("attorney_name", "Attorney Name", "text", False, 1),
            "attorney_bar_number": FormField("attorney_bar_number", "State Bar Number", "text", False, 1),
            "attorney_address": FormField("attorney_address", "Attorney Address", "text", False, 1),
            "attorney_phone": FormField("attorney_phone", "Telephone Number", "text", True, 1),
            "attorney_fax": FormField("attorney_fax", "Fax Number", "text", False, 1),
            "attorney_email": FormField("attorney_email", "Email Address", "text", False, 1),
            "attorney_for": FormField("attorney_for", "Attorney For", "text", False, 1),

            # Court Information
            "court_division": FormField("court_division", "Court Division", "choice", True, 1,
                                       options=["Central", "East County", "North County", "South County"]),
            "petitioner_name": FormField("petitioner_name", "Petitioner Name", "text", True, 1),
            "respondent_name": FormField("respondent_name", "Respondent Name", "text", True, 1),
            "case_number": FormField("case_number", "Case Number", "text", True, 1),
            "judge_dept": FormField("judge_dept", "Judge/Department", "text", False, 1),

            # Hearing Information
            "hearing_date": FormField("hearing_date", "Hearing Date", "date", False, 1),
            "hearing_time": FormField("hearing_time", "Hearing Time", "text", False, 1),
            "hearing_am_pm": FormField("hearing_am_pm", "AM/PM", "choice", False, 1, options=["a.m.", "p.m."]),
            "hearing_opposed": FormField("hearing_opposed", "Opposed/Unopposed", "choice", False, 1,
                                        options=["Opposed", "Unopposed"]),

            # Relief Requested
            "relief_type_tro": FormField("relief_type_tro", "Temporary Restraining Orders", "checkbox", False, 1),
            "relief_type_custody": FormField("relief_type_custody", "Child Custody/Visitation Order", "checkbox", False, 1),
            "relief_type_ost": FormField("relief_type_ost", "Order Shortening Time", "checkbox", False, 1),
            "relief_type_signature": FormField("relief_type_signature", "Order Being Submitted for Signature", "checkbox", False, 1),
            "relief_type_other": FormField("relief_type_other", "Other Relief", "text", False, 1),
            "ex_parte_necessity": FormField("ex_parte_necessity", "Why Ex Parte Relief is Necessary", "text", True, 1),

            # Notice Information
            "opposing_party_name": FormField("opposing_party_name", "Name of Opposing Attorney/Party", "text", True, 1),
            "notice_given": FormField("notice_given", "Was Notice Given", "checkbox", False, 1),
            "notice_date": FormField("notice_date", "Notice Date", "date", False, 1),
            "notice_time": FormField("notice_time", "Notice Time", "text", False, 1),
            "no_notice_reason": FormField("no_notice_reason", "Reason if No Notice", "text", False, 1),

            # Supporting Documents
            "declarations_submitted": FormField("declarations_submitted", "Evidentiary Declarations Submitted", "checkbox", False, 1),
            "proposed_order_submitted": FormField("proposed_order_submitted", "Proposed Order Submitted", "checkbox", False, 1),
            "previous_ex_parte": FormField("previous_ex_parte", "Previous Ex Parte for Same Relief", "checkbox", False, 1),
            "previous_result": FormField("previous_result", "Previous Result", "choice", False, 1,
                                        options=["granted", "denied"]),

            # Declaration
            "declaration_date": FormField("declaration_date", "Declaration Date", "date", True, 1),
            "applicant_signature": FormField("applicant_signature", "Applicant Signature", "text", True, 1),
        }

    def _get_fl150_fields(self) -> Dict[str, FormField]:
        """FL-150: Income and Expense Declaration"""
        return {
            # Employment Information
            "employer_name": FormField("employer_name", "Employer Name", "text", True, 1),
            "employer_address": FormField("employer_address", "Employer Address", "text", True, 1),
            "employer_phone": FormField("employer_phone", "Employer Phone", "text", True, 1),
            "occupation": FormField("occupation", "Occupation", "text", True, 1),
            "date_job_started": FormField("date_job_started", "Date Job Started", "date", True, 1),
            "date_job_ended": FormField("date_job_ended", "Date Job Ended (if unemployed)", "date", False, 1),
            "work_hours_per_week": FormField("work_hours_per_week", "Hours Worked Per Week", "number", True, 1),
            "gross_income": FormField("gross_income", "Gross Income", "number", True, 1),
            "income_frequency": FormField("income_frequency", "Income Frequency", "choice", True, 1,
                                        options=["per month", "per week", "per hour"]),

            # Personal Information
            "age": FormField("age", "Age", "number", True, 1),
            "high_school_completed": FormField("high_school_completed", "Completed High School", "checkbox", True, 1),
            "highest_grade": FormField("highest_grade", "Highest Grade Completed", "text", False, 1),
            "college_years": FormField("college_years", "Years of College", "number", False, 1),
            "college_degree": FormField("college_degree", "College Degree(s)", "text", False, 1),
            "graduate_years": FormField("graduate_years", "Years of Graduate School", "number", False, 1),
            "graduate_degree": FormField("graduate_degree", "Graduate Degree(s)", "text", False, 1),
            "professional_licenses": FormField("professional_licenses", "Professional Licenses", "text", False, 1),
            "vocational_training": FormField("vocational_training", "Vocational Training", "text", False, 1),

            # Tax Information
            "tax_year": FormField("tax_year", "Last Tax Year Filed", "text", True, 1),
            "tax_filing_status": FormField("tax_filing_status", "Tax Filing Status", "choice", True, 1,
                                          options=["single", "head of household", "married filing separately",
                                                  "married filing jointly"]),
            "tax_state": FormField("tax_state", "State for Tax Returns", "text", True, 1),
            "tax_exemptions": FormField("tax_exemptions", "Number of Exemptions", "number", True, 1),

            # Income Details (Page 2)
            "salary_wages": FormField("salary_wages", "Salary/Wages (monthly)", "number", True, 2),
            "overtime": FormField("overtime", "Overtime (monthly)", "number", False, 2),
            "commissions": FormField("commissions", "Commissions/Bonuses (monthly)", "number", False, 2),
            "public_assistance": FormField("public_assistance", "Public Assistance", "number", False, 2),
            "spousal_support_received": FormField("spousal_support_received", "Spousal Support Received", "number", False, 2),
            "pension_retirement": FormField("pension_retirement", "Pension/Retirement", "number", False, 2),
            "social_security": FormField("social_security", "Social Security", "number", False, 2),
            "disability_income": FormField("disability_income", "Disability Income", "number", False, 2),
            "unemployment": FormField("unemployment", "Unemployment Compensation", "number", False, 2),
            "workers_comp": FormField("workers_comp", "Workers Compensation", "number", False, 2),

            # Expenses (Page 3)
            "rent_mortgage": FormField("rent_mortgage", "Rent or Mortgage", "number", True, 3),
            "real_property_taxes": FormField("real_property_taxes", "Property Taxes", "number", False, 3),
            "home_insurance": FormField("home_insurance", "Homeowner's Insurance", "number", False, 3),
            "health_care_costs": FormField("health_care_costs", "Health Care Costs", "number", False, 3),
            "child_care": FormField("child_care", "Child Care", "number", False, 3),
            "groceries": FormField("groceries", "Groceries and Household", "number", True, 3),
            "eating_out": FormField("eating_out", "Eating Out", "number", False, 3),
            "utilities": FormField("utilities", "Utilities", "number", True, 3),
            "telephone": FormField("telephone", "Telephone/Cell Phone", "number", True, 3),
            "laundry_cleaning": FormField("laundry_cleaning", "Laundry and Cleaning", "number", False, 3),
            "clothes": FormField("clothes", "Clothes", "number", False, 3),
            "education": FormField("education", "Education", "number", False, 3),
            "entertainment": FormField("entertainment", "Entertainment/Gifts", "number", False, 3),
            "auto_expenses": FormField("auto_expenses", "Auto Expenses", "number", True, 3),

            # Child Support Information (Page 4)
            "number_of_children": FormField("number_of_children", "Number of Children", "number", False, 4),
            "time_with_children": FormField("time_with_children", "Percentage Time with Children", "number", False, 4),
            "children_health_insurance": FormField("children_health_insurance", "Children's Health Insurance Available", "checkbox", False, 4),
            "insurance_company": FormField("insurance_company", "Insurance Company Name", "text", False, 4),
            "insurance_cost_children": FormField("insurance_cost_children", "Monthly Cost for Children's Insurance", "number", False, 4),
        }

    def _get_fl300_fields(self) -> Dict[str, FormField]:
        """FL-300: Request for Order"""
        return {
            # Header and Court Information
            "petitioner_name": FormField("petitioner_name", "Petitioner Name", "text", True, 1),
            "respondent_name": FormField("respondent_name", "Respondent Name", "text", True, 1),
            "other_parent_name": FormField("other_parent_name", "Other Parent/Party Name", "text", False, 1),
            "case_number": FormField("case_number", "Case Number", "text", True, 1),

            # Type of Request
            "request_change": FormField("request_change", "Request is a Change", "checkbox", False, 1),
            "request_temporary": FormField("request_temporary", "Request Temporary Emergency Orders", "checkbox", False, 1),
            "request_child_custody": FormField("request_child_custody", "Child Custody", "checkbox", False, 1),
            "request_visitation": FormField("request_visitation", "Visitation (Parenting Time)", "checkbox", False, 1),
            "request_child_support": FormField("request_child_support", "Child Support", "checkbox", False, 1),
            "request_spousal_support": FormField("request_spousal_support", "Spousal or Partner Support", "checkbox", False, 1),
            "request_property_control": FormField("request_property_control", "Property Control", "checkbox", False, 1),
            "request_attorneys_fees": FormField("request_attorneys_fees", "Attorney's Fees and Costs", "checkbox", False, 1),
            "request_other": FormField("request_other", "Other Request", "text", False, 1),

            # Notice of Hearing
            "notice_to": FormField("notice_to", "Notice To (Name)", "text", True, 1),
            "notice_party_type": FormField("notice_party_type", "Party Type for Notice", "choice", False, 1,
                                          options=["Petitioner", "Respondent", "Other Parent/Party", "Other"]),
            "hearing_date": FormField("hearing_date", "Hearing Date", "date", False, 1),
            "hearing_time": FormField("hearing_time", "Hearing Time", "text", False, 1),
            "hearing_dept": FormField("hearing_dept", "Department", "text", False, 1),
            "hearing_room": FormField("hearing_room", "Room", "text", False, 1),
            "court_address": FormField("court_address", "Court Address", "text", False, 1),

            # Restraining Order Information (Page 2)
            "existing_restraining_orders": FormField("existing_restraining_orders", "Existing Restraining Orders", "checkbox", False, 2),
            "restraining_parties": FormField("restraining_parties", "Parties in Restraining Order", "text", False, 2),
            "criminal_case_info": FormField("criminal_case_info", "Criminal Case Info", "text", False, 2),
            "family_case_info": FormField("family_case_info", "Family Case Info", "text", False, 2),
            "juvenile_case_info": FormField("juvenile_case_info", "Juvenile Case Info", "text", False, 2),

            # Child Custody/Visitation (Page 2)
            "children_info": FormField("children_info", "Children Information", "text", True, 2,
                                      description="List of children with names, DOB, physical and legal custody"),
            "custody_best_interest_reason": FormField("custody_best_interest_reason",
                                                     "Why Orders are in Best Interest", "text", True, 2),
            "change_from_current": FormField("change_from_current", "This is a Change from Current Order", "checkbox", False, 2),
            "current_order_date": FormField("current_order_date", "Current Order Date", "date", False, 2),
            "current_order_details": FormField("current_order_details", "Current Order Details", "text", False, 2),

            # Child Support (Page 3)
            "child_support_requested": FormField("child_support_requested", "Child Support Amount Requested", "number", False, 3),
            "guideline_support": FormField("guideline_support", "Request Guideline Support", "checkbox", False, 3),
            "change_current_support": FormField("change_current_support", "Change Current Support Order", "checkbox", False, 3),
            "current_support_date": FormField("current_support_date", "Current Support Order Date", "date", False, 3),
            "support_change_reason": FormField("support_change_reason", "Reason for Support Change", "text", False, 3),
            "fl150_attached": FormField("fl150_attached", "Income and Expense Declaration Attached", "checkbox", True, 3),

            # Spousal Support (Page 3)
            "spousal_support_amount": FormField("spousal_support_amount", "Spousal Support Amount", "number", False, 3),
            "modify_spousal_support": FormField("modify_spousal_support", "Modify Spousal Support", "checkbox", False, 3),
            "end_spousal_support": FormField("end_spousal_support", "End Spousal Support", "checkbox", False, 3),
            "spousal_support_reason": FormField("spousal_support_reason", "Reason for Spousal Support Request", "text", False, 3),

            # Property Control (Page 4)
            "property_control_party": FormField("property_control_party", "Party for Property Control", "choice", False, 4,
                                               options=["petitioner", "respondent", "other parent/party"]),
            "property_description": FormField("property_description", "Property Description", "text", False, 4),
            "debt_payments": FormField("debt_payments", "Debt Payment Details", "text", False, 4),

            # Attorney's Fees (Page 4)
            "attorney_fees_amount": FormField("attorney_fees_amount", "Attorney's Fees Amount", "number", False, 4),
            "fl319_attached": FormField("fl319_attached", "Request for Attorney's Fees Attachment", "checkbox", False, 4),
            "fl158_attached": FormField("fl158_attached", "Supporting Declaration Attached", "checkbox", False, 4),

            # Other Orders (Page 4)
            "other_orders": FormField("other_orders", "Other Orders Requested", "text", False, 4),

            # Time for Service (Page 4)
            "expedited_service": FormField("expedited_service", "Need Expedited Service", "checkbox", False, 4),
            "service_days": FormField("service_days", "Number of Court Days for Service", "number", False, 4),
            "expedited_reason": FormField("expedited_reason", "Reason for Expedited Service", "text", False, 4),

            # Supporting Facts (Page 4)
            "supporting_facts": FormField("supporting_facts", "Facts Supporting Request", "text", True, 4,
                                         description="Limited to 10 pages unless court permission"),

            # Declaration
            "declaration_date": FormField("declaration_date", "Declaration Date", "date", True, 4),
            "declarant_signature": FormField("declarant_signature", "Declarant Signature", "text", True, 4),
        }

    def _get_fl305_fields(self) -> Dict[str, FormField]:
        """FL-305: Temporary Emergency (Ex Parte) Orders"""
        return {
            # Court and Party Information
            "petitioner_name": FormField("petitioner_name", "Petitioner Name", "text", True, 1),
            "respondent_name": FormField("respondent_name", "Respondent Name", "text", True, 1),
            "other_parent_name": FormField("other_parent_name", "Other Parent/Party Name", "text", False, 1),
            "case_number": FormField("case_number", "Case Number", "text", True, 1),

            # Order Types
            "order_child_custody": FormField("order_child_custody", "Child Custody Order", "checkbox", False, 1),
            "order_visitation": FormField("order_visitation", "Visitation Order", "checkbox", False, 1),
            "order_property_control": FormField("order_property_control", "Property Control Order", "checkbox", False, 1),
            "order_other": FormField("order_other", "Other Order", "text", False, 1),

            # Notice Information
            "notice_to_party": FormField("notice_to_party", "Notice To Party Name", "text", True, 1),
            "notice_party_type": FormField("notice_party_type", "Party Type", "choice", False, 1,
                                          options=["Petitioner", "Respondent", "Other Parent/Party", "Other"]),

            # Hearing Information
            "hearing_date": FormField("hearing_date", "Hearing Date", "date", True, 1),
            "hearing_time": FormField("hearing_time", "Hearing Time", "text", True, 1),
            "hearing_dept": FormField("hearing_dept", "Department", "text", False, 1),
            "hearing_room": FormField("hearing_room", "Room", "text", False, 1),
            "court_address": FormField("court_address", "Court Address", "text", False, 1),

            # Findings
            "findings_immediate_harm": FormField("findings_immediate_harm", "Immediate Harm Finding", "checkbox", True, 1),
            "findings_property_loss": FormField("findings_property_loss", "Property Loss Finding", "checkbox", False, 1),
            "findings_procedure_change": FormField("findings_procedure_change", "Procedure Change Finding", "checkbox", False, 1),

            # Child Custody Orders
            "custody_children": FormField("custody_children", "Children for Custody Orders", "text", False, 1,
                                         description="List children names and dates of birth"),
            "physical_custody_to": FormField("physical_custody_to", "Physical Custody To", "choice", False, 1,
                                            options=["Petitioner", "Respondent", "Other Party/Parent"]),
            "visitation_schedule": FormField("visitation_schedule", "Visitation Schedule", "text", False, 1),

            # Travel Restrictions (Page 2)
            "no_remove_from_california": FormField("no_remove_from_california", "Cannot Remove from California", "checkbox", False, 2),
            "travel_restrict_party": FormField("travel_restrict_party", "Party with Travel Restrictions", "choice", False, 2,
                                              options=["Petitioner", "Respondent", "Other Parent/Party"]),
            "travel_restrict_counties": FormField("travel_restrict_counties", "Cannot Remove from Counties", "text", False, 2),
            "travel_restrict_other": FormField("travel_restrict_other", "Other Travel Restrictions", "text", False, 2),

            # Child Abduction Prevention
            "abduction_prevention": FormField("abduction_prevention", "Child Abduction Prevention Orders", "checkbox", False, 2),

            # Jurisdiction
            "uccjea_jurisdiction": FormField("uccjea_jurisdiction", "UCCJEA Jurisdiction", "checkbox", True, 2),
            "notice_opportunity": FormField("notice_opportunity", "Notice and Opportunity to be Heard", "checkbox", True, 2),
            "habitual_residence": FormField("habitual_residence", "Country of Habitual Residence", "text", False, 2),

            # Property Control
            "property_control_party": FormField("property_control_party", "Party with Property Control", "choice", False, 2,
                                               options=["Petitioner", "Respondent", "Other Parent/Party"]),
            "property_description": FormField("property_description", "Property Description", "text", False, 2),
            "property_own_buy": FormField("property_own_buy", "Own or Buying", "checkbox", False, 2),
            "property_lease_rent": FormField("property_lease_rent", "Lease or Rent", "checkbox", False, 2),

            # Debt Payments
            "debt_pay_to": FormField("debt_pay_to", "Pay Debt To", "text", False, 2),
            "debt_for": FormField("debt_for", "Debt For", "text", False, 2),
            "debt_amount": FormField("debt_amount", "Debt Amount", "number", False, 2),
            "debt_due_date": FormField("debt_due_date", "Debt Due Date", "date", False, 2),

            # Other Orders
            "other_orders": FormField("other_orders", "Other Orders", "text", False, 2),
            "existing_orders_remain": FormField("existing_orders_remain", "Existing Orders Remain in Effect", "checkbox", False, 2),

            # Judge Signature
            "order_date": FormField("order_date", "Order Date", "date", True, 2),
        }

    def _get_fl335_fields(self) -> Dict[str, FormField]:
        """FL-335: Proof of Service by Mail"""
        return {
            # Case Information
            "petitioner_name": FormField("petitioner_name", "Petitioner/Plaintiff Name", "text", True, 1),
            "respondent_name": FormField("respondent_name", "Respondent/Defendant Name", "text", True, 1),
            "other_parent_name": FormField("other_parent_name", "Other Parent/Party Name", "text", False, 1),
            "case_number": FormField("case_number", "Case Number", "text", True, 1),
            "hearing_date": FormField("hearing_date", "Hearing Date", "date", False, 1),
            "hearing_time": FormField("hearing_time", "Hearing Time", "text", False, 1),
            "hearing_dept": FormField("hearing_dept", "Department", "text", False, 1),

            # Server Information
            "server_age_declaration": FormField("server_age_declaration", "Server is 18+ and Not a Party", "checkbox", True, 1),
            "server_address": FormField("server_address", "Server's Residence or Business Address", "text", True, 1),

            # Service Method
            "service_method_usps": FormField("service_method_usps", "Deposited with USPS", "checkbox", False, 1),
            "service_method_business": FormField("service_method_business", "Business Mail Practice", "checkbox", False, 1),

            # Documents Served
            "documents_served": FormField("documents_served", "Documents Served", "text", True, 1,
                                         description="List all documents that were served"),

            # Service Details
            "person_served_name": FormField("person_served_name", "Name of Person Served", "text", True, 1),
            "person_served_address": FormField("person_served_address", "Address Where Served", "text", True, 1),
            "date_mailed": FormField("date_mailed", "Date Mailed", "date", True, 1),
            "place_mailing": FormField("place_mailing", "Place of Mailing (City and State)", "text", True, 1),

            # Special Service Requirements
            "address_verification": FormField("address_verification", "Address Verification for Support Modification", "checkbox", False, 1),

            # Declaration
            "declaration_date": FormField("declaration_date", "Declaration Date", "date", True, 1),
            "server_name": FormField("server_name", "Server Name (Type or Print)", "text", True, 1),
            "server_signature": FormField("server_signature", "Server Signature", "text", True, 1),
        }

    def _get_fl410_fields(self) -> Dict[str, FormField]:
        """FL-410: Order to Show Cause and Affidavit for Contempt"""
        return {
            # Case and Party Information
            "petitioner_name": FormField("petitioner_name", "Petitioner/Plaintiff Name", "text", True, 1),
            "respondent_name": FormField("respondent_name", "Respondent/Defendant Name", "text", True, 1),
            "other_parent_name": FormField("other_parent_name", "Other Party/Parent Name", "text", False, 1),
            "case_number": FormField("case_number", "Case Number", "text", True, 1),

            # Citee Information
            "citee_name": FormField("citee_name", "Name of Person Alleged to Violate Orders", "text", True, 1),

            # Hearing Information
            "hearing_date": FormField("hearing_date", "Hearing Date", "date", False, 1),
            "hearing_time": FormField("hearing_time", "Hearing Time", "text", False, 1),
            "hearing_dept": FormField("hearing_dept", "Department", "text", False, 1),
            "hearing_room": FormField("hearing_room", "Room", "text", False, 1),
            "court_address": FormField("court_address", "Court Address", "text", False, 1),

            # Affidavit Supporting Contempt
            "fl411_attached": FormField("fl411_attached", "FL-411 Attached (Financial Orders)", "checkbox", False, 1),
            "fl412_attached": FormField("fl412_attached", "FL-412 Attached (DV/Custody Orders)", "checkbox", False, 1),

            # Knowledge of Order
            "citee_present_in_court": FormField("citee_present_in_court", "Citee Present When Order Made", "checkbox", False, 1),
            "citee_served": FormField("citee_served", "Citee Was Served", "checkbox", False, 1),
            "citee_signed_stipulation": FormField("citee_signed_stipulation", "Citee Signed Stipulation", "checkbox", False, 1),
            "citee_knowledge_other": FormField("citee_knowledge_other", "Other Way Citee Knew", "text", False, 1),

            # Ability to Comply
            "citee_able_to_comply": FormField("citee_able_to_comply", "Citee Was Able to Comply", "checkbox", True, 1),

            # Previous Contempt
            "no_previous_contempt": FormField("no_previous_contempt", "No Previous Contempt Request", "checkbox", False, 1),
            "previous_contempt_details": FormField("previous_contempt_details", "Previous Contempt Details", "text", False, 1),
            "citee_previous_contempt": FormField("citee_previous_contempt", "Citee Previously Found in Contempt", "text", False, 2),

            # Order Violations (Page 2)
            "support_order_violations": FormField("support_order_violations", "Support Order Violations", "checkbox", False, 2),
            "dv_custody_violations": FormField("dv_custody_violations", "DV/Custody Order Violations", "checkbox", False, 2),
            "injunctive_violations": FormField("injunctive_violations", "Injunctive Order Violations", "text", False, 2),
            "other_material_facts": FormField("other_material_facts", "Other Material Facts", "text", False, 2),

            # Attorney Fees
            "request_attorney_fees": FormField("request_attorney_fees", "Request Attorney Fees", "checkbox", False, 2),
            "fl150_attached": FormField("fl150_attached", "Income and Expense Declaration Attached", "checkbox", False, 2),

            # Warning
            "da_prosecution_warning": FormField("da_prosecution_warning", "DA Prosecution Warning Acknowledged", "checkbox", True, 2),

            # Declaration
            "declaration_date": FormField("declaration_date", "Declaration Date", "date", True, 2),
            "declarant_name": FormField("declarant_name", "Declarant Name", "text", True, 2),
            "declarant_signature": FormField("declarant_signature", "Declarant Signature", "text", True, 2),
        }

    def _get_fl411_fields(self) -> Dict[str, FormField]:
        """FL-411: Affidavit of Facts Constituting Contempt (Financial and Injunctive Orders)"""
        return {
            # Case Information
            "petitioner_name": FormField("petitioner_name", "Petitioner/Plaintiff Name", "text", True, 1),
            "respondent_name": FormField("respondent_name", "Respondent/Defendant Name", "text", True, 1),
            "other_parent_name": FormField("other_parent_name", "Other Parent/Party Name", "text", False, 1),
            "case_number": FormField("case_number", "Case Number", "text", True, 1),

            # Financial Order Violations
            "support_violations": FormField("support_violations", "Support Payment Violations", "text", False, 1,
                                           description="Table of missed payments with dates, types, amounts"),

            # Support Violation Details
            "child_support_ordered": FormField("child_support_ordered", "Total Child Support Ordered", "number", False, 1),
            "child_support_paid": FormField("child_support_paid", "Total Child Support Paid", "number", False, 1),
            "child_support_due": FormField("child_support_due", "Total Child Support Due", "number", False, 1),

            "spousal_support_ordered": FormField("spousal_support_ordered", "Total Spousal Support Ordered", "number", False, 1),
            "spousal_support_paid": FormField("spousal_support_paid", "Total Spousal Support Paid", "number", False, 1),
            "spousal_support_due": FormField("spousal_support_due", "Total Spousal Support Due", "number", False, 1),

            "family_support_ordered": FormField("family_support_ordered", "Total Family Support Ordered", "number", False, 1),
            "family_support_paid": FormField("family_support_paid", "Total Family Support Paid", "number", False, 1),
            "family_support_due": FormField("family_support_due", "Total Family Support Due", "number", False, 1),

            "attorney_fees_ordered": FormField("attorney_fees_ordered", "Total Attorney Fees Ordered", "number", False, 1),
            "attorney_fees_paid": FormField("attorney_fees_paid", "Total Attorney Fees Paid", "number", False, 1),
            "attorney_fees_due": FormField("attorney_fees_due", "Total Attorney Fees Due", "number", False, 1),

            "court_costs_ordered": FormField("court_costs_ordered", "Total Court Costs Ordered", "number", False, 1),
            "court_costs_paid": FormField("court_costs_paid", "Total Court Costs Paid", "number", False, 1),
            "court_costs_due": FormField("court_costs_due", "Total Court Costs Due", "number", False, 1),

            "total_amount_ordered": FormField("total_amount_ordered", "Grand Total Ordered", "number", True, 1),
            "total_amount_paid": FormField("total_amount_paid", "Grand Total Paid", "number", True, 1),
            "total_amount_due": FormField("total_amount_due", "Grand Total Due", "number", True, 1),

            # Other Order Violations
            "other_order_violations": FormField("other_order_violations", "Other Order Violations", "text", False, 1),

            # Other Material Facts
            "other_material_facts": FormField("other_material_facts", "Other Material Facts", "text", False, 1),

            # Declaration
            "declaration_date": FormField("declaration_date", "Declaration Date", "date", True, 1),
            "declarant_name": FormField("declarant_name", "Declarant Name", "text", True, 1),
            "declarant_signature": FormField("declarant_signature", "Declarant Signature", "text", True, 1),
        }

    def _get_mc030_fields(self) -> Dict[str, FormField]:
        """MC-030: Declaration (General Purpose)"""
        return {
            # Case Information
            "plaintiff_petitioner": FormField("plaintiff_petitioner", "Plaintiff/Petitioner Name", "text", True, 1),
            "defendant_respondent": FormField("defendant_respondent", "Defendant/Respondent Name", "text", True, 1),
            "case_number": FormField("case_number", "Case Number", "text", True, 1),

            # Declarant Information
            "declarant_type": FormField("declarant_type", "Declarant Type", "choice", False, 1,
                                       options=["Plaintiff", "Defendant", "Petitioner", "Respondent", "Other"]),
            "declarant_attorney_for": FormField("declarant_attorney_for", "Attorney For", "text", False, 1),

            # Declaration Content
            "declaration_text": FormField("declaration_text", "Declaration Text", "text", True, 1,
                                         description="Main body of the declaration - facts and statements"),

            # Signature
            "declaration_date": FormField("declaration_date", "Declaration Date", "date", True, 1),
            "declarant_name": FormField("declarant_name", "Declarant Name (Type or Print)", "text", True, 1),
            "declarant_signature": FormField("declarant_signature", "Declarant Signature", "text", True, 1),
        }

    def map_conversation_to_form(
        self,
        form_type: FormType,
        conversation_data: Dict[str, Any],
        profile_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map conversation and profile data to specific form fields

        Args:
            form_type: The type of form to map to
            conversation_data: Extracted data from chat conversation
            profile_data: User's saved profile information

        Returns:
            Dictionary of mapped form fields with values
        """
        form_fields = self.form_definitions.get(form_type, {})
        mapped_data = {}

        # Combine data sources for mapping
        combined_data = {**profile_data, **conversation_data}

        # Map common fields that appear across multiple forms
        common_mappings = {
            "petitioner_name": combined_data.get("party_name") if combined_data.get("is_petitioner") else combined_data.get("other_party_name"),
            "respondent_name": combined_data.get("other_party_name") if combined_data.get("is_petitioner") else combined_data.get("party_name"),
            "case_number": combined_data.get("case_number"),
            "attorney_name": combined_data.get("attorney_name"),
            "attorney_phone": combined_data.get("attorney_phone") or combined_data.get("party_phone"),
            "attorney_email": combined_data.get("attorney_email") or combined_data.get("party_email"),
            "hearing_date": combined_data.get("hearing_date"),
            "hearing_time": combined_data.get("hearing_time"),
            "hearing_dept": combined_data.get("department"),
        }

        # Apply common mappings
        for field_key, field_def in form_fields.items():
            if field_key in common_mappings and common_mappings[field_key]:
                mapped_data[field_key] = common_mappings[field_key]

        # Form-specific mappings
        if form_type == FormType.FL300:
            mapped_data.update(self._map_fl300_specific(combined_data))
        elif form_type == FormType.FL150:
            mapped_data.update(self._map_fl150_specific(combined_data))
        elif form_type == FormType.D046:
            mapped_data.update(self._map_d046_specific(combined_data))
        # Add other form-specific mappings as needed

        return mapped_data

    def _map_fl300_specific(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map data specifically for FL-300 Request for Order"""
        mapped = {}

        # Request type checkboxes based on motion type
        motion_type = data.get("motion_type", "").lower()
        if "custody" in motion_type:
            mapped["request_child_custody"] = True
        if "support" in motion_type:
            mapped["request_child_support"] = True
        if "visitation" in motion_type or "parenting" in motion_type:
            mapped["request_visitation"] = True
        if "emergency" in data and data["emergency"]:
            mapped["request_temporary"] = True

        # Children information
        if data.get("children_info"):
            children_text = ""
            for child in data["children_info"]:
                children_text += f"{child.get('name', '')}, DOB: {child.get('dob', '')}\\n"
            mapped["children_info"] = children_text

        # Support amounts
        if data.get("requested_support_amount"):
            mapped["child_support_requested"] = data["requested_support_amount"]

        # Custody arrangements
        if data.get("requested_custody_arrangement"):
            mapped["custody_best_interest_reason"] = data["requested_custody_arrangement"]

        # Supporting facts
        if data.get("change_reason"):
            mapped["supporting_facts"] = data["change_reason"]

        return mapped

    def _map_fl150_specific(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map data specifically for FL-150 Income and Expense Declaration"""
        mapped = {}

        # Employment information
        if data.get("employer_name"):
            mapped["employer_name"] = data["employer_name"]
        if data.get("occupation"):
            mapped["occupation"] = data["occupation"]
        if data.get("monthly_income"):
            mapped["gross_income"] = data["monthly_income"]
            mapped["salary_wages"] = data["monthly_income"]

        # Personal information
        if data.get("age"):
            mapped["age"] = data["age"]

        # Expenses
        if data.get("monthly_expenses"):
            expenses = data["monthly_expenses"]
            mapped["rent_mortgage"] = expenses.get("housing", 0)
            mapped["utilities"] = expenses.get("utilities", 0)
            mapped["groceries"] = expenses.get("food", 0)
            mapped["child_care"] = expenses.get("childcare", 0)

        # Children information
        if data.get("children_info"):
            mapped["number_of_children"] = len(data["children_info"])

        return mapped

    def _map_d046_specific(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map data specifically for SDSC D-046 Ex Parte Application"""
        mapped = {}

        # San Diego specific court division
        if data.get("county") == "San Diego":
            if data.get("court_branch"):
                mapped["court_division"] = data["court_branch"]
            else:
                # Default to Central if not specified
                mapped["court_division"] = "Central"

        # Ex parte specific fields
        if data.get("is_emergency"):
            mapped["relief_type_tro"] = True
            mapped["ex_parte_necessity"] = data.get("emergency_reason", "Immediate harm to children")

        # Notice information
        if data.get("notice_given") is False:
            mapped["no_notice_reason"] = data.get("no_notice_reason", "Risk of harm to children")

        return mapped

    def get_required_fields(self, form_type: FormType) -> List[str]:
        """Get list of required fields for a form"""
        form_fields = self.form_definitions.get(form_type, {})
        return [
            field_key for field_key, field_def in form_fields.items()
            if field_def.required
        ]

    def validate_form_data(
        self,
        form_type: FormType,
        form_data: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """
        Validate that all required fields are present

        Returns:
            Tuple of (is_valid, list_of_missing_fields)
        """
        required_fields = self.get_required_fields(form_type)
        missing_fields = []

        for field in required_fields:
            if field not in form_data or not form_data[field]:
                missing_fields.append(field)

        return len(missing_fields) == 0, missing_fields

    def get_form_description(self, form_type: FormType) -> str:
        """Get a description of what the form is used for"""
        descriptions = {
            FormType.D046: "Ex Parte Application for emergency orders in San Diego County",
            FormType.FL150: "Income and Expense Declaration for support calculations",
            FormType.FL300: "Request for Order - main form for requesting court orders",
            FormType.FL305: "Temporary Emergency Orders issued on ex parte basis",
            FormType.FL335: "Proof of Service by Mail to prove documents were served",
            FormType.FL410: "Order to Show Cause for Contempt when orders are violated",
            FormType.FL411: "Affidavit supporting contempt for financial violations",
            FormType.MC030: "General declaration form for stating facts under penalty of perjury",
        }
        return descriptions.get(form_type, "Court form")

# Singleton instance
court_forms_mapping = CourtFormsMapping()