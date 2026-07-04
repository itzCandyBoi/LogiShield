import csv
import io
import json
import os
import re
import smtplib
import sqlite3
import urllib.request
from datetime import datetime
from functools import wraps
from typing import BinaryIO

from flask import Flask, Response, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "logishield-demo-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
DATABASE = os.path.join(app.root_path, "logishield.db")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                alert_threshold INTEGER DEFAULT 2,
                notification_preference TEXT DEFAULT 'email'
            );

            CREATE TABLE IF NOT EXISTS reconciliations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL,
                invoice_name TEXT NOT NULL,
                receipt_name TEXT NOT NULL,
                total_items INTEGER NOT NULL,
                total_discrepancies INTEGER NOT NULL,
                potential_loss REAL NOT NULL,
                status TEXT NOT NULL,
                notification_status TEXT DEFAULT 'none',
                FOREIGN KEY(user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS discrepancies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reconciliation_id INTEGER NOT NULL,
                item_name TEXT NOT NULL,
                invoice_qty INTEGER NOT NULL,
                receipt_qty INTEGER NOT NULL,
                delta INTEGER NOT NULL,
                severity TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                FOREIGN KEY(reconciliation_id) REFERENCES reconciliations(id)
            );
            """
        )
        columns = {row[1] for row in conn.execute("PRAGMA table_info(discrepancies)").fetchall()}
        if "status" not in columns:
            conn.execute("ALTER TABLE discrepancies ADD COLUMN status TEXT DEFAULT 'open'")

        columns = {row[1] for row in conn.execute("PRAGMA table_info(reconciliations)").fetchall()}
        if "notification_status" not in columns:
            conn.execute("ALTER TABLE reconciliations ADD COLUMN notification_status TEXT DEFAULT 'none'")

        demo_user = conn.execute(
            "SELECT id FROM users WHERE email = ?", ("demo@logishield.com",)
        ).fetchone()
        if demo_user is None:
            conn.execute(
                """
                INSERT INTO users (name, email, password_hash, alert_threshold, notification_preference)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Demo Operator",
                    "demo@logishield.com",
                    generate_password_hash("demo1234"),
                    2,
                    "email",
                ),
            )

        if conn.execute("SELECT COUNT(*) FROM reconciliations").fetchone()[0] == 0:
            invoice_content = """item,quantity,price
Widget A,100,12.50
Widget B,20,8.00
Widget C,15,4.50
"""
            receipt_content = """item,quantity
Widget A,85
Widget B,20
Widget C,15
"""
            details = reconcile_uploads(
                io.BytesIO(invoice_content.encode("utf-8")),
                io.BytesIO(receipt_content.encode("utf-8")),
            )
            demo_user_id = conn.execute(
                "SELECT id FROM users WHERE email = ?", ("demo@logishield.com",)
            ).fetchone()["id"]
            reconciliation_id = conn.execute(
                """
                INSERT INTO reconciliations (
                    user_id, created_at, title, invoice_name, receipt_name,
                    total_items, total_discrepancies, potential_loss, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    demo_user_id,
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    "Demo discrepancy: Widget A overcharge",
                    "supplier_invoice.csv",
                    "warehouse_receipt.csv",
                    details["summary"]["total_items"],
                    details["summary"]["total_discrepancies"],
                    details["summary"]["potential_loss"],
                    "Needs review",
                ),
            ).lastrowid
            for discrepancy in details["discrepancies"]:
                conn.execute(
                    """
                    INSERT INTO discrepancies (
                        reconciliation_id, item_name, invoice_qty, receipt_qty, delta, severity, reason
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reconciliation_id,
                        discrepancy["item_name"],
                        discrepancy["invoice_qty"],
                        discrepancy["receipt_qty"],
                        discrepancy["delta"],
                        discrepancy["severity"],
                        discrepancy["reason"],
                    ),
                )


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parse_csv_rows(file_like: BinaryIO):
    file_like.seek(0)
    raw_text = file_like.read().decode("utf-8", errors="ignore")
    if not raw_text.strip():
        return []

    reader = csv.DictReader(io.StringIO(raw_text))
    rows = []
    for row in reader:
        rows.append(
            {
                "item_name": (row.get("item") or row.get("sku") or row.get("product") or row.get("description") or row.get("name") or "Unknown").strip(),
                "quantity": int(float(row.get("quantity") or row.get("qty") or row.get("units") or 0)),
                "price": float(row.get("price") or row.get("unit_price") or row.get("amount") or 0),
            }
        )
    return rows


def parse_pdf_rows(file_like: BinaryIO):
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        return []

    file_like.seek(0)
    reader = PdfReader(file_like)
    text_pages = [page.extract_text() or "" for page in reader.pages]
    raw_text = "\n".join(text_pages).strip()
    if not raw_text:
        return []

    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    header_index = 0
    for index, line in enumerate(lines):
        if re.search(r"\b(item|sku|product|description|name)\b", line, re.I) and re.search(r"\b(quantity|qty|units)\b", line, re.I):
            header_index = index
            break

    rows = []
    for line in lines[header_index + 1 :]:
        if re.search(r"^total\b", line, re.I):
            continue
        columns = re.split(r"[\t,]{1,}| {2,}", line)
        if len(columns) < 2:
            continue
        item = columns[0].strip()
        qty = re.sub(r"[^0-9.-]", "", columns[1]) or "0"
        price = "0"
        if len(columns) > 2:
            price = re.sub(r"[^0-9.-]", "", columns[2]) or "0"
        try:
            rows.append(
                {
                    "item_name": item,
                    "quantity": int(float(qty)),
                    "price": float(price),
                }
            )
        except ValueError:
            continue

    if rows:
        return rows

    # fallback: extract numeric rows from text
    for line in lines:
        match = re.search(r"(.+?)\s+(\d+)\s+(\d+(?:\.\d+)?)$", line)
        if match:
            item = match.group(1).strip()
            qty = match.group(2)
            price = match.group(3)
            try:
                rows.append(
                    {
                        "item_name": item,
                        "quantity": int(float(qty)),
                        "price": float(price),
                    }
                )
            except ValueError:
                continue
    return rows


def parse_uploaded_document(uploaded_file):
    filename = (uploaded_file.filename or "").lower()
    if filename.endswith(".pdf") or uploaded_file.content_type == "application/pdf":
        return parse_pdf_rows(uploaded_file.stream)
    return parse_csv_rows(uploaded_file.stream)


def send_slack_message(text: str) -> bool:
    webhook_url = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False
    payload = json.dumps({"text": text}).encode("utf-8")
    request_obj = urllib.request.Request(
        webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request_obj, timeout=10) as response:
            return response.status == 200
    except Exception:
        return False


def send_email_notification(to_email: str, subject: str, body: str) -> bool:
    smtp_server = os.environ.get("SMTP_SERVER")
    smtp_port = int(os.environ.get("SMTP_PORT", 25))
    smtp_user = os.environ.get("SMTP_USERNAME")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("EMAIL_SENDER")
    if not smtp_server or not sender:
        return False
    message = f"Subject: {subject}\nFrom: {sender}\nTo: {to_email}\n\n{body}"
    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.sendmail(sender, [to_email], message)
        return True
    except Exception:
        return False


def notify_user(user, details):
    text = (
        f"LogiShield alert: {details['summary']['total_discrepancies']} discrepancies detected "
        f"in {details['summary']['total_items']} lines. Estimated exposure ${details['summary']['potential_loss']}."
    )
    if user["notification_preference"] == "slack":
        return "sent" if send_slack_message(text) else "failed"
    if user["notification_preference"] == "email":
        return "sent" if send_email_notification(user["email"], "LogiShield discrepancy alert", text) else "failed"
    return "none"


def reconcile_uploads(invoice_file: BinaryIO, receipt_file: BinaryIO):
    invoice_items = parse_csv_rows(invoice_file)
    receipt_items = parse_csv_rows(receipt_file)

    discrepancies = []
    invoice_lookup = {normalize_text(item["item_name"]): item for item in invoice_items}
    receipt_lookup = {normalize_text(item["item_name"]): item for item in receipt_items}

    for item_name, invoice_item in invoice_lookup.items():
        receipt_item = receipt_lookup.get(item_name)
        if receipt_item is None:
            discrepancies.append(
                {
                    "item_name": invoice_item["item_name"],
                    "invoice_qty": invoice_item["quantity"],
                    "receipt_qty": 0,
                    "delta": invoice_item["quantity"],
                    "severity": "high",
                    "reason": "Receipt missing for billed item",
                }
            )
            continue

        delta = invoice_item["quantity"] - receipt_item["quantity"]
        if delta != 0:
            abs_delta = abs(delta)
            if abs_delta >= 20:
                severity = "high"
            elif abs_delta >= 5:
                severity = "medium"
            else:
                severity = "low"
            discrepancies.append(
                {
                    "item_name": invoice_item["item_name"],
                    "invoice_qty": invoice_item["quantity"],
                    "receipt_qty": receipt_item["quantity"],
                    "delta": delta,
                    "severity": severity,
                    "reason": "Invoice quantity differs from warehouse receipt",
                }
            )

    for item_name, receipt_item in receipt_lookup.items():
        if item_name not in invoice_lookup:
            severity = "high" if receipt_item["quantity"] >= 10 else "medium"
            discrepancies.append(
                {
                    "item_name": receipt_item["item_name"],
                    "invoice_qty": 0,
                    "receipt_qty": receipt_item["quantity"],
                    "delta": -receipt_item["quantity"],
                    "severity": severity,
                    "reason": "Unexpected receipt line not present in invoice",
                }
            )

    total_items = max(len(invoice_items), len(receipt_items))
    invoice_price_lookup = {
        normalize_text(item["item_name"]): item.get("price", 0) for item in invoice_items
    }
    potential_loss = sum(
        abs(item["delta"]) * invoice_price_lookup.get(normalize_text(item["item_name"]), 0)
        for item in discrepancies
    )

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for item in discrepancies:
        severity_counts[item["severity"]] = severity_counts.get(item["severity"], 0) + 1

    if severity_counts["high"] >= 1 or potential_loss >= 500:
        risk_level = "High"
    elif severity_counts["medium"] >= 1 or potential_loss >= 150:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "summary": {
            "total_items": total_items,
            "total_discrepancies": len(discrepancies),
            "potential_loss": round(potential_loss, 2),
            "risk_level": risk_level,
            "severity_counts": severity_counts,
        },
        "discrepancies": discrepancies,
    }


def reconcile_uploads_from_data(invoice_items, receipt_items):
    invoice_lookup = {normalize_text(item["item_name"]): item for item in invoice_items}
    receipt_lookup = {normalize_text(item["item_name"]): item for item in receipt_items}

    discrepancies = []
    for item_name, invoice_item in invoice_lookup.items():
        receipt_item = receipt_lookup.get(item_name)
        if receipt_item is None:
            discrepancies.append(
                {
                    "item_name": invoice_item["item_name"],
                    "invoice_qty": invoice_item["quantity"],
                    "receipt_qty": 0,
                    "delta": invoice_item["quantity"],
                    "severity": "high",
                    "reason": "Receipt missing for billed item",
                }
            )
            continue

        delta = invoice_item["quantity"] - receipt_item["quantity"]
        if delta != 0:
            abs_delta = abs(delta)
            if abs_delta >= 20:
                severity = "high"
            elif abs_delta >= 5:
                severity = "medium"
            else:
                severity = "low"
            discrepancies.append(
                {
                    "item_name": invoice_item["item_name"],
                    "invoice_qty": invoice_item["quantity"],
                    "receipt_qty": receipt_item["quantity"],
                    "delta": delta,
                    "severity": severity,
                    "reason": "Invoice quantity differs from warehouse receipt",
                }
            )

    for item_name, receipt_item in receipt_lookup.items():
        if item_name not in invoice_lookup:
            severity = "high" if receipt_item["quantity"] >= 10 else "medium"
            discrepancies.append(
                {
                    "item_name": receipt_item["item_name"],
                    "invoice_qty": 0,
                    "receipt_qty": receipt_item["quantity"],
                    "delta": -receipt_item["quantity"],
                    "severity": severity,
                    "reason": "Unexpected receipt line not present in invoice",
                }
            )

    total_items = max(len(invoice_items), len(receipt_items))
    invoice_price_lookup = {
        normalize_text(item["item_name"]): item.get("price", 0) for item in invoice_items
    }
    potential_loss = sum(
        abs(item["delta"]) * invoice_price_lookup.get(normalize_text(item["item_name"]), 0)
        for item in discrepancies
    )

    severity_counts = {"high": 0, "medium": 0, "low": 0}
    for item in discrepancies:
        severity_counts[item["severity"]] = severity_counts.get(item["severity"], 0) + 1

    if severity_counts["high"] >= 1 or potential_loss >= 500:
        risk_level = "High"
    elif severity_counts["medium"] >= 1 or potential_loss >= 150:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "summary": {
            "total_items": total_items,
            "total_discrepancies": len(discrepancies),
            "potential_loss": round(potential_loss, 2),
            "risk_level": risk_level,
            "severity_counts": severity_counts,
        },
        "discrepancies": discrepancies,
    }


def login_required(view_func):
    @wraps(view_func)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            flash("Please sign in to continue.", "warning")
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return decorated


def get_current_user():
    if not session.get("user_id"):
        return None
    with get_db() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE id = ?", (session["user_id"],)
        ).fetchone()


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            flash("Welcome back to LogiShield.", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or not password:
            flash("All fields are required.", "warning")
            return redirect(url_for("register"))
        with get_db() as conn:
            existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if existing:
                flash("That email already exists.", "warning")
                return redirect(url_for("register"))
            conn.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, generate_password_hash(password)),
            )
        flash("Account created. Please sign in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    with get_db() as conn:
        total_cases = conn.execute("SELECT COUNT(*) FROM reconciliations").fetchone()[0]
        total_discrepancies = conn.execute(
            "SELECT COALESCE(SUM(total_discrepancies), 0) FROM reconciliations"
        ).fetchone()[0]
        potential_loss = conn.execute(
            "SELECT COALESCE(SUM(potential_loss), 0) FROM reconciliations"
        ).fetchone()[0]
        recent_cases = conn.execute(
            "SELECT * FROM reconciliations ORDER BY created_at DESC LIMIT 4"
        ).fetchall()
        severity_rows = conn.execute(
            "SELECT severity, COUNT(*) as count FROM discrepancies GROUP BY severity"
        ).fetchall()
    severity_counts = {row["severity"]: row["count"] for row in severity_rows}
    stats = {
        "total_cases": total_cases,
        "total_discrepancies": total_discrepancies,
        "potential_loss": round(float(potential_loss), 2),
        "high_risk": severity_counts.get("high", 0),
        "medium_risk": severity_counts.get("medium", 0),
        "low_risk": severity_counts.get("low", 0),
    }
    return render_template("dashboard.html", user=user, stats=stats, cases=recent_cases)


@app.route("/core-business", methods=["GET", "POST"])
@login_required
def core_business():
    user = get_current_user()
    details = None
    latest_case = None
    if request.method == "POST":
        invoice_file = request.files.get("invoice_file")
        receipt_file = request.files.get("receipt_file")
        if not invoice_file or not receipt_file:
            flash("Please upload both files.", "warning")
            return redirect(url_for("core_business"))

        invoice_rows = parse_uploaded_document(invoice_file)
        receipt_rows = parse_uploaded_document(receipt_file)
        if not invoice_rows or not receipt_rows:
            flash("Unable to parse the uploaded documents. Please use CSV or readable PDFs.", "danger")
            return redirect(url_for("core_business"))

        details = reconcile_uploads_from_data(invoice_rows, receipt_rows)

        notification_status = "none"
        if details["summary"]["total_discrepancies"] >= user["alert_threshold"]:
            notification_status = notify_user(user, details)
            if notification_status == "sent":
                flash(f"Alert sent via {user['notification_preference']}.", "info")
            elif notification_status == "failed":
                flash("Alert configuration is missing or failed.", "warning")

        with get_db() as conn:
            conn.execute(
                """
                INSERT INTO reconciliations (
                    user_id, created_at, title, invoice_name, receipt_name,
                    total_items, total_discrepancies, potential_loss, status, notification_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user["id"],
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                    f"Reconciliation detected {details['summary']['total_discrepancies']} discrepancies",
                    invoice_file.filename or "invoice.csv",
                    receipt_file.filename or "receipt.csv",
                    details["summary"]["total_items"],
                    details["summary"]["total_discrepancies"],
                    details["summary"]["potential_loss"],
                    "Needs review",
                    notification_status,
                ),
            )
            reconciliation_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for discrepancy in details["discrepancies"]:
                conn.execute(
                    """
                    INSERT INTO discrepancies (
                        reconciliation_id, item_name, invoice_qty, receipt_qty, delta, severity, reason, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        reconciliation_id,
                        discrepancy["item_name"],
                        discrepancy["invoice_qty"],
                        discrepancy["receipt_qty"],
                        discrepancy["delta"],
                        discrepancy["severity"],
                        discrepancy["reason"],
                        "open",
                    ),
                )

        flash("Reconciliation complete. Review the discrepancies below.", "success")

    with get_db() as conn:
        latest_case = conn.execute(
            "SELECT * FROM reconciliations ORDER BY id DESC LIMIT 1"
        ).fetchone()
    return render_template("core_business.html", user=user, details=details, latest_case=latest_case)


@app.route("/reports")
@login_required
def reports():
    user = get_current_user()
    with get_db() as conn:
        cases = conn.execute(
            "SELECT * FROM reconciliations ORDER BY created_at DESC"
        ).fetchall()
        discrepancies = conn.execute(
            "SELECT d.*, r.title FROM discrepancies d JOIN reconciliations r ON r.id = d.reconciliation_id ORDER BY r.created_at DESC"
        ).fetchall()
    return render_template("reports.html", user=user, cases=cases, discrepancies=discrepancies)


@app.route("/reports/export")
@login_required
def export_reports():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT r.title, r.created_at, r.total_discrepancies, r.potential_loss, r.status, d.item_name, d.invoice_qty, d.receipt_qty, d.delta, d.severity, d.reason, d.status as discrepancy_status FROM reconciliations r JOIN discrepancies d ON d.reconciliation_id = r.id ORDER BY r.created_at DESC"
        ).fetchall()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["case", "created_at", "item_name", "invoice_qty", "receipt_qty", "delta", "severity", "reason", "discrepancy_status"])
    for row in rows:
        writer.writerow([row["title"], row["created_at"], row["item_name"], row["invoice_qty"], row["receipt_qty"], row["delta"], row["severity"], row["reason"], row["discrepancy_status"]])

    response = Response(output.getvalue(), mimetype="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=logishield_report.csv"
    return response


@app.route("/discrepancies/<int:discrepancy_id>/review", methods=["POST"])
@login_required
def review_discrepancy(discrepancy_id):
    status = request.form.get("status", "reviewed")
    with get_db() as conn:
        conn.execute("UPDATE discrepancies SET status = ? WHERE id = ?", (status, discrepancy_id))
    flash("Discrepancy marked for follow-up.", "success")
    return redirect(url_for("reports"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = get_current_user()
    if request.method == "POST":
        threshold = int(request.form.get("alert_threshold", 2))
        preference = request.form.get("notification_preference", "email")
        with get_db() as conn:
            conn.execute(
                "UPDATE users SET alert_threshold = ?, notification_preference = ? WHERE id = ?",
                (threshold, preference, user["id"]),
            )
        flash("Preferences updated.", "success")
        return redirect(url_for("settings"))
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    slack_enabled = bool(os.environ.get("SLACK_WEBHOOK_URL"))
    email_enabled = bool(os.environ.get("SMTP_SERVER") and os.environ.get("EMAIL_SENDER"))
    return render_template(
        "settings.html",
        user=user,
        slack_enabled=slack_enabled,
        email_enabled=email_enabled,
    )


with app.app_context():
    init_db()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
