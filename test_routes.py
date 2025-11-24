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
        self.assertEqual(response.status_code, 200)

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

if __name__ == '__main__':
    unittest.main()
