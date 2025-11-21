import sqlite3

def migrate():
    conn = sqlite3.connect('invoice_app.db')
    cursor = conn.cursor()
    
    try:
        print("Creating fee_types table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fee_types (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR NOT NULL UNIQUE
            )
        """)
        
        print("Seeding initial fee types...")
        initial_types = ["Management Fee", "Assessment", "Special Assessment", "Late Fee"]
        for ft in initial_types:
            try:
                cursor.execute("INSERT INTO fee_types (name) VALUES (?)", (ft,))
            except sqlite3.IntegrityError:
                print(f"Fee type '{ft}' already exists.")
                
        conn.commit()
        print("Successfully created and seeded fee_types table.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
