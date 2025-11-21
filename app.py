from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, send_file
from apscheduler.schedulers.background import BackgroundScheduler
import os

from models import init_db, SessionLocal, Customer, Invoice, FeeType


app = Flask(__name__)
from invoice_generator import generate_invoice_for_customer, get_invoice_templates, generate_invoice_with_template, generate_invoice_buffer

# Initialize DB (safe to run multiple times)
init_db()

@app.route("/generate-invoice", methods=["GET", "POST"])
def generate_invoice():
    session = SessionLocal()
    try:
        customers = session.query(Customer).all()
        templates = get_invoice_templates()
        if request.method == "POST":
            customer_id = int(request.form["customer_id"])
            invoice_date = date.fromisoformat(request.form["invoice_date"])
            template_name = request.form["template_name"]
            customer = session.query(Customer).get(customer_id)
            invoice = generate_invoice_with_template(customer, invoice_date, template_name)
            return redirect(url_for("list_invoices"))
        return render_template("generate_invoice.html", customers=customers, templates=templates)
    finally:
        session.close()

def bill_due_customers():
    """Run once a day: generate invoices for customers whose next_bill_date is today."""
    session = SessionLocal()
    try:
        today = date.today()
        customers = session.query(Customer).filter(Customer.next_bill_date == today).all()
        for c in customers:
            generate_invoice_for_customer(c, today)

            # Advance next_bill_date based on cadence
            if c.cadence == "monthly":
                c.next_bill_date = c.next_bill_date + timedelta(days=30)
            elif c.cadence == "quarterly":
                c.next_bill_date = c.next_bill_date + timedelta(days=90)
            elif c.cadence == "yearly":
                c.next_bill_date = c.next_bill_date + timedelta(days=365)

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
    finally:
        session.close()

@app.route("/customers/new", methods=["GET", "POST"])
def new_customer():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        address = request.form["property_address"]
        city = request.form["property_city"]
        state = request.form["property_state"]
        zip_code = request.form["property_zip"]
        rate = float(request.form["rate"])
        cadence = request.form["cadence"]
        fee_type = request.form.get("fee_type", "Management Fee")
        next_bill_date = date.fromisoformat(request.form["next_bill_date"])

        session = SessionLocal()
        try:
            c = Customer(
                name=name,
                email=email,
                property_address=address,
                property_city=city,
                property_state=state,
                property_zip=zip_code,
                rate=rate,
                cadence=cadence,
                fee_type=fee_type,
                next_bill_date=next_bill_date,
            )
            session.add(c)
            session.commit()
        finally:
            session.close()
        return redirect(url_for("list_customers"))

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
            
            session.commit()
            return redirect(url_for("list_customers"))
        
        
        return render_template("edit_customer.html", customer=customer, fee_types=fee_types)
    finally:
        session.close()

@app.route("/settings/fee-types", methods=["GET", "POST"])
def manage_fee_types():
    session = SessionLocal()
    try:
        if request.method == "POST":
            name = request.form["name"]
            if name:
                try:
                    ft = FeeType(name=name)
                    session.add(ft)
                    session.commit()
                except Exception:
                    session.rollback() # Handle duplicate or error
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
        invoices = session.query(Invoice).order_by(Invoice.invoice_date.desc()).all()
        # For simplicity, join customers manually
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

if __name__ == "__main__":
    init_db()

    # Only run scheduler if NOT in Vercel (check for VERCEL env var)
    # In Vercel, we use Vercel Cron to hit /run-today
    if not os.environ.get("VERCEL"):
        scheduler = BackgroundScheduler()
        # Run once every day at 6am, for example
        scheduler.add_job(bill_due_customers, "cron", hour=6, minute=0)
        scheduler.start()

    app.run(debug=True)
