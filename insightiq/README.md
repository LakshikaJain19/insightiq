# InsightIQ — AI Business Intelligence Copilot for SMEs

A beginner-friendly Flask + Pandas web app that lets small businesses explore CSV/Excel data, view dashboard KPIs and charts, ask common questions in plain English, and export cleaned data.

## Features
- CSV and Excel (`.xlsx`, `.xls`) uploads with a 10 MB request limit
- Automatic recognition of common business column names
- Dashboard KPIs, interactive charts, transactions table, and data-driven insights
- Rule-based copilot that calculates answers from the active dataset (no paid API key required)
- Fictional demo data and sample CSV download
- CSV export and print-friendly report
- INR/USD/EUR/GBP display settings
- Render deployment configuration

## Run locally (Windows / VS Code)
1. Install Python 3.11 or 3.12.
2. Open this folder in VS Code.
3. Open Terminal and create a virtual environment:
   ```powershell
   python -m venv venv
   ```
4. Activate it:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt and run `venv\Scripts\activate.bat`.
5. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
6. Start the website:
   ```powershell
   python app.py
   ```
7. Open http://127.0.0.1:5000 in your browser.

## Deploy to Render
1. Push the complete project folder to a GitHub repository.
2. In Render, choose **New + → Blueprint** and connect the repository, or create a Web Service manually.
3. If creating a Web Service manually:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
   - Add environment variable `SECRET_KEY` with a long random value.
4. Deploy and open the generated Render URL.

`render.yaml` can configure the service as a Blueprint. Do not commit secrets or `.env` files.

## Data and limitations
- Demo records are fictional and clearly labelled.
- Uploads are held in server memory for the current session and are not permanently stored. They may disappear when the process restarts; this is expected on Render.
- This starter version is designed for a college project demo, not multi-user enterprise deployment. The in-memory dataset store is not durable or isolated enough for a public multi-user production service.
- The copilot uses deterministic Pandas functions and keyword matching, not a live LLM. It never executes user-provided code.
- Column mapping supports common English names; verify that your file's columns were detected correctly.
- Financial totals use the values in your file. Currency selection changes display symbols only; it does not convert currency.
- Excel `.xls` files may require additional compatibility dependencies depending on the workbook format. `.xlsx` is recommended.

## Suggested demo flow
1. Load Demo Data.
2. Show KPI cards and charts.
3. Ask the Copilot: “Which product generated the highest revenue?”
4. Upload your own CSV to show that results change dynamically.
5. Export cleaned CSV and open the print report.
