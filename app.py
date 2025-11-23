from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file
from apscheduler.schedulers.background import BackgroundScheduler
import os
import traceback

from models import init_db, SessionLocal, Customer, Invoice, FeeType


app = Flask(__name__)
from invoice_generator import generate_invoice_for_customer, get_invoice_templates, generate_invoice_with_template, generate_invoice_buffer, get_period_label

# Initialize DB (safe to run multiple times)
init_db()

@app.route("/generate-invoice", methods=["GET", "POST"])
def generate_invoice():
    session = SessionLocal()
    try:
        customers = session.query(Customer).all()
        templates = get_invoice_templates()
        fee_types = session.query(FeeType).all()
        
        if request.method == "POST":
            # Debug logging
            print(f"DEBUG: Form Data Received: {request.form}")
            
            customer_id = int(request.form["customer_id"])
            invoice_date = date.fromisoformat(request.form["invoice_date"])
            template_name = request.form["template_name"]
            
            fee_2_type = request.form.get("fee_2_type")
            fee_2_amount = float(request.form["fee_2_amount"]) if request.form.get("fee_2_amount") else None
            
            fee_3_type = request.form.get("fee_3_type")
            fee_3_amount = float(request.form["fee_3_amount"]) if request.form.get("fee_3_amount") else None
            
            additional_fee_desc = request.form.get("additional_fee_desc")
            additional_fee_amount = float(request.form["additional_fee_amount"]) if request.form.get("additional_fee_amount") else None
            
            print(f"DEBUG: Extracted Fees: Fee2={fee_2_type}/${fee_2_amount}, Fee3={fee_3_type}/${fee_3_amount}")

            customer = session.query(Customer).get(customer_id)
            
            # Pass extra fees as kwargs
            invoice = generate_invoice_with_template(
                customer, 
                invoice_date, 
                template_name,
                fee_2_type=fee_2_type,
                fee_2_amount=fee_2_amount,
                fee_3_type=fee_3_type,
                fee_3_amount=fee_3_amount,
                additional_fee_desc=additional_fee_desc,
                additional_fee_amount=additional_fee_amount
            )
            return redirect(url_for("list_invoices"))
        return render_template("generate_invoice.html", customers=customers, templates=templates, fee_types=fee_types, date=date)
    finally:
        session.close()

def bill_due_customers():
    """Run once a day: generate invoices for customers whose next_bill_date is today or in the past."""
    session = SessionLocal()
    try:
        today = date.today()
        # Catch up on any missed invoices
        customers = session.query(Customer).filter(Customer.next_bill_date <= today).all()
        
        for c in customers:
            # Process all due periods until next_bill_date is in the future
            # Limit iterations to prevent infinite loops in case of logic error
            max_iterations = 12 
            iterations = 0
            
            while c.next_bill_date <= today and iterations < max_iterations:
                iterations += 1
                
                # Check if invoice already exists for this period
                period_label = get_period_label(c.next_bill_date, c.cadence)
                existing_invoice = session.query(Invoice).filter(
                    Invoice.customer_id == c.id,
                    Invoice.period_label == period_label
                ).first()
                
                if not existing_invoice:
                    print(f"Generating invoice for {c.name} - {period_label}")
                    generate_invoice_for_customer(c, c.next_bill_date)
                else:
                    print(f"Skipping {c.name} - {period_label} (Invoice already exists)")

                # Advance next_bill_date based on cadence
                if c.cadence == "monthly":
                    # 1st of next month
                    if c.next_bill_date.month == 12:
                        c.next_bill_date = c.next_bill_date.replace(year=c.next_bill_date.year + 1, month=1, day=1)
                    else:
                        c.next_bill_date = c.next_bill_date.replace(month=c.next_bill_date.month + 1, day=1)
                elif c.cadence == "quarterly":
                    # 1/1, 4/1, 7/1, 10/1
                    current_month = c.next_bill_date.month
                    if current_month < 4:
                        next_month = 4
                        next_year = c.next_bill_date.year
                    elif current_month < 7:
                        next_month = 7
                        next_year = c.next_bill_date.year
                    elif current_month < 10:
                        next_month = 10
                        next_year = c.next_bill_date.year
                    else:
                        next_month = 1
                        next_year = c.next_bill_date.year + 1
                    
                    c.next_bill_date = c.next_bill_date.replace(year=next_year, month=next_month, day=1)
                elif c.cadence == "yearly":
                    c.next_bill_date = c.next_bill_date.replace(year=c.next_bill_date.year + 1)

            session.add(c)
        session.commit()
    finally:
        session.close()

@app.route("/")
def index():
    return redirect(url_for("list_customers"))

@app.route("/customers")
def list_customers():
    session = SessionLocal()
    try:
        customers = session.query(Customer).all()
        return render_template("customers.html", customers=customers)
    except Exception as e:
        with open("debug.log", "a") as f:
            import traceback
            traceback.print_exc(file=f)
        return str(e), 500
    finally:
        session.close()

@app.route("/customers/new", methods=["GET", "POST"])
def new_customer():
    with open("debug.log", "a") as f:
        f.write("DEBUG: Entered new_customer\n")
    if request.method == "POST":
        try:
            with open("debug.log", "a") as f:
                f.write("DEBUG: Starting POST new_customer\n")
            name = request.form["name"]
            sys.stderr.write(f"DEBUG: Name={name}\n")
            email = request.form["email"]
            property_address = request.form["property_address"]
            property_city = request.form["property_city"]
            property_state = request.form["property_state"]
            property_zip = request.form["property_zip"]
            rate = float(request.form["rate"])
            cadence = request.form["cadence"]
            fee_type = request.form.get("fee_type", "Management Fee")
            next_bill_date_str = request.form["next_bill_date"]
            next_bill_date = date.fromisoformat(next_bill_date_str)
            sys.stderr.write("DEBUG: Extracted basic fields\n")

            # Extract new fee fields
            fee_2_type = request.form.get("fee_2_type")
            fee_2_rate_str = request.form.get("fee_2_rate", "")
            fee_2_rate = float(fee_2_rate_str) if fee_2_rate_str else None

            fee_3_type = request.form.get("fee_3_type")
            fee_3_rate_str = request.form.get("fee_3_rate", "")
            fee_3_rate = float(fee_3_rate_str) if fee_3_rate_str else None

            additional_fee_desc = request.form.get("additional_fee_desc")
            additional_fee_amount_str = request.form.get("additional_fee_amount", "")
            additional_fee_amount = float(additional_fee_amount_str) if additional_fee_amount_str else None
            sys.stderr.write("DEBUG: Extracted fee fields\n")

            new_customer = Customer(
                name=name,
                email=email,
                property_address=property_address,
                property_city=property_city,
                property_state=property_state,
                property_zip=property_zip,
                rate=rate,
                cadence=cadence,
                fee_type=fee_type,
                next_bill_date=next_bill_date,
                fee_2_type=fee_2_type,
                fee_2_rate=fee_2_rate,
                fee_3_type=fee_3_type,
                fee_3_rate=fee_3_rate,
                additional_fee_desc=additional_fee_desc,
                additional_fee_amount=additional_fee_amount
            )
            sys.stderr.write("DEBUG: Created Customer object\n")
            session.add(new_customer)
            sys.stderr.write("DEBUG: Added to session\n")
            session.commit()
            sys.stderr.write("DEBUG: Committed\n")
            return redirect(url_for('list_customers'))
        except Exception as e:
            sys.stderr.write(f"DEBUG: Exception: {e}\n")
            import traceback
            traceback.print_exc()
            return str(e), 500

    session = SessionLocal()
    try:
        fee_types = session.query(FeeType).all()
        return render_template("new_customer.html", fee_types=fee_types)
    finally:
        session.close()

@app.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
def edit_customer(customer_id):
    session = SessionLocal()
    try:
        customer = session.query(Customer).get(customer_id)
        fee_types = session.query(FeeType).all()
        if not customer:
            return redirect(url_for("list_customers"))

        if request.method == "POST":
            customer.name = request.form["name"]
            customer.email = request.form["email"]
            customer.property_address = request.form["property_address"]
            customer.property_city = request.form["property_city"]
            customer.property_state = request.form["property_state"]
            customer.property_zip = request.form["property_zip"]
            customer.rate = float(request.form["rate"])
            customer.cadence = request.form["cadence"]
            customer.fee_type = request.form.get("fee_type", "Management Fee")
            customer.next_bill_date = date.fromisoformat(request.form["next_bill_date"])
            
            # Handle fee_2 fields
            customer.fee_2_type = request.form.get("fee_2_type", "")
            fee_2_rate_str = request.form.get("fee_2_rate", "")
            customer.fee_2_rate = float(fee_2_rate_str) if fee_2_rate_str else None
            
            # Handle fee_3 fields
            customer.fee_3_type = request.form.get("fee_3_type", "")
            fee_3_rate_str = request.form.get("fee_3_rate", "")
            customer.fee_3_rate = float(fee_3_rate_str) if fee_3_rate_str else None
            
            # Handle additional fee fields
            customer.additional_fee_desc = request.form.get("additional_fee_desc", "")
            additional_fee_amount_str = request.form.get("additional_fee_amount", "")
            customer.additional_fee_amount = float(additional_fee_amount_str) if additional_fee_amount_str else None
            
            session.commit()
            return redirect(url_for("list_customers"))
        
        
        return render_template("edit_customer.html", customer=customer, fee_types=fee_types)
    finally:
        session.close()

@app.route("/customers/<int:customer_id>/add-property", methods=["POST"])
def add_property(customer_id):
    from models import Property
    session = SessionLocal()
    try:
        address = request.form.get("address")
        city = request.form.get("city")
        state = request.form.get("state")
        zip_code = request.form.get("zip_code")
        fee_amount_str = request.form.get("fee_amount")
        fee_amount = float(fee_amount_str) if fee_amount_str else None
        
        new_prop = Property(
            customer_id=customer_id,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            fee_amount=fee_amount
        )
        session.add(new_prop)
        session.commit()
        return redirect(url_for("edit_customer", customer_id=customer_id))
    finally:
        session.close()

@app.route("/customers/<int:customer_id>/delete-property/<int:property_id>", methods=["POST"])
def delete_property(customer_id, property_id):
    from models import Property
    session = SessionLocal()
    try:
        prop = session.query(Property).get(property_id)
        if prop and prop.customer_id == customer_id:
            session.delete(prop)
            session.commit()
        return redirect(url_for("edit_customer", customer_id=customer_id))
    finally:
        session.close()

@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def delete_customer(customer_id):
    session = SessionLocal()
    try:
        customer = session.query(Customer).get(customer_id)
        if customer:
            # User requested NOT to delete invoices when deleting a customer.
            # Customer deletion will fail if there are invoices due to NOT NULL constraint
            session.delete(customer)
            session.commit()
        return redirect(url_for("list_customers"))
    finally:
        session.close()

@app.route("/settings/fee-types", methods=["GET", "POST"])
def manage_fee_types():
    session = SessionLocal()
    try:
        if request.method == "POST":
            name = request.form.get("name")
            if name:
                try:
                    ft = FeeType(name=name)
                    session.add(ft)
                    session.commit()
                except Exception:
                    session.rollback()
            return redirect(url_for("manage_fee_types"))
        
        fee_types = session.query(FeeType).all()
        return render_template("fee_types.html", fee_types=fee_types)
    finally:
        session.close()

@app.route("/settings/fee-types/<int:fee_type_id>/delete", methods=["POST"])
def delete_fee_type(fee_type_id):
    session = SessionLocal()
    try:
        ft = session.query(FeeType).get(fee_type_id)
        if ft:
            session.delete(ft)
            session.commit()
        return redirect(url_for("manage_fee_types"))
    finally:
        session.close()

@app.route("/invoices")
def list_invoices():
    session = SessionLocal()
    try:
        # Sort by Customer Name then Invoice Date
        # We need to join Customer to sort by name
        invoices = session.query(Invoice).join(Customer, Invoice.customer_id == Customer.id).order_by(Customer.name.asc(), Invoice.invoice_date.desc()).all()
        
        # For simplicity, join customers manually (or use the join above)
        customers_map = {c.id: c for c in session.query(Customer).all()}
        return render_template("invoices.html", invoices=invoices, customers=customers_map)
    finally:
        session.close()

@app.route("/run-today")
def run_today():
    bill_due_customers()
    return redirect(url_for("list_invoices"))

@app.route("/invoices/<int:invoice_id>/download")
def download_invoice(invoice_id):
    session = SessionLocal()
    try:
        invoice = session.query(Invoice).get(invoice_id)
        if not invoice:
            return "Invoice not found", 404
        
        filename, buffer = generate_invoice_buffer(invoice)
        return send_file(
            buffer,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
    except Exception as e:
        return f"Error generating invoice: {e}", 500
    finally:
        session.close()

@app.route("/seed-data")
def run_seeding():
    try:
        from seed_from_templates import seed_customers
        # Capture output to return to user
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            seed_customers()
        
        output = f.getvalue()
        return f"<pre>{output}</pre>"
    except Exception as e:
        return f"Error seeding data: {e}", 500

@app.route('/clear-invoices')
def clear_invoices_route():
    from models import Invoice
    session = SessionLocal()
    try:
        count = session.query(Invoice).count()
        session.query(Invoice).delete()
        session.commit()
        return f'Cleared {count} invoices from the database!', 200
    except Exception as e:
        session.rollback()
        return f'Error: {str(e)}', 500
    finally:
        session.close()

@app.route('/migrate-db')
def run_migration():
    from sqlalchemy import create_engine, text
    import os
    
    database_url = os.getenv("POSTGRES_URL") or os.getenv("DATABASE_URL") or "sqlite:///invoice_app.db"
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            # Add new columns to invoices table
            invoice_columns = [
                ("fee_2_type", "VARCHAR"),
                ("fee_2_amount", "FLOAT"),
                ("fee_3_type", "VARCHAR"),
                ("fee_3_amount", "FLOAT"),
                ("additional_fee_desc", "VARCHAR"),
                ("additional_fee_amount", "FLOAT")
            ]
            
            results = []
            for col_name, col_type in invoice_columns:
                try:
                    if "sqlite" in database_url:
                        conn.execute(text(f"ALTER TABLE invoices ADD COLUMN {col_name} {col_type}"))
                    else:
                        conn.execute(text(f"ALTER TABLE invoices ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    results.append(f"Added invoices.{col_name}")
                except Exception as e:
                    results.append(f"Skipped invoices.{col_name}: {str(e)}")
            
            # Add new columns to customers table
            customer_columns = [
                ("fee_2_type", "VARCHAR"),
                ("fee_2_rate", "FLOAT"),
                ("fee_3_type", "VARCHAR"),
                ("fee_3_rate", "FLOAT"),
                ("additional_fee_desc", "VARCHAR"),
                ("additional_fee_amount", "FLOAT")
            ]
            
            for col_name, col_type in customer_columns:
                try:
                    if "sqlite" in database_url:
                        conn.execute(text(f"ALTER TABLE customers ADD COLUMN {col_name} {col_type}"))
                    else:
                        conn.execute(text(f"ALTER TABLE customers ADD COLUMN IF NOT EXISTS {col_name} {col_type}"))
                    results.append(f"Added customers.{col_name}")
                except Exception as e:
                    results.append(f"Skipped customers.{col_name}: {str(e)}")
            
            # Create properties table
            from models import Base
            Base.metadata.create_all(bind=engine)
            results.append("Ensured properties table exists")
            
            # Add fee_amount to properties (in case properties existed before)
            try:
                if "sqlite" in database_url:
                    conn.execute(text("ALTER TABLE properties ADD COLUMN fee_amount FLOAT"))
                else:
                    conn.execute(text("ALTER TABLE properties ADD COLUMN IF NOT EXISTS fee_amount FLOAT"))
                results.append("Added properties.fee_amount")
            except Exception as e:
                results.append(f"Skipped properties.fee_amount: {str(e)}")
            
            # Commit all changes
            conn.commit()
            
            return f"Migration results:<br>" + "<br>".join(results)
    except Exception as e:
        return f"Migration failed: {e}", 500

if __name__ == "__main__":
    init_db()
    print(app.url_map)

    # Only run scheduler if NOT in Vercel (check for VERCEL env var)
    # In Vercel, we use Vercel Cron to hit /run-today
    # if not os.environ.get("VERCEL"):
    #     scheduler = BackgroundScheduler()
    #     # Run once every day at 6am, for example
    #     scheduler.add_job(bill_due_customers, "cron", hour=6, minute=0)
    #     scheduler.start()

    app.run(debug=True)
