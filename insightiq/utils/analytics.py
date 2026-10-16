import pandas as pd
from .data_processor import get_kpis

def money(value, symbol="₹"):
    if value is None:
        return "Not available"
    return f"{symbol}{value:,.2f}"

def generate_insights(df):
    insights = []
    if "revenue" in df.columns and not df["revenue"].dropna().empty:
        total = float(df["revenue"].sum())
        insights.append({"title": "Revenue recorded", "detail": f"Total revenue in this dataset is {money(total)}.", "kind": "fact"})
        if "product" in df.columns:
            product_sales = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
            if not product_sales.empty:
                insights.append({"title": "Top product by revenue", "detail": f"{product_sales.index[0]} generated {money(float(product_sales.iloc[0]))} in revenue.", "kind": "fact"})
                if len(product_sales) > 1:
                    insights.append({"title": "Review lower-selling products", "detail": f"{product_sales.index[-1]} has the lowest recorded revenue among listed products. Consider reviewing demand and stock before changing inventory.", "kind": "suggestion"})
        if "date" in df.columns:
            dated = df.dropna(subset=["date"]).copy()
            if not dated.empty:
                dated["month"] = dated["date"].dt.to_period("M").astype(str)
                monthly = dated.groupby("month")["revenue"].sum().sort_values(ascending=False)
                if not monthly.empty:
                    insights.append({"title": "Strongest month", "detail": f"{monthly.index[0]} has the highest recorded revenue at {money(float(monthly.iloc[0]))}.", "kind": "fact"})
                    chronological = dated.groupby("month")["revenue"].sum().sort_index()
                    if len(chronological) >= 2:
                        previous, latest = float(chronological.iloc[-2]), float(chronological.iloc[-1])
                        if previous != 0:
                            change = (latest - previous) / abs(previous) * 100
                            insights.append({"title": "Latest monthly change", "detail": f"Revenue changed by {change:.1f}% from {chronological.index[-2]} to {chronological.index[-1]}. This is a comparison, not an explanation of why it changed.", "kind": "fact"})
    if "category" in df.columns and "profit" in df.columns:
        grouped = df.groupby("category")["profit"].sum().sort_values(ascending=False)
        if not grouped.empty:
            insights.append({"title": "Most profitable category", "detail": f"{grouped.index[0]} has the highest total recorded profit at {money(float(grouped.iloc[0]))}.", "kind": "fact"})
    if not insights:
        insights.append({"title": "Add more business columns", "detail": "Include columns such as revenue, date, product, category, expenses, or profit to unlock more insights.", "kind": "suggestion"})
    return insights[:6]

def build_business_summary(df):
    kpis = get_kpis(df)
    lines = [f"Rows analysed: {len(df):,}."]
    if kpis["revenue"] is not None: lines.append(f"Total revenue: {money(kpis['revenue'])}.")
    if kpis["expenses"] is not None: lines.append(f"Total expenses: {money(kpis['expenses'])}.")
    if kpis["profit"] is not None: lines.append(f"Total profit: {money(kpis['profit'])}.")
    lines.append("Metrics are calculated only from columns detected in the uploaded dataset.")
    return " ".join(lines)
