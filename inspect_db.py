from sqlalchemy import create_engine, inspect
import os

database_url = "sqlite:///invoice_app_v2.db"
engine = create_engine(database_url)
inspector = inspect(engine)
columns = inspector.get_columns('invoices')
for column in columns:
    print(column['name'], column['type'])
