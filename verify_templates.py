from flask import Flask, render_template
from models import Customer
import os

app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'), static_folder=os.path.join(os.getcwd(), 'static'))

@app.route('/')
def test_render():
    try:
        # Test new_customer.html
        print("Rendering new_customer.html...")
        render_template("new_customer.html")
        print("SUCCESS: new_customer.html rendered.")

        # Test edit_customer.html
        print("Rendering edit_customer.html...")
        # Create a dummy customer for the template context
        dummy_customer = Customer(
            name="Test", email="test@test.com", property_address="123 St",
            rate=100, cadence="monthly", next_bill_date="2025-01-01"
        )
        render_template("edit_customer.html", customer=dummy_customer)
        print("SUCCESS: edit_customer.html rendered.")
        
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    with app.app_context():
        test_render()
