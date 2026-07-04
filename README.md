# LogiShield

LogiShield is a hackathon MVP for automated discrepancy and fraud detection in logistics and finance workflows.

## What it does
- User registration and login
- Reconciliation engine for invoice vs warehouse receipt CSV uploads
- Dashboard with summary metrics
- Reports and audit trail
- Settings for alert thresholds and notification preferences

## Run locally
1. Install Python 3.13+
2. Install dependencies:
   `pip install -r requirements.txt`
3. Start the app:
   `python app.py`
4. Open http://127.0.0.1:5000

## Features
- Upload CSV or PDF supplier invoices and warehouse receipts
- Automatic discrepancy detection with severity scoring
- Exportable CSV reports
- Reviewer workflow with discrepancy statuses
- Optional Slack and email alerts when risk thresholds are exceeded

## Demo credentials
- Email: demo@logishield.com
- Password: demo1234
