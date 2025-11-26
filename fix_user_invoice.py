from models import Invoice, Customer, SessionLocal

def fix_invoice():
    session = SessionLocal()
    try:
        # Find the customer
        customer = session.query(Customer).filter(Customer.name == "Test Customer").first()
        if not customer:
            print("Customer 'Test Customer' not found.")
            return

        print(f"Found Customer: {customer.name} (ID: {customer.id})")
        print(f"Customer Fees: Fee 2={customer.fee_2_rate}, Fee 3={customer.fee_3_rate}, Add={customer.additional_fee_amount}")

        # Find the invoice
        invoice = session.query(Invoice).filter(
            Invoice.customer_id == customer.id,
            Invoice.period_label == "4th quarter 2025"
        ).first()

        if not invoice:
            print("Invoice for '4th quarter 2025' not found.")
            return

        print(f"Found Invoice ID: {invoice.id}")
        print(f"Current Invoice Fees: Fee 2={invoice.fee_2_amount}, Fee 3={invoice.fee_3_amount}, Add={invoice.additional_fee_amount}")

        # Update invoice fees
        invoice.fee_2_type = customer.fee_2_type
        invoice.fee_2_amount = customer.fee_2_rate
        invoice.fee_3_type = customer.fee_3_type
        invoice.fee_3_amount = customer.fee_3_rate
        invoice.additional_fee_desc = customer.additional_fee_desc
        invoice.additional_fee_amount = customer.additional_fee_amount

        session.commit()
        print("Invoice updated successfully with customer fees.")

    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fix_invoice()
