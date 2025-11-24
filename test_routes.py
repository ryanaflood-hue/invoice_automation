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
        response = self.client.get('/customers/new')
        self.assertEqual(response.status_code, 200)

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

if __name__ == '__main__':
    unittest.main()
