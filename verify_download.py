from app import app
from models import SessionLocal, Invoice, Customer
from datetime import date
import io

def verify():
    session = SessionLocal()
    try:
        # Ensure we have a customer and invoice
        customer = session.query(Customer).first()
        if not customer:
            print("Creating dummy customer...")
            customer = Customer(name="Test", email="t@t.com", property_address="123 T", rate=100, cadence="monthly", next_bill_date=date.today())
            session.add(customer)
            session.commit()
            
        invoice = session.query(Invoice).first()
        if not invoice:
            print("Creating dummy invoice...")
            invoice = Invoice(customer_id=customer.id, invoice_date=date.today(), period_label="Test Period", amount=100, file_path="dummy", email_subject="s", email_body="b")
            session.add(invoice)
            session.commit()
            
        invoice_id = invoice.id
        print(f"Testing download for invoice ID: {invoice_id}")
        
        with app.test_client() as client:
            response = client.get(f'/invoices/{invoice_id}/download')
            
            if response.status_code == 200:
                print("SUCCESS: Download route returned 200 OK.")
                if response.headers['Content-Type'] == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                    print("SUCCESS: Content-Type is correct.")
                else:
                    print(f"FAILURE: Incorrect Content-Type: {response.headers['Content-Type']}")
                    
                if int(response.headers['Content-Length']) > 0:
                     print("SUCCESS: Content-Length > 0.")
                else:
                     print("FAILURE: Empty file returned.")
            else:
                print(f"FAILURE: Status Code {response.status_code}")
                print(response.data)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verify()
