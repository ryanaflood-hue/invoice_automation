from models import SessionLocal, Customer, FeeType
from app import app
from flask import template_rendered
from contextlib import contextmanager

@contextmanager
def captured_templates(app):
    recorded = []
    def record(sender, template, context, **extra):
        recorded.append((template, context))
    template_rendered.connect(record, app)
    try:
        yield recorded
    finally:
        template_rendered.disconnect(record, app)

def verify():
    session = SessionLocal()
    try:
        # 1. Verify FeeType model works
        print("Testing FeeType model...")
        new_fee = FeeType(name="Verification Fee")
        session.add(new_fee)
        session.commit()
        
        ft = session.query(FeeType).filter_by(name="Verification Fee").first()
        if ft:
            print("SUCCESS: Created 'Verification Fee'.")
        else:
            print("FAILURE: Could not create fee type.")
            return

        # 2. Verify Templates receive fee_types
        print("Testing Template Context...")
        with app.test_client() as client:
            with captured_templates(app) as templates:
                client.get('/new-customer')
                if not templates:
                    print("FAILURE: No templates rendered for /new-customer")
                else:
                    template, context = templates[0]
                    if 'fee_types' in context:
                        types = [t.name for t in context['fee_types']]
                        if "Verification Fee" in types:
                            print("SUCCESS: 'Verification Fee' passed to new_customer template.")
                        else:
                            print(f"FAILURE: 'Verification Fee' not in context. Found: {types}")
                    else:
                        print("FAILURE: 'fee_types' not in context.")

        # 3. Clean up
        session.delete(ft)
        session.commit()
        print("Cleanup complete.")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == "__main__":
    verify()
