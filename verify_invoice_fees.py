import os
import sys
from datetime import date
from models import Customer, Invoice, SessionLocal, init_db, Base
from invoice_generator import generate_invoice_for_customer, generate_invoice_buffer

# Use a test database
os.environ["DATABASE_URL"] = "sqlite:///test_invoice_fees.db"

def verify_fix():
    # Initialize DB
    if os.path.exists("test_invoice_fees.db"):
        os.remove("test_invoice_fees.db")
    
    init_db()
    session = SessionLocal()
    
    try:
        # Create a customer with fees
        customer = Customer(
            name="Test Fee Customer",
            email="test@example.com",
            property_address="123 Fee St",
            property_city="Fee City",
            property_state="FS",
            property_zip="12345",
            rate=100.0,
            cadence="monthly",
            next_bill_date=date.today(),
            fee_2_type="Late Fee",
            fee_2_rate=50.0,
            fee_3_type="Release Fee",
            fee_3_rate=30.0,
            additional_fee_desc="Air Purifier",
            additional_fee_amount=300.0
        )
        session.add(customer)
        session.commit()
        
        print(f"Created customer with fees: {customer.fee_2_type}=${customer.fee_2_rate}")
        
        # Generate invoice
        print("Generating invoice...")
        generate_invoice_for_customer(customer, date.today())
        
        # Re-query to avoid DetachedInstanceError
        # Get the latest invoice
        invoice = session.query(Invoice).order_by(Invoice.id.desc()).first()
        print(f"Invoice ID: {invoice.id}")
        
        print(f"Invoice Fee 2: {invoice.fee_2_type} = {invoice.fee_2_amount}")
        print(f"Invoice Fee 3: {invoice.fee_3_type} = {invoice.fee_3_amount}")
        print(f"Invoice Add Fee: {invoice.additional_fee_desc} = {invoice.additional_fee_amount}")
        
        assert invoice.fee_2_type == "Late Fee"
        assert invoice.fee_2_amount == 50.0
        assert invoice.fee_3_type == "Release Fee"
        assert invoice.fee_3_amount == 30.0
        assert invoice.additional_fee_desc == "Air Purifier"
        assert invoice.additional_fee_amount == 300.0
        
        print("SUCCESS: Invoice record has correct fees.")
        
        # Verify regeneration works
        print("Testing regeneration...")
        filename, buffer = generate_invoice_buffer(invoice)
        print(f"Regeneration successful. Filename: {filename}, Buffer size: {buffer.getbuffer().nbytes}")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()
        if os.path.exists("test_invoice_fees.db"):
            try:
                os.remove("test_invoice_fees.db")
            except:
                pass

if __name__ == "__main__":
    verify_fix()
