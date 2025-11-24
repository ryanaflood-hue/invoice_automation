import unittest
from app import app, init_db, SessionLocal
from models import Customer, Invoice
from datetime import date

class TestRoutes(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        init_db()
        
        # Create a dummy customer and invoice for testing
        session = SessionLocal()
        if not session.query(Customer).filter_by(email="test@example.com").first():
            c = Customer(
                name="Test Customer",
                email="test@example.com",
                property_address="123 Test St",
                rate=100.0,
                cadence="quarterly",
                next_bill_date=date.today()
            )
            session.add(c)
            session.commit()
            
            inv = Invoice(
                customer_id=c.id,
                invoice_date=date.today(),
                period_label="Q4 2025",
                amount=100.0,
                file_path="test.docx",
                email_subject="Test",
                email_body="Test"
            )
            session.add(inv)
            session.commit()
        session.close()

    def test_home_route(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 302)

    def test_customers_route(self):
        response = self.client.get('/customers')
        self.assertEqual(response.status_code, 200)

    def test_new_customer_route(self):
        print("\nTesting New Customer Route...")
        # Test GET
        response = self.client.get('/customers/new')
        self.assertEqual(response.status_code, 200)
        
        # Test POST
        response = self.client.post('/customers/new', data={
            "name": "New Guy",
            "email": "new@guy.com",
            "property_address": "123 New St",
            "property_city": "New City",
            "property_state": "WI",
            "property_zip": "53000",
            "rate": "100.00",
            "cadence": "monthly",
            "fee_type": "Management Fee",
            "next_bill_date": date.today().isoformat()
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"New Guy", response.data)

    def test_invoices_route(self):
        print("\nTesting /invoices route...")
        response = self.client.get('/invoices')
        if response.status_code != 200:
            print(f"FAILED: {response.status_code}")
            print(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)

    def test_delete_invoice(self):
        print("\nTesting DELETE /invoices/<id>/delete...")
        # Create an invoice to delete
        session = SessionLocal()
        c = session.query(Customer).first()
        inv = Invoice(
            customer_id=c.id,
            invoice_date=date.today(),
            period_label="Delete Me",
            amount=100.0,
            file_path="delete.docx",
            email_subject="Delete",
            email_body="Delete"
        )
        session.add(inv)
        session.commit()
        inv_id = inv.id
        session.close()

        # Send POST request to delete
        response = self.client.post(f'/invoices/{inv_id}/delete', follow_redirects=True)
        if response.status_code != 200:
            print(f"DELETE FAILED: {response.status_code}")
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        session = SessionLocal()
        deleted_inv = session.query(Invoice).get(inv_id)
        session.close()
        self.assertIsNone(deleted_inv)

    def test_invoice_consistency(self):
        print("\nTesting Invoice Consistency (Email vs PDF)...")
        # 1. Create customer with defaults
        session = SessionLocal()
        c = Customer(
            name="Consistency Test",
            email="test@consistency.com",
            property_address="999 Consistency Ln",
            rate=500.0,
            cadence="quarterly",
            fee_2_type="Late Fee",
            fee_2_rate=50.0,
            next_bill_date=date.today()
        )
        session.add(c)
        session.commit()
        c_id = c.id
        session.close()

        # 2. Generate Invoice via POST (mimic form submission with empty fields)
        # Empty fields should trigger fallback to customer defaults
        response = self.client.post('/generate-invoice', data={
            "customer_id": c_id,
            "invoice_date": date.today().isoformat(),
            "template_name": "base_invoice_template.docx",
            "fee_2_type": "",
            "fee_2_amount": "", # Empty string
            "fee_3_type": "",
            "fee_3_amount": "",
            "additional_fee_desc": "",
            "additional_fee_amount": ""
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 3. Verify Invoice Record
        session = SessionLocal()
        inv = session.query(Invoice).filter_by(customer_id=c_id).first()
        self.assertIsNotNone(inv)
        
        # Check Amount (Should be BASE rate)
        self.assertEqual(inv.amount, 500.0)
        
        # Check Email Body (Should be TOTAL: 500 + 50 = 550)
        print(f"Email Body: {inv.email_body}")
        self.assertIn("$550.00", inv.email_body)
        
        # 4. Verify Regeneration (PDF logic)
        from invoice_generator import generate_invoice_buffer
        filename, buffer = generate_invoice_buffer(inv)
        
        # We can't easily parse the DOCX buffer here, but we can check the logic
        # by calling _generate_invoice_logic directly with the same params
        from invoice_generator import _generate_invoice_logic, get_period_dates
        
        session = SessionLocal()
        c_refreshed = session.query(Customer).get(c_id)
        
        start_date, end_date = get_period_dates(inv.invoice_date, "quarterly")
        period_dates = f"{start_date.strftime('%m/%d/%Y')} - {end_date.strftime('%m/%d/%Y')}"
        
        _, _, total_amount = _generate_invoice_logic(
            c_refreshed, 
            inv.invoice_date, 
            inv.period_label, 
            period_dates, 
            inv.amount, 
            return_buffer=True,
            fee_2_type=inv.fee_2_type,
            fee_2_amount=inv.fee_2_amount
        )
        
        self.assertEqual(total_amount, 550.0)
        session.close()

    def test_delete_customer_preserves_invoices(self):
        """Test that deleting a customer does NOT delete their invoices."""
        print("\nTesting Customer Deletion Preserves Invoices...")
        
        # 1. Create a customer
        session = SessionLocal()
        c = Customer(
            name="To Be Deleted",
            email="delete@me.com",
            property_address="123 Delete St",
            rate=100.0,
            cadence="monthly",
            next_bill_date=date(2025, 1, 1)
        )
        session.add(c)
        session.commit()
        c_id = c.id
        session.close()

        # 2. Create an invoice for this customer
        session = SessionLocal()
        inv = Invoice(
            customer_id=c_id,
            invoice_date=date(2025, 1, 1),
            period_label="Jan 2025",
            amount=100.0,
            file_path="test_invoice.docx",
            email_subject="Test Invoice",
            email_body="Test Body"
        )
        session.add(inv)
        session.commit()
        inv_id = inv.id
        session.close()

        # 3. Delete the customer via the route
        response = self.client.post(f'/customers/{c_id}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        # 4. Verify customer is gone
        session = SessionLocal()
        deleted_customer = session.query(Customer).get(c_id)
        self.assertIsNone(deleted_customer)
        
        # 5. Verify invoice still exists
        orphaned_invoice = session.query(Invoice).get(inv_id)
        self.assertIsNotNone(orphaned_invoice)
        session.close()

        # 6. Verify /invoices route still works (doesn't crash)
        response = self.client.get('/invoices')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Deleted Customer", response.data)
        print("Customer deletion preserved invoices successfully.")

if __name__ == '__main__':
    unittest.main()
