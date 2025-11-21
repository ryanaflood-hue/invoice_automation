from models import SessionLocal, FeeType
from app import app
import os

def verify():
    print(f"CWD: {os.getcwd()}")
    session = SessionLocal()
    try:
        # 1. Verify FeeType model works
        print("Testing FeeType model...")
        # Check if it already exists
        ft = session.query(FeeType).filter_by(name="Verification Fee").first()
        if not ft:
            new_fee = FeeType(name="Verification Fee")
            session.add(new_fee)
            session.commit()
            print("Created 'Verification Fee'.")
        else:
            print("'Verification Fee' already exists.")
        
        # 2. Verify Response Content
        print("Testing Response Content...")
        with app.test_client() as client:
            response = client.get('/customers/new') # Correct URL is /customers/new, not /new-customer!
            content = response.data.decode('utf-8')
            
            if "Verification Fee" in content:
                print("SUCCESS: 'Verification Fee' found in /customers/new response.")
            else:
                print("FAILURE: 'Verification Fee' NOT found in response.")
                print("Partial content preview:")
                print(content[:500]) # Print first 500 chars
                print("...")
                # Check if we are getting a redirect or error
                print(f"Status Code: {response.status_code}")

        # 3. Clean up
        ft = session.query(FeeType).filter_by(name="Verification Fee").first()
        if ft:
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
