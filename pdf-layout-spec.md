# PDF Layout Specification - California Family Law Motions

## Document Standards
- **Page Size**: 8.5" x 11" (Letter)
- **Margins**: 1" all sides (California Rules of Court)
- **Font**: Times New Roman or Arial
- **Font Size**: 12pt for body text, 10pt for footnotes
- **Line Spacing**: 1.5 or double-spaced for declarations
- **Page Numbers**: Bottom center, format "Page X of Y"
- **Binding**: 2-hole punch at top (California standard)

## FL-300 Request for Order - Layout Structure

### Page 1: Cover Sheet
```
┌─────────────────────────────────────────────────────────┐
│  SUPERIOR COURT OF CALIFORNIA                          │
│  COUNTY OF [COUNTY NAME]                               │
│                                                         │
│  [PETITIONER NAME]           )  Case No: [CASE#]       │
│      Petitioner,             )                         │
│                              )  REQUEST FOR ORDER      │
│  vs.                         )  (Family Law)           │
│                              )                         │
│  [RESPONDENT NAME]           )  Form FL-300            │
│      Respondent.             )                         │
│                                                         │
│  Hearing Date: [DATE]        Time: [TIME]              │
│  Department: [DEPT]          Room: [ROOM]              │
└─────────────────────────────────────────────────────────┘
```

### Page 2-3: Relief Requested
```
┌─────────────────────────────────────────────────────────┐
│  TO THE RESPONDENT: [Name]                             │
│  A COURT HEARING WILL BE HELD AS FOLLOWS:              │
│  [Hearing details box]                                 │
│                                                         │
│  1. CHILD CUSTODY AND VISITATION                       │
│     □ Legal custody to: □ Petitioner □ Respondent     │
│     □ Physical custody to: [Details]                   │
│     □ Visitation: [Schedule grid]                      │
│                                                         │
│  2. CHILD SUPPORT                                      │
│     □ Amount: $_______ per month                       │
│     □ Start date: _______                              │
│                                                         │
│  3. SPOUSAL SUPPORT                                    │
│     □ Amount: $_______ per month                       │
│     □ Duration: _______                                │
│                                                         │
│  4. ATTORNEY FEES                                      │
│     □ Amount: $_______                                 │
│                                                         │
│  5. OTHER RELIEF                                       │
│     [Multi-line text area]                             │
└─────────────────────────────────────────────────────────┘
```

### Page 4+: Declaration/Facts
```
┌─────────────────────────────────────────────────────────┐
│  DECLARATION IN SUPPORT OF REQUEST FOR ORDER           │
│                                                         │
│  I, [Declarant Name], declare:                         │
│                                                         │
│  FACTS:                                                │
│  1. [Numbered paragraph with facts]                    │
│     [Continuation of paragraph 1...]                   │
│                                                         │
│  2. [Numbered paragraph with facts]                    │
│     [Continuation of paragraph 2...]                   │
│                                                         │
│  BEST INTERESTS (if custody/visitation):               │
│  3. [Best interests analysis]                          │
│                                                         │
│  [Continue numbered paragraphs...]                     │
│                                                         │
│  I declare under penalty of perjury under the laws     │
│  of the State of California that the foregoing is     │
│  true and correct.                                     │
│                                                         │
│  Date: _______                                         │
│  Signature: _______________________                    │
│  Print Name: [Name]                                    │
└─────────────────────────────────────────────────────────┘
```

## FL-320 Response to RFO - Layout Structure

### Page 1: Response Cover
```
┌─────────────────────────────────────────────────────────┐
│  RESPONSIVE DECLARATION TO REQUEST FOR ORDER           │
│                                                         │
│  [Same header as RFO with case caption]                │
│                                                         │
│  RESPONSE TO REQUESTS:                                 │
│  1. □ AGREE □ DISAGREE □ AGREE IN PART                │
│     [Explanation area]                                 │
│                                                         │
│  2. □ AGREE □ DISAGREE □ AGREE IN PART                │
│     [Explanation area]                                 │
└─────────────────────────────────────────────────────────┘
```

## Common Elements

### Header (All Pages After First)
```
┌─────────────────────────────────────────────────────────┐
│  [PETITIONER] v. [RESPONDENT]     Case No: [CASE#]     │
└─────────────────────────────────────────────────────────┘
```

### Footer (All Pages)
```
┌─────────────────────────────────────────────────────────┐
│                    Page [X] of [Y]                     │
│         [DOCUMENT TYPE] - [DATE GENERATED]             │
└─────────────────────────────────────────────────────────┘
```

### Signature Block
```
┌─────────────────────────────────────────────────────────┐
│  Date: _______________                                 │
│                                                         │
│  _____________________________                         │
│  [Printed Name]                                        │
│  [□ Petitioner □ Respondent]                          │
│  [Address if self-represented]                         │
│  [Phone number]                                        │
└─────────────────────────────────────────────────────────┘
```

## PDF Generation Technical Specs

### Libraries/Tools
- **Primary**: PDFKit (Node.js) or ReportLab (Python)
- **Alternative**: Puppeteer for HTML-to-PDF conversion
- **Forms**: PDF form fields for fillable sections

### Rendering Pipeline
1. **Data Collection**: Gather from database
2. **Template Selection**: Choose FL-300 or FL-320
3. **Content Flow**: 
   - Apply word wrap at margins
   - Handle page breaks (no orphan lines)
   - Maintain paragraph integrity
4. **Form Fields**: 
   - Checkboxes for options
   - Text fields for amounts/dates
   - Multi-line for declarations
5. **Finalization**:
   - Add page numbers
   - Generate table of contents (if > 10 pages)
   - Create bookmarks for sections

### Accessibility Requirements
- **PDF/A Compliance**: For long-term archival
- **Text Layer**: Searchable/selectable text
- **Tagging**: Proper heading structure
- **Reading Order**: Logical flow for screen readers

### File Naming Convention
```
[CASE#]_[DOCTYPE]_[PARTY]_[DATE].pdf
Example: FL2024001234_RFO_Petitioner_20240315.pdf
```

## Attachment Handling

### Standard Attachments
- **FL-311**: Child Custody and Visitation Attachment
- **FL-150**: Income and Expense Declaration
- **FL-160**: Property Declaration
- **MC-030**: Declaration (additional pages)

### Attachment Rules
- Number exhibits sequentially (Exhibit A, B, C...)
- Include exhibit index on page 2
- Separator pages between attachments
- Maximum 25 pages for declarations (local rule)

## Quality Checks
1. **Margins**: Verify 1" minimum
2. **Font Size**: Confirm 12pt minimum
3. **Line Numbers**: Add if required by local rules
4. **Page Count**: Flag if exceeds limits
5. **Required Fields**: Validate all mandatory fields completed
6. **Signature Areas**: Ensure adequate space
7. **Date Format**: MM/DD/YYYY consistency
8. **Case Number**: Appears on every page

## Local Variations by County

### Los Angeles
- Line numbers required on declarations
- Electronic filing mandatory
- Blue backing paper not required for e-filing

### San Francisco
- Department-specific cover sheets
- Courtesy copies required for some departments

### Orange County
- Specific font requirements (Century Schoolbook)
- Extended page limits for complex cases

### Default/Universal
- Follow California Rules of Court
- Check local rules website before filing