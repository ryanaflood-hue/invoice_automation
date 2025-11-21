import sys
import os
from datetime import date

# Add current directory to path
sys.path.append(os.getcwd())

from models import init_db, SessionLocal, Customer
from invoice_generator import generate_invoice_for_customer, generate_invoice_with_template

def reproduce():
    # Initialize DB
    init_db()
    session = SessionLocal()
    
    try:
        # Create a dummy customer if not exists
        customer = session.query(Customer).filter_by(email="test@example.com").first()
        if not customer:
            customer = Customer(
                name="Test Customer",
                email="test@example.com",
                property_address="123 Test St",
                property_city="Test City",
                property_state="TS",
                property_zip="12345",
                rate=100.0,
                cadence="monthly",
                next_bill_date=date.today()
            )
            session.add(customer)
            session.commit()
            print("Created test customer")
        
        # Try generating invoice
        print("Attempting to generate invoice for customer...")
        invoice = generate_invoice_for_customer(customer, date.today())
        print(f"Successfully generated invoice: {invoice.file_path}")
        
        # Try generating with template
        print("Attempting to generate invoice with template...")
        invoice2 = generate_invoice_with_template(customer, date.today(), "base_invoice_template.docx")
        print(f"Successfully generated invoice with template: {invoice2.file_path}")

    except Exception as e:
        print(f"Caught exception: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    reproduce()
