from invoice_generator import _generate_invoice_logic
from datetime import date
from unittest.mock import MagicMock

# Mock customer
customer = MagicMock()
customer.name = "Test Customer"
customer.email = "test@example.com"
customer.property_address = "123 Test St"
customer.property_city = "Test City"
customer.property_state = "TS"
customer.property_zip = "12345"
customer.fee_type = "Management Fee"
customer.properties = []

# Inputs
invoice_date = date(2025, 10, 1)
period_label = "4th quarter 2025"
period_dates = "10/01/2025 - 12/31/2025"
amount = 100.0

kwargs = {
    "fee_2_type": "Late Fee",
    "fee_2_amount": 50.0,
    "fee_3_type": "Late Fee",
    "fee_3_amount": 75.0,
    "additional_fee_desc": "Air purifier fee",
    "additional_fee_amount": 300.0
}

print("Testing _generate_invoice_logic with inputs:")
print(f"Base Amount: {amount}")
print(f"Kwargs: {kwargs}")

try:
    # We don't care about the file output, just the logic execution (and print statements I added)
    # Note: This will try to open the template file. If it fails, we'll know.
    _generate_invoice_logic(customer, invoice_date, period_label, period_dates, amount, **kwargs)
except Exception as e:
    print(f"Caught exception (expected if template missing): {e}")
