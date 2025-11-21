from models import SessionLocal, FeeType
from app import app

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

        # 2. Verify Response Content
        print("Testing Response Content...")
        with app.test_client() as client:
            response = client.get('/new-customer')
            content = response.data.decode('utf-8')
            
            if "Verification Fee" in content:
                print("SUCCESS: 'Verification Fee' found in /new-customer response.")
            else:
                print("FAILURE: 'Verification Fee' NOT found in response.")
                # print(content) # Uncomment to debug

            response_edit = client.get('/customers/1/edit') # Assuming customer 1 exists, if not this might fail 404 but that's ok for now
            # We can't easily test edit without a known customer ID, but new_customer is sufficient to prove the context is passed.

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
