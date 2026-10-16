import os
import io
import secrets
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, session, flash, make_response
import pandas as pd
from utils.data_processor import (
    load_uploaded_file, load_demo_data, normalize_columns, dataset_summary,
    get_kpis, get_chart_data, get_transactions, clean_export
)
from utils.analytics import generate_insights, build_business_summary
from utils.copilot import answer_question

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls"}

# Beginner-friendly in-memory dataset storage. Data resets when the server restarts.
# For multi-user production use, replace this with per-user persistent storage.
DATASETS = {}
DEFAULT_SETTINGS = {"business_name": "My Business", "currency": "INR", "appearance": "light"}

def current_df():
    key = session.get("dataset_key")
    return DATASETS.get(key) if key else None

def save_df(df, name):
    key = secrets.token_urlsafe(12)
    DATASETS[key] = df.copy()
    session["dataset_key"] = key
    session["dataset_name"] = name
    return key

def get_settings():
    return session.get("settings", DEFAULT_SETTINGS.copy())

def currency_symbol():
    return {"INR": "₹", "USD": "$", "EUR": "€", "GBP": "£"}.get(get_settings().get("currency", "INR"), "₹")

@app.context_processor
def inject_globals():
    return {"business_settings": get_settings(), "currency_symbol": currency_symbol()}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/dashboard")
def dashboard():
    df = current_df()
    return render_template("dashboard.html", has_data=df is not None, dataset_name=session.get("dataset_name", "No dataset loaded"))

@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        file = request.files.get("file")
        if not file or not file.filename:
            flash("Choose a CSV or Excel file first.", "error")
            return redirect(url_for("upload"))
        extension = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
        if extension not in ALLOWED_EXTENSIONS:
            flash("Unsupported file type. Please upload CSV, XLS, or XLSX.", "error")
            return redirect(url_for("upload"))
        try:
            df = load_uploaded_file(file, extension)
            save_df(df, file.filename.rsplit("/", 1)[-1].rsplit("\\", 1)[-1])
            flash(f"Dataset loaded successfully: {len(df):,} rows.", "success")
            return redirect(url_for("dashboard"))
        except Exception as exc:
            flash(str(exc), "error")
            return redirect(url_for("upload"))
    df = current_df()
    preview = df.head(8).fillna("").to_dict(orient="records") if df is not None else []
    columns = list(df.columns) if df is not None else []
    return render_template("upload.html", preview=preview, columns=columns, row_count=len(df) if df is not None else 0, dataset_name=session.get("dataset_name", ""))

@app.route("/demo")
def demo():
    df = load_demo_data()
    save_df(df, "sample_sales.csv (fictional demo)")
    flash("Fictional demo data loaded. These records are not real business results.", "success")
    return redirect(url_for("dashboard"))

@app.route("/api/dashboard")
def api_dashboard():
    df = current_df()
    if df is None:
        return jsonify({"ok": False, "message": "Upload a dataset or load demo data to see analytics."}), 400
    return jsonify({
        "ok": True,
        "dataset_name": session.get("dataset_name", "Dataset"),
        "summary": dataset_summary(df),
        "kpis": get_kpis(df),
        "charts": get_chart_data(df),
        "transactions": get_transactions(df),
        "insights": generate_insights(df),
        "currency": currency_symbol()
    })

@app.route("/api/copilot", methods=["POST"])
def copilot_api():
    df = current_df()
    if df is None:
        return jsonify({"answer": "Please upload a dataset or load demo data first.", "supported": False}), 400
    payload = request.get_json(silent=True) or {}
    question = str(payload.get("question", "")).strip()[:500]
    if not question:
        return jsonify({"answer": "Type a question about your business data first.", "supported": False}), 400
    return jsonify(answer_question(df, question, currency_symbol()))

@app.route("/analytics")
def analytics():
    return render_template("analytics.html")

@app.route("/copilot")
def copilot():
    return render_template("copilot.html")

@app.route("/reports")
def reports():
    return render_template("reports.html")

@app.route("/settings", methods=["GET", "POST"])
def settings():
    current = get_settings()
    if request.method == "POST":
        current["business_name"] = request.form.get("business_name", "My Business").strip()[:80] or "My Business"
        currency = request.form.get("currency", "INR")
        current["currency"] = currency if currency in {"INR", "USD", "EUR", "GBP"} else "INR"
        current["appearance"] = request.form.get("appearance", "light")
        session["settings"] = current
        flash("Settings saved.", "success")
        return redirect(url_for("settings"))
    return render_template("settings.html", settings=current)

@app.route("/download/sample.csv")
def sample_csv():
    df = load_demo_data()
    return send_file(io.BytesIO(df.to_csv(index=False).encode("utf-8")), mimetype="text/csv", as_attachment=True, download_name="insightiq_sample_sales.csv")

@app.route("/download/cleaned.csv")
def cleaned_csv():
    df = current_df()
    if df is None:
        flash("Load a dataset before exporting.", "error")
        return redirect(url_for("upload"))
    data = clean_export(df).to_csv(index=False).encode("utf-8")
    return send_file(io.BytesIO(data), mimetype="text/csv", as_attachment=True, download_name="insightiq_cleaned_data.csv")

@app.route("/report/print")
def print_report():
    df = current_df()
    if df is None:
        flash("Load a dataset before generating a report.", "error")
        return redirect(url_for("upload"))
    return render_template("print_report.html", metrics=get_kpis(df), insights=generate_insights(df), summary=build_business_summary(df), dataset_name=session.get("dataset_name", "Dataset"), generated_at=datetime.now().strftime("%d %b %Y, %I:%M %p"))

@app.errorhandler(413)
def too_large(_error):
    flash("The file is larger than 10 MB. Please upload a smaller file.", "error")
    return redirect(url_for("upload"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_DEBUG") == "1")
