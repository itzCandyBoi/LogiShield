# LogiShield — 5-Slide Pitch Deck & Demo Script

This file contains a compact 5-slide deck and exact demo script you can submit now with the prototype link.

---

## Slide 1 — Problem & Impact
- Headline: Manual invoice ↔ warehouse receipt reconciliation is slow, error-prone, and exposes SMEs to payment and fraud risk.
- Quick stat: Manual reconciliation can take hours per invoice cycle for SMBs; missed discrepancies cause cashflow and supplier disputes.
- One-line value prop: LogiShield automates reconciliation, surfaces high-risk discrepancies, and provides concise investigator notes so teams act faster.

Talking points (30–45s): describe the business pain and why it matters to SMEs.

---

## Slide 2 — Solution Overview
- Product: Lightweight web app that ingests CSV/PDF invoices and receipts, reconciles line-items, scores risk, and provides reviewer workflow + exportable reports.
- Core capabilities: CSV/PDF ingest, fuzzy line matching, risk scoring, LLM-generated investigator note, reviewer accept/reject, export audit trail.
- Screenshot / link: include your live prototype link (or GitHub repo link).

Talking points (45–60s): short demo flow summary (upload → reconcile → review → export).

---

## Slide 3 — AI & Novelty
- AI uses: OCR/NLP for PDFs, embedding-based fuzzy matching for noisy descriptions, anomaly detection for numeric outliers, LLM summarization for explainable notes.
- Why novel: combines deterministic reconciliation with explainable AI that produces actionable remediation steps.

Talking points (45–60s): emphasize novelty and measurable automation benefits.

---

## Slide 4 — Live Demo (what judges should see)
- Demo script (exact):
  1. Login with demo account: `demo@logishield.com` / `demo1234` (or show repo if not deployed).
  2. Upload `sample_invoice.csv` and `sample_receipt.csv` (available in repo).
  3. Click Reconcile → observe discrepancies sorted by risk.
  4. Open top discrepancy → show summary note (LLM output) and suggested action.
  5. Mark as `reviewed` / export CSV report.
- Time: aim to complete in ~90s for judges to reproduce quickly.

Note: If you can't deploy live, record a 2–3 minute screencast doing the same steps and include the link in your submission.

---

## Slide 5 — Business Value & Next Steps
- One-liner: Faster reconciliations, fewer missed frauds, improved cashflow for SMBs.
- Go-to-market: plugin for accounting software, pay-per-seat subscription for SMEs, onboarding package.
- Ask / closing: Request feedback, pilot partners, and judge attention for final round demonstration.

---

## Submission checklist (what to include now)
- Prototype link (live URL) OR GitHub repo link: https://github.com/itzCandyBoi/LogiShield
- Attach `PRESENTATION.md` or `slides.pdf` (this file is acceptable as the slide content).
- Short instructions: run `python app.py` and open `http://127.0.0.1:5000` (demo credentials above) if judges run locally.

---

## Optional next steps I can do for you
- Generate a 5-slide PDF for direct upload.
- Deploy prototype to Render and return a live URL.
- Record a 2–3 minute demo video and upload it to GitHub Releases.

Tell me which of these you'd like me to do next.
