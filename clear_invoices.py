"""
Script to clear all invoices from the database.
Use with caution - this will delete ALL invoice records!
"""
from models import SessionLocal, Invoice

def clear_all_invoices():
    session = SessionLocal()
    try:
        count = session.query(Invoice).count()
        print(f"Found {count} invoices in the database")
        
        if count > 0:
            confirm = input(f"Are you sure you want to delete all {count} invoices? (yes/no): ")
            if confirm.lower() == 'yes':
                session.query(Invoice).delete()
                session.commit()
                print(f"✓ Deleted {count} invoices")
            else:
                print("Cancelled")
        else:
            print("No invoices to delete")
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    clear_all_invoices()
