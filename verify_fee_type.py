from models import SessionLocal, Customer, Invoice, init_db
from invoice_generator import generate_invoice_for_customer
from datetime import date
import os

def verify():
    session = SessionLocal()
    try:
        # Create a test customer with a specific fee type
        print("Creating test customer...")
        customer = Customer(
            name="Verification User",
            email="verify@test.com",
            property_address="999 Verify St",
            rate=150.0,
            cadence="monthly",
            fee_type="Special Assessment",
            next_bill_date=date.today()
        )
        session.add(customer)
        session.commit()
        session.refresh(customer)
        
        print(f"Customer created with fee_type: {customer.fee_type}")
        
        # Generate invoice
        print("Generating invoice...")
        invoice = generate_invoice_for_customer(customer, date.today())
        
        # Verify email body
        print("Verifying email body...")
        if "Linda Flood" in invoice.email_body:
            print("SUCCESS: Signature is correct (Linda Flood).")
        else:
            print(f"FAILURE: Signature incorrect. Body:\n{invoice.email_body}")
            
        if "Special Assessment" in invoice.email_body:
            print("SUCCESS: Fee type is present in email body.")
        else:
            print(f"FAILURE: Fee type missing from email body. Body:\n{invoice.email_body}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        if 'customer' in locals():
            session.delete(customer)
            session.commit()
        session.close()

if __name__ == "__main__":
    verify()
