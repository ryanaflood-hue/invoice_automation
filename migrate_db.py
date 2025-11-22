import sqlite3
import os
from sqlalchemy import create_engine, text

# Use DATABASE_URL if available (Vercel/Heroku), else local SQLite
database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or "sqlite:///invoice_app.db"

if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

def migrate():
    engine = create_engine(database_url)
    with engine.connect() as conn:
        print("Migrating database...")
        
        # 1. Add new columns to invoices table
        # SQLite doesn't support IF NOT EXISTS for ADD COLUMN, so we try/except
        new_columns = [
            ("fee_2_type", "VARCHAR"),
            ("fee_2_amount", "FLOAT"),
            ("fee_3_type", "VARCHAR"),
            ("fee_3_amount", "FLOAT"),
            ("additional_fee_desc", "VARCHAR"),
            ("additional_fee_amount", "FLOAT")
        ]
        
        for col_name, col_type in new_columns:
            try:
                if "sqlite" in database_url:
                    conn.execute(text(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}"))
                else:
                    # Postgres
                    conn.execute(text(f"ALTER TABLE invoices ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                print(f"Added column {col_name} to invoices")
            except Exception as e:
                print(f"Column {col_name} might already exist: {e}")

        # 2. Create properties table
        # We can use the models metadata to create the table if it doesn't exist
        from models import Base
        Base.metadata.create_all(bind=engine)
        print("Created properties table (if it didn't exist)")
        
        print("Migration complete!")

if __name__ == "__main__":
    migrate()
