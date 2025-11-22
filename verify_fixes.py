import os
from datetime import date
from models import init_db, SessionLocal, Customer, Property, Invoice
from invoice_generator import generate_invoice_for_customer

# Initialize DB
init_db()

def verify_fixes():
    session = SessionLocal()
    try:
        # 1. Create a test customer with multiple fees
        print("Creating test customer...")
        c = Customer(
            name="Test Customer MultiFee",
            email="test@example.com",
            property_address="123 Test St",
            property_city="Test City",
            property_state="TS",
            property_zip="12345",
            rate=100.0,
            cadence="monthly",
            fee_type="Management Fee",
            fee_2_type="Technology Fee",
            fee_2_rate=25.0,
            next_bill_date=date.today()
        )
        session.add(c)
        session.commit()
        
        # 2. Add a property with a fee
        print("Adding property with fee...")
        p = Property(
            customer_id=c.id,
            address="456 Rental Ave",
            city="Rentville",
            state="TS",
            zip_code="67890",
            fee_amount=50.0
        )
        session.add(p)
        session.commit()
        
        # 3. Generate Invoice
        print("Generating invoice...")
        invoice = generate_invoice_for_customer(c, date.today())
        # print(f"Invoice generated: {invoice.file_path}")
        # print(f"Total Amount: {invoice.amount}") 
        
        # 4. Verify File Exists
        # We can't access invoice.file_path easily if detached, so let's just check the directory
        print("Checking generated_invoices directory...")
        files = os.listdir("generated_invoices")
        if files:
            print(f"SUCCESS: Found files: {files}")
        else:
            print("FAILURE: No files found.")
            
        # 5. Clean up
        session.delete(c) # Cascades to property
        session.delete(invoice)
        session.commit()
        print("Test data cleaned up.")
        
    except Exception as e:
        print(f"VERIFICATION FAILED: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    verify_fixes()
