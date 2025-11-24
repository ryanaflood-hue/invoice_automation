from invoice_generator import _generate_invoice_logic
from models import Customer, Property
from datetime import date
from docx import Document
import os

def reproduce():
    # Setup Customer
    c = Customer(
        id=1,
        name="Test Customer",
        email="test@example.com",
        property_address="123 Test St",
        property_city="Test City",
        property_state="TS",
        property_zip="12345",
        rate=100.0,
        cadence="monthly",
        fee_type="Management Fee",
        # Default fees (to test override)
        fee_2_type="Default Fee 2",
        fee_2_rate=50.0,
        fee_3_type="Default Fee 3",
        fee_3_rate=25.0,
        additional_fee_desc="Default Add Fee",
        additional_fee_amount=10.0,
        next_bill_date=date(2025, 10, 1)
    )
    # Add Property with fee
    p = Property(address="123 Test St", fee_amount=125.0)
    c.properties = [p]

    # Manual Overrides (matching user scenario)
    kwargs = {
        "fee_2_type": "Late Fee",
        "fee_2_amount": 50.0,
        "fee_3_type": "Release Fee",
        "fee_3_amount": 30.0,
        "additional_fee_desc": "Air Purifier Fee",
        "additional_fee_amount": 300.0
    }

    print("Generating invoice...")
    # Pass return_buffer=False to save file
    filename, path = _generate_invoice_logic(
        c,
        date(2025, 11, 24),
        "4th quarter 2025",
        "10/01/2025 - 12/31/2025",
        100.0,
        return_buffer=False,
        **kwargs
    )
    
    print(f"Generated: {path}")
    
    # Inspect the generated file
    doc = Document(path)
    print("\n[Generated Content]")
    found_fee_3 = False
    found_prop_fee = False
    
    for p in doc.paragraphs:
        if p.text.strip():
            print(f"P: '{p.text}'")
        if "30.00" in p.text:
            found_fee_3 = True
        if "125.00" in p.text:
            found_prop_fee = True
            
    if found_fee_3:
        print("\n✅ Fee 3 ($30.00) FOUND in output.")
    else:
        print("\n❌ Fee 3 ($30.00) MISSING from output.")

    if found_prop_fee:
        print("\n✅ Property Fee ($125.00) FOUND in output.")
    else:
        print("\n❌ Property Fee ($125.00) MISSING from output.")

if __name__ == "__main__":
    reproduce()
