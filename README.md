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

## Deploy (Render) — recommended for judges

We recommend deploying to Render so judges can open a live URL (your laptop can be off).

Quick setup (Render):
1. Create a Render account and connect your GitHub account.
2. In Render dashboard, click "New" → "Web Service" and select the `itzCandyBoi/LogiShield` repo.
3. For "Start Command", use:

   `python app.py`

4. (Optional) Add any environment variables in the Render UI (e.g. `SLACK_WEBHOOK`, `SMTP_*`, `OPENAI_API_KEY`).
5. Deploy — Render will build and host the app. Copy the live URL and include it in your submission.

Notes:
- Render runs the app on their servers — you do NOT need your laptop on.
- Free tiers may sleep after inactivity (cold start), but the app remains hosted.
- If you prefer IaC, a `render.yaml` and `Procfile` are included in the repo to speed up setup.

## If judges run locally (fallback)
Include these commands in the `README` or submission so judges can run the prototype locally:

```powershell
# activate venv
& .\.venv\Scripts\Activate.ps1

# install deps
python -m pip install -r requirements.txt

# run tests
python -m unittest discover -s tests -v

# start app
python app.py
# open http://127.0.0.1:5000
```

## Docker (optional reproducible run)
Add a Dockerfile and run with Docker if judges prefer containers. A simple example is:

```
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
```

Build & run:
```
docker build -t logishield .
docker run -p 5000:5000 logishield
```

## Submission checklist (what to include now)
- Live URL (Render) or GitHub repo link: https://github.com/itzCandyBoi/LogiShield
- `PRESENTATION.md` (slide content & demo script) — already added.
- Demo credentials: `demo@logishield.com` / `demo1234` (include in README). 
- Sample CSVs are in the repo (`sample_invoice.csv`, `sample_receipt.csv`).


## Features
- Upload CSV or PDF supplier invoices and warehouse receipts
- Automatic discrepancy detection with severity scoring
- Exportable CSV reports
- Reviewer workflow with discrepancy statuses
- Optional Slack and email alerts when risk thresholds are exceeded

## Demo credentials
- Email: demo@logishield.com
- Password: demo1234
