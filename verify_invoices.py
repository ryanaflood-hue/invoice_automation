from flask import Flask, render_template
from models import Invoice, Customer
import os
from datetime import date

app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'), static_folder=os.path.join(os.getcwd(), 'static'))

@app.route('/')
def test_render():
    try:
        # Create dummy data
        customer = Customer(id=1, name="Test Customer", email="test@test.com", property_address="123 St", rate=100, cadence="monthly", next_bill_date=date.today())
        invoice = Invoice(
            id=1, customer_id=1, invoice_date=date.today(), period_label="November 2025", 
            amount=100.0, file_path="path/to/invoice.docx", 
            email_subject="Invoice Subject", email_body="Invoice Body Content"
        )
        
        customers_map = {1: customer}
        invoices = [invoice]

        print("Rendering invoices.html...")
        render_template("invoices.html", invoices=invoices, customers=customers_map)
        print("SUCCESS: invoices.html rendered.")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    with app.app_context():
        test_render()
