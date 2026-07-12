# San Diego Violation Filing Integration

## ✅ Completed Integration

I've successfully integrated the San Diego Family Court violation filing forms into your California Motion Writer application. Here's what was implemented:

## 📁 Forms Added

All 8 required forms for San Diego violation filings have been added:

1. **D-046** - Ex Parte Application and Order (San Diego specific)
2. **FL-300** - Request for Order (main form)
3. **FL-305** - Temporary Orders
4. **FL-335** - Continuance of Hearing
5. **FL-410** - Order to Show Cause and Affidavit for Contempt
6. **FL-411** - Order to Show Cause (Contempt)
7. **FL-150** - Income and Expense Declaration
8. **MC-030** - Declaration

## 🏗️ Architecture Created

### 1. Forms Organization
```
forms/san-diego-violation/
├── d046.pdf
├── fl150.pdf
├── fl300.pdf
├── fl305.pdf
├── fl335.pdf
├── fl410.pdf
├── fl411 .pdf
├── mc030.pdf
├── FORMS-OVERVIEW.md          # Complete documentation
└── form-config.json          # Form configuration and mapping
```

### 2. Service Layer (`app/services/violation_service.py`)
- **ViolationFilingService** class handles all violation logic
- Determines filing track (emergency/regular/contempt)
- Generates declarations from intake data
- Provides filing instructions
- Determines correct courthouse

### 3. API Endpoints (`app/api/v1/endpoints/violations.py`)

#### Available Endpoints:

**POST `/api/v1/violations/process`**
- Process complete violation filing
- Returns track, forms, declaration, and instructions

**GET `/api/v1/violations/tracks`**
- Get available filing tracks and descriptions

**GET `/api/v1/violations/intake-questions`**
- Get dynamic intake questions

**GET `/api/v1/violations/forms/{track}`**
- Get required forms for specific track

**POST `/api/v1/violations/generate-declaration`**
- Generate MC-030 declaration from intake data

### 4. Database Updates
- Enhanced Motion model with violation-specific fields
- Added MotionType enum including VIOLATION, EX_PARTE, CONTEMPT
- Store filing track, courthouse, intake data

## 📋 Three Filing Tracks

### 1. **Emergency (Ex Parte) Track**
- Timeline: 24-48 hours
- Forms: D-046, FL-300, MC-030
- For urgent violations requiring immediate relief

### 2. **Regular Track**
- Timeline: 3-6 weeks
- Forms: FL-300, MC-030, optionally FL-150
- Standard violation filing process

### 3. **Contempt Track**
- Timeline: 4-8 weeks
- Forms: FL-410, FL-411, MC-030
- For serious, willful violations with criminal consequences

## 🔄 Workflow

### User Flow:
1. User reports violation through intake questions
2. System determines appropriate track based on urgency
3. System identifies required forms
4. LLM generates formal declaration from user input
5. System provides:
   - List of forms to complete
   - Pre-filled declaration
   - Step-by-step filing instructions
   - Correct courthouse location
   - Service requirements

### Intelligent Features:
- **Auto Track Selection**: Based on violation type and urgency
- **Courthouse Routing**: Selects correct division based on user location
- **Declaration Generation**: Converts plain language to legal format
- **Service Requirements**: Different for each track type

## 📊 Intake Questions

Comprehensive intake captures:
- Violation type (custody, support, property, etc.)
- Urgency level
- Violation dates and details
- Available evidence
- Prior violations history
- Attempted resolution
- Requested relief

## 🏛️ San Diego Courthouses

System knows all 4 divisions:
1. **Central**: 1100 Union St., San Diego
2. **East County**: 250 E. Main St., El Cajon
3. **North County**: 325 S. Melrose Dr., Vista
4. **South County**: 500 3rd Ave., Chula Vista

## 💻 Testing the Integration

To test the violation filing system:

```python
# Example API call
POST /api/v1/violations/process

{
  "violationType": "Custody/Visitation",
  "urgency": true,
  "violationDates": ["2025-09-15", "2025-09-16"],
  "violationDescription": "Other parent failed to return children...",
  "evidence": ["Text messages", "Witness statements"],
  "attemptedResolution": true,
  "resolutionDescription": "Contacted other parent multiple times...",
  "requestedRelief": ["Modify custody/visitation", "Find party in contempt"]
}
```

## 🚀 Next Steps

1. **Frontend Integration**: Create React components for violation intake
2. **PDF Generation**: Implement form filling with PyPDF2
3. **Document Storage**: Save completed forms to Cloud Storage
4. **Email Notifications**: Send filing instructions to users
5. **Tracking**: Add status tracking for filed violations

## 🔒 Security Note

All forms are stored locally in the project. No sensitive user data is stored in the forms directory. User responses are saved securely in the database.

## 📈 Benefits

- **Automated Track Selection**: No legal knowledge needed
- **Reduced Errors**: System ensures correct forms are used
- **Time Savings**: Declaration generated automatically
- **Location Aware**: Correct courthouse automatically selected
- **Comprehensive**: Covers all violation types and urgency levels

The system is now ready to handle San Diego Family Court violation filings!