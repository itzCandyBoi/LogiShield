# LogiShield

LogiShield is a prototype web application designed to help logistics and finance teams automate the reconciliation of supplier invoices against warehouse receipts. The system allows users to upload invoice and receipt data, detect mismatches such as quantity differences, price discrepancies, or missing entries, and highlight these issues through a risk-based review workflow. It is built to reduce manual effort, improve accuracy, and give users a faster way to identify suspicious or high-risk transactions.

The prototype focuses on the core workflow of ingesting data, reconciling it, flagging discrepancies, and presenting results in a simple dashboard. It also includes basic reporting features so users can review issues and export records for further follow-up. While it is still a prototype, it demonstrates how AI-assisted reconciliation and anomaly detection could help small and medium-sized businesses save time and reduce fraud risk.

## What the prototype does
- Lets users register and log in
- Accepts invoice and warehouse receipt files
- Reconciles the uploaded data and highlights mismatches
- Scores discrepancies by risk level
- Provides a basic review workflow and exportable reports
- Supports optional notifications for higher-risk issues

## How to use it
### Option 1: Open the hosted version
https://logishield.onrender.com/register

### Option 2: Run it locally
If you want to run the prototype on your own machine, follow these steps:

1. Install Python 3.13+
2. Open the project folder
3. Create and activate a virtual environment (recommended)
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Start the app:
   ```bash
   python app.py
   ```
6. Open the app in your browser at:
   ```text
   http://127.0.0.1:5000
   ```

## Demo credentials
- Email: demo@logishield.com
- Password: demo1234

## Sample data
The repository already includes sample files for demo purposes:
- sample_invoice.csv
- sample_receipt.csv

## Notes for reviewers
- The deployed version on Render is only for convenience. Judges do not need to use Render themselves.
- They can simply open the provided live URL, or run the prototype locally using the instructions above.
- This is a prototype, so it is designed to demonstrate the core workflow clearly rather than replace a full production system.

## Repository contents
- app.py — main Flask application
- templates/ — UI pages
- static/ — CSS and static assets
- tests/ — basic unit tests
