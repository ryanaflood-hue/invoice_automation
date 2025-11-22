# Template Update Instructions

## Update base_invoice_template.docx

Replace the current multi-placeholder fee lines with single placeholders:

### Current Template Structure (REMOVE):
```
{{PERIOD2}} {{FEE_TYPE2}} fee ({{PERIOD_DATES2}}) = {{AMOUNT2}}
{{PERIOD3}} {{FEE_TYPE3}} fee ({{PERIOD_DATES3}}) = {{AMOUNT3}}
```

### New Template Structure (USE INSTEAD):
```
{{FEE_LINE_2}}
{{FEE_LINE_3}}
{{ADDITIONAL_FEE_LINE}}
```

## How to Update:

1. Open `C:\Development\invoice_automation\invoice_templates\base_invoice_template.docx`
2. Find the rows that have the PERIOD2/PERIOD3 placeholders
3. Replace the ENTIRE content of those rows with just:
   - `{{FEE_LINE_2}}` for the second fee row
   - `{{FEE_LINE_3}}` for the third fee row
   - `{{ADDITIONAL_FEE_LINE}}` if you have an additional fee row
4. Save the template

## What this does:

The Python code now builds complete lines like:
- `"4th quarter 2025 Lawn Care fee (10/01/2025 - 12/31/2025) = $50.00"`

Or empty strings (`""`) if the fee doesn't exist, which results in blank lines instead of "fee () =".

This is much cleaner and more reliable than trying to detect and remove rows!
