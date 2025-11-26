from models import Invoice, SessionLocal
from sqlalchemy import desc

def inspect_latest_invoice():
    session = SessionLocal()
    try:
        invoice = session.query(Invoice).order_by(Invoice.id.desc()).first()
        if not invoice:
            print("No invoices found.")
            return

        print(f"Latest Invoice ID: {invoice.id}")
        print(f"Date: {invoice.invoice_date}")
        print(f"Period: {invoice.period_label}")
        
        from models import Customer
        customer = session.query(Customer).get(invoice.customer_id)
        print(f"Customer: {customer.name} (ID: {invoice.customer_id})")
        
        print(f"Fee 2 Type: {invoice.fee_2_type}")
        print(f"Fee 2 Amount: {invoice.fee_2_amount}")
        print(f"Fee 3 Type: {invoice.fee_3_type}")
        print(f"Fee 3 Amount: {invoice.fee_3_amount}")
        print(f"Additional Fee Desc: {invoice.additional_fee_desc}")
        print(f"Additional Fee Amount: {invoice.additional_fee_amount}")
        
    finally:
        session.close()

if __name__ == "__main__":
    inspect_latest_invoice()
