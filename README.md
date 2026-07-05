# LogiShield

LogiShield is a hackathon prototype for automating invoice-to-warehouse receipt reconciliation for small and medium-sized logistics and finance teams.

## What the prototype does
- Lets users register and log in
- Accepts invoice and warehouse receipt files
- Reconciles the uploaded data and highlights mismatches
- Scores discrepancies by risk level
- Provides a basic review workflow and exportable reports
- Supports optional notifications for higher-risk issues

## How to use it
### Option 1: Open the hosted version
If a live demo URL is available, open it in the browser and start using the system directly. This is the easiest way for judges and other reviewers.

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
- PRESENTATION.md — short judge-friendly pitch and demo outline
