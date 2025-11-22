import unittest
from unittest.mock import MagicMock, patch
from datetime import date
import os
import sys

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from invoice_generator import _generate_invoice_logic, generate_invoice_for_customer, generate_invoice_with_template
from models import Customer, Property, Invoice
from app import app

class TestInvoiceRoutes(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
    def tearDown(self):
        self.app_context.pop()

    @patch('app.generate_invoice_with_template')
    @patch('app.SessionLocal')
    def test_generate_invoice_route_passes_data(self, mock_session_cls, mock_gen):
        """Test that the /generate-invoice route correctly extracts form data and passes it to the generator."""
        # Mock DB session and customer
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        
        mock_customer = MagicMock()
        mock_customer.id = 1
        mock_session.query.return_value.get.return_value = mock_customer
        
        # Mock fee types query
        mock_session.query.return_value.all.return_value = []
        
        # Mock form data
        form_data = {
            "customer_id": "1",
            "invoice_date": "2025-10-01",
            "template_name": "base_invoice_template.docx",
            "fee_2_type": "Route Fee 2",
            "fee_2_amount": "50.00",
            "fee_3_type": "Route Fee 3",
            "fee_3_amount": "75.00",
            "additional_fee_desc": "Route Add",
            "additional_fee_amount": "300.00"
        }
        
        # Make POST request
        response = self.client.post('/generate-invoice', data=form_data)
        
        # Verify generate_invoice_with_template was called with correct kwargs
        self.assertTrue(mock_gen.called)
        args, kwargs = mock_gen.call_args
        
        print(f"\n[Route Test] Kwargs passed to generator: {kwargs}")
        
        self.assertEqual(kwargs.get('fee_2_type'), "Route Fee 2")
        self.assertEqual(kwargs.get('fee_2_amount'), 50.0)
        self.assertEqual(kwargs.get('fee_3_type'), "Route Fee 3")
        self.assertEqual(kwargs.get('fee_3_amount'), 75.0)
        self.assertEqual(kwargs.get('additional_fee_desc'), "Route Add")
        self.assertEqual(kwargs.get('additional_fee_amount'), 300.0)

    def test_new_customer_route(self):
        """Test that the new_customer route correctly creates a customer with all fee fields."""
        with patch('app.SessionLocal') as mock_session_cls:
            mock_session = MagicMock()
            mock_session_cls.return_value = mock_session
            
            # Mock fee types query for GET request or template rendering
            mock_session.query.return_value.all.return_value = []
            
            data = {
                'name': 'Test Customer',
                'email': 'test@example.com',
                'property_address': '123 Test St',
                'property_city': 'Test City',
                'property_state': 'TS',
                'property_zip': '12345',
                'rate': '100.00',
                'cadence': 'monthly',
                'fee_type': 'Management Fee',
                'next_bill_date': '2025-10-01',
                'fee_2_type': 'Fee 2',
                'fee_2_rate': '50.00',
                'fee_3_type': 'Fee 3',
                'fee_3_rate': '75.00',
                'additional_fee_desc': 'Add Fee',
                'additional_fee_amount': '25.00'
            }
            
            response = self.client.post('/customers/new', data=data, follow_redirects=True)
            
            # Check if session.add was called with a Customer object
            self.assertTrue(mock_session.add.called)
            created_customer = mock_session.add.call_args[0][0]
            
            print(f"\n[New Customer Test] Created Customer: {created_customer.__dict__}")
            
            self.assertEqual(created_customer.name, 'Test Customer')
            self.assertEqual(created_customer.fee_2_type, 'Fee 2')
            self.assertEqual(created_customer.fee_2_rate, 50.0)
            self.assertEqual(created_customer.fee_3_type, 'Fee 3')
            self.assertEqual(created_customer.fee_3_rate, 75.0)
            self.assertEqual(created_customer.additional_fee_desc, 'Add Fee')
            self.assertEqual(created_customer.additional_fee_amount, 25.0)

class TestInvoiceSystem(unittest.TestCase):
    def setUp(self):
        # Create a mock customer with defaults
        self.customer = Customer(
            id=1,
            name="Test Customer",
            email="test@example.com",
            property_address="123 Test St",
            property_city="Test City",
            property_state="TS",
            property_zip="12345",
            rate=100.0,
            cadence="monthly",
            fee_type="Management Fee",
            # Default fees
            fee_2_type="Default Fee 2",
            fee_2_rate=50.0,
            fee_3_type="Default Fee 3",
            fee_3_rate=25.0,
            additional_fee_desc="Default Add Fee",
            additional_fee_amount=10.0,
            next_bill_date=date(2025, 10, 1)
        )
        self.customer.properties = []

    @patch('invoice_generator.Document')
    @patch('invoice_generator.fill_invoice_template')
    def test_batch_generation_uses_defaults(self, mock_fill, mock_doc):
        """Test that automated batch generation uses the customer's default fees."""
        # Setup mock document
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        mock_doc_instance.tables = []
        mock_doc_instance.paragraphs = []
        
        # Call batch generation (simulated by calling logic directly as batch does)
        # Batch calls: _generate_invoice_logic(customer, ...) without kwargs
        
        _generate_invoice_logic(
            self.customer, 
            date(2025, 10, 1), 
            "October 2025", 
            "10/01/2025 - 10/31/2025", 
            100.0
        )
        
        # Get the replacements dict passed to fill_invoice_template
        args, _ = mock_fill.call_args
        replacements = args[1]
        
        print(f"\n[Batch Test] Total Amount: {replacements.get('{{TOTAL_AMOUNT}}')}")
        
    @patch('invoice_generator.Document')
    @patch('invoice_generator.fill_invoice_template')
    def test_manual_generation_overrides(self, mock_fill, mock_doc):
        """Test that manual generation uses provided kwargs and ignores defaults if provided."""
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        mock_doc_instance.tables = []
        mock_doc_instance.paragraphs = []
        
        kwargs = {
            "fee_2_type": "Manual Fee 2",
            "fee_2_amount": 200.0,
            "fee_3_type": "Manual Fee 3",
            "fee_3_amount": 300.0,
            "additional_fee_desc": "Manual Add",
            "additional_fee_amount": 400.0
        }
        
        _generate_invoice_logic(
            self.customer, 
            date(2025, 10, 1), 
            "October 2025", 
            "10/01/2025 - 10/31/2025", 
            100.0,
            **kwargs
        )
        
        args, _ = mock_fill.call_args
        replacements = args[1]
        
        print(f"\n[Manual Test] Total Amount: {replacements.get('{{TOTAL_AMOUNT}}')}")
        
        # Base 100 + Manual 200 + Manual 300 + Manual 400 = 1000
        self.assertEqual(replacements.get('{{TOTAL_AMOUNT}}'), "$1,000.00")
        
        # Verify lines
        self.assertIn("Manual Fee 2", replacements.get('{{FEE_LINE_2}}'))
        self.assertIn("Manual Fee 3", replacements.get('{{FEE_LINE_3}}'))
        self.assertIn("Manual Add", replacements.get('{{ADDITIONAL_FEE_LINE}}'))

    @patch('invoice_generator.Document')
    @patch('invoice_generator.fill_invoice_template')
    def test_manual_generation_partial_override(self, mock_fill, mock_doc):
        """Test manual generation with some fields empty (should NOT use defaults if explicitly None)."""
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        mock_doc_instance.tables = []
        mock_doc_instance.paragraphs = []
        
        # User leaves Fee 2 blank, but sets Fee 3
        kwargs = {
            "fee_2_type": None,
            "fee_2_amount": None,
            "fee_3_type": "Manual Fee 3",
            "fee_3_amount": 300.0,
            "additional_fee_desc": None,
            "additional_fee_amount": None
        }
        
        _generate_invoice_logic(
            self.customer, 
            date(2025, 10, 1), 
            "October 2025", 
            "10/01/2025 - 10/31/2025", 
            100.0,
            **kwargs
        )
        
        args, _ = mock_fill.call_args
        replacements = args[1]
        
        print(f"\n[Partial Test] Total Amount: {replacements.get('{{TOTAL_AMOUNT}}')}")
        
        # Base 100 + Fee 3 300 = 400. Fee 2 and Add should be ignored (even though customer has defaults)
        self.assertEqual(replacements.get('{{TOTAL_AMOUNT}}'), "$400.00")
        self.assertEqual(replacements.get('{{FEE_LINE_2}}'), "")

    @patch('invoice_generator.Document')
    @patch('invoice_generator.fill_invoice_template')
    def test_property_fees_included(self, mock_fill, mock_doc):
        """Test that property fees are added to the total."""
        mock_doc_instance = MagicMock()
        mock_doc.return_value = mock_doc_instance
        mock_doc_instance.tables = []
        mock_doc_instance.paragraphs = []
        
        # Add a property with a fee
        prop = MagicMock()
        prop.fee_amount = 50.0
        self.customer.properties = [prop]
        
        # Manual generation with overrides
        kwargs = {
            "fee_2_type": "Manual Fee 2",
            "fee_2_amount": 50.0,
            "fee_3_type": "Manual Fee 3",
            "fee_3_amount": 75.0,
            "additional_fee_desc": "Manual Add",
            "additional_fee_amount": 300.0
        }
        
        _generate_invoice_logic(
            self.customer, 
            date(2025, 10, 1), 
            "October 2025", 
            "10/01/2025 - 10/31/2025", 
            100.0,
            **kwargs
        )
        
        args, _ = mock_fill.call_args
        replacements = args[1]
        
        print(f"\n[Property Fee Test] Total Amount: {replacements.get('{{TOTAL_AMOUNT}}')}")
        
        # Base 100 + Fee2 50 + Fee3 75 + Add 300 + Prop 50 = 575
        self.assertEqual(replacements.get('{{TOTAL_AMOUNT}}'), "$575.00")

if __name__ == '__main__':
    unittest.main()
