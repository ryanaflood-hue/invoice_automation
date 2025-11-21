import sqlite3

def migrate():
    conn = sqlite3.connect('invoice_app.db')
    cursor = conn.cursor()
    
    try:
        print("Attempting to add fee_type column to customers table...")
        cursor.execute("ALTER TABLE customers ADD COLUMN fee_type VARCHAR DEFAULT 'Management Fee'")
        conn.commit()
        print("Successfully added fee_type column.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("Column fee_type already exists. Skipping.")
        else:
            print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
