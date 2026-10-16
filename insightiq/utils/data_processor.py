import io
import pandas as pd
import numpy as np

COLUMN_ALIASES = {
    "date": ["date", "order_date", "transaction_date", "created_at", "sale_date"],
    "product": ["product", "product_name", "item", "item_name", "sku"],
    "category": ["category", "product_category", "type"],
    "quantity": ["quantity", "qty", "units", "unit_sold", "units_sold"],
    "revenue": ["revenue", "sales", "total_sales", "amount", "sales_amount", "total_revenue"],
    "expenses": ["expenses", "expense", "cost", "total_cost", "costs", "total_expenses"],
    "profit": ["profit", "net_profit", "gross_profit", "earnings"],
    "order_id": ["order_id", "order", "invoice_id", "transaction_id"]
}

def _canonicalize_columns(df):
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_").replace("-", "_") for c in df.columns]
    rename = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        for col in df.columns:
            if col == canonical or col in aliases:
                rename[col] = canonical
                break
    return df.rename(columns=rename)

def normalize_columns(df):
    df = _canonicalize_columns(df)
    for col in ["quantity", "revenue", "expenses", "profit"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "", regex=False).str.replace("₹", "", regex=False).str.replace("$", "", regex=False).str.strip(), errors="coerce")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce", dayfirst=True)
    if "revenue" in df.columns and "expenses" in df.columns and "profit" not in df.columns:
        df["profit"] = df["revenue"] - df["expenses"]
    return df

def load_uploaded_file(file, extension):
    raw = file.read()
    if not raw:
        raise ValueError("The uploaded file is empty.")
    try:
        if extension == "csv":
            try:
                df = pd.read_csv(io.BytesIO(raw))
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(raw), encoding="latin-1")
        else:
            df = pd.read_excel(io.BytesIO(raw), engine="openpyxl" if extension == "xlsx" else None)
    except Exception:
        raise ValueError("We couldn't read this file. Check that it is a valid CSV or Excel spreadsheet.")
    if df.empty:
        raise ValueError("This dataset has no rows. Add data and upload again.")
    if len(df.columns) > 100:
        raise ValueError("This dataset has too many columns (maximum 100).")
    if len(df) > 100000:
        raise ValueError("This dataset has too many rows (maximum 100,000).")
    df = normalize_columns(df)
    # Avoid processing datasets with no usable column names.
    if not len(df.columns):
        raise ValueError("No usable columns were found in the file.")
    return df

def load_demo_data():
    rows = []
    products = [
        ("Notebook", "Stationery", 80), ("Wireless Mouse", "Electronics", 650),
        ("Water Bottle", "Lifestyle", 250), ("Desk Lamp", "Home", 520),
        ("Pen Set", "Stationery", 120), ("USB Hub", "Electronics", 480)
    ]
    for month in range(1, 13):
        for day in [3, 8, 14, 19, 25, 28]:
            for j, (product, category, price) in enumerate(products):
                qty = 1 + ((month * 3 + day + j) % 8)
                revenue = qty * price
                expenses = round(revenue * (0.48 + ((month + j) % 5) * 0.035), 2)
                rows.append({
                    "order_date": f"2025-{month:02d}-{day:02d}",
                    "order_id": f"DEMO-{month:02d}-{day:02d}-{j+1}",
                    "product_name": product, "category": category, "quantity": qty,
                    "revenue": revenue, "expenses": expenses, "profit": round(revenue-expenses, 2)
                })
    return normalize_columns(pd.DataFrame(rows))

def dataset_summary(df):
    return {"rows": int(len(df)), "columns": int(len(df.columns)), "column_names": [str(c) for c in df.columns],
            "missing_cells": int(df.isna().sum().sum())}

def _safe_sum(df, col):
    if col not in df.columns:
        return None
    return round(float(pd.to_numeric(df[col], errors="coerce").fillna(0).sum()), 2)

def get_kpis(df):
    revenue = _safe_sum(df, "revenue")
    expenses = _safe_sum(df, "expenses")
    profit = _safe_sum(df, "profit")
    orders = int(df["order_id"].nunique()) if "order_id" in df.columns else int(len(df))
    return {
        "revenue": revenue, "expenses": expenses, "profit": profit, "orders": orders,
        "average_order_value": round(revenue / orders, 2) if revenue is not None and orders else None,
        "available": {"revenue": "revenue" in df.columns, "expenses": "expenses" in df.columns,
                      "profit": "profit" in df.columns, "orders": True}
    }

def get_chart_data(df):
    result = {"monthly": {"labels": [], "values": []}, "products": {"labels": [], "values": []},
              "categories": {"labels": [], "values": []}, "expenses_profit": {"labels": [], "expenses": [], "profit": []}}
    if "date" in df.columns and "revenue" in df.columns:
        temp = df.dropna(subset=["date"]).copy()
        if not temp.empty:
            temp["month"] = temp["date"].dt.to_period("M").astype(str)
            grouped = temp.groupby("month")["revenue"].sum().sort_index()
            result["monthly"] = {"labels": grouped.index.tolist(), "values": [round(float(x), 2) for x in grouped.values]}
    if "product" in df.columns and "revenue" in df.columns:
        grouped = df.groupby("product")["revenue"].sum().sort_values(ascending=False).head(8)
        result["products"] = {"labels": [str(x) for x in grouped.index], "values": [round(float(x), 2) for x in grouped.values]}
    if "category" in df.columns and "revenue" in df.columns:
        grouped = df.groupby("category")["revenue"].sum().sort_values(ascending=False).head(8)
        result["categories"] = {"labels": [str(x) for x in grouped.index], "values": [round(float(x), 2) for x in grouped.values]}
    if "expenses" in df.columns or "profit" in df.columns:
        labels, expenses, profit = [], [], []
        for col in ["expenses", "profit"]:
            if col in df.columns:
                labels.append(col.title())
        if "expenses" in df.columns:
            expenses = [round(float(df["expenses"].fillna(0).sum()), 2)]
        if "profit" in df.columns:
            profit = [round(float(df["profit"].fillna(0).sum()), 2)]
        result["expenses_profit"] = {"labels": labels, "expenses": expenses, "profit": profit}
    return result

def get_transactions(df):
    columns = [c for c in ["date", "product", "category", "quantity", "revenue", "expenses", "profit"] if c in df.columns]
    if not columns:
        columns = list(df.columns[:7])
    out = df[columns].tail(8).copy()
    if "date" in out.columns:
        out["date"] = out["date"].astype(str).replace("NaT", "")
    return out.fillna("").to_dict(orient="records")

def clean_export(df):
    return df.copy()
