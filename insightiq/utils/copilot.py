import pandas as pd
from .data_processor import get_kpis
from .analytics import money

def answer_question(df, question, symbol="₹"):
    q = question.lower().strip()
    k = get_kpis(df)
    if any(x in q for x in ["total sales", "total revenue", "revenue", "sales"]):
        if k["revenue"] is None:
            return {"answer": "I couldn't find a revenue or sales column. Try a column named revenue, sales, total_sales, or amount.", "supported": False}
        if any(x in q for x in ["which product", "top product", "best product", "highest product"]):
            if "product" not in df.columns:
                return {"answer": "I can calculate total revenue, but I couldn't identify a product column in this dataset.", "supported": False}
            grouped = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
            return {"answer": f"{grouped.index[0]} generated the highest revenue: {money(float(grouped.iloc[0]), symbol)}.", "supported": True}
        if any(x in q for x in ["which month", "highest month", "best month"]):
            if "date" not in df.columns:
                return {"answer": f"Total revenue is {money(k['revenue'], symbol)}, but I couldn't identify a date column for monthly comparison.", "supported": False}
            temp = df.dropna(subset=["date"]).copy()
            if temp.empty:
                return {"answer": "The date column doesn't contain usable dates, so I can't compare months.", "supported": False}
            temp["month"] = temp["date"].dt.to_period("M").astype(str)
            grouped = temp.groupby("month")["revenue"].sum().sort_values(ascending=False)
            return {"answer": f"{grouped.index[0]} had the highest recorded revenue: {money(float(grouped.iloc[0]), symbol)}.", "supported": True}
        return {"answer": f"Total recorded revenue is {money(k['revenue'], symbol)}.", "supported": True}
    if "expense" in q or "cost" in q:
        return {"answer": f"Total recorded expenses are {money(k['expenses'], symbol)}." if k["expenses"] is not None else "I couldn't find an expenses or cost column.", "supported": k["expenses"] is not None}
    if "profit" in q or "earn" in q:
        return {"answer": f"Total recorded profit is {money(k['profit'], symbol)}." if k["profit"] is not None else "I couldn't find a profit column. If both revenue and expenses exist, the app can calculate profit.", "supported": k["profit"] is not None}
    if "order" in q or "average order" in q or "aov" in q:
        if "average" in q or "aov" in q:
            return {"answer": f"Average order value is {money(k['average_order_value'], symbol)}." if k["average_order_value"] is not None else "Average order value isn't available because revenue is missing.", "supported": k["average_order_value"] is not None}
        return {"answer": f"There are {k['orders']:,} recorded orders/rows. If no order ID column exists, rows are used as the count.", "supported": True}
    if any(x in q for x in ["category", "categories"]):
        if "category" not in df.columns or "revenue" not in df.columns:
            return {"answer": "I need both category and revenue columns to compare category performance.", "supported": False}
        grouped = df.groupby("category")["revenue"].sum().sort_values(ascending=False)
        return {"answer": f"{grouped.index[0]} is the top category by revenue with {money(float(grouped.iloc[0]), symbol)}.", "supported": True}
    if any(x in q for x in ["summar", "business performance", "how is my business"]):
        parts = []
        if k["revenue"] is not None: parts.append(f"revenue is {money(k['revenue'], symbol)}")
        if k["expenses"] is not None: parts.append(f"expenses are {money(k['expenses'], symbol)}")
        if k["profit"] is not None: parts.append(f"profit is {money(k['profit'], symbol)}")
        if "product" in df.columns and "revenue" in df.columns:
            p = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
            if not p.empty: parts.append(f"{p.index[0]} is the top product by revenue")
        if not parts: return {"answer": "I couldn't calculate a summary from the available columns. Try adding revenue, expenses, profit, product, or date.", "supported": False}
        return {"answer": "Based on the loaded dataset, " + "; ".join(parts) + ". These are descriptive results, not predictions.", "supported": True}
    if any(x in q for x in ["suggest", "recommend", "improve", "three"]):
        suggestions = []
        if "product" in df.columns and "revenue" in df.columns:
            p = df.groupby("product")["revenue"].sum().sort_values()
            if not p.empty: suggestions.append(f"Review demand and inventory for {p.index[0]}, the lowest-revenue product in this dataset.")
            top = p.sort_values(ascending=False)
            if not top.empty: suggestions.append(f"Study what customers value about {top.index[0]}, the top-revenue product, before deciding whether to expand it.")
        if "date" in df.columns and "revenue" in df.columns:
            suggestions.append("Compare monthly revenue over several periods before making major pricing or staffing changes.")
        suggestions.append("Check that costs, refunds, and dates are recorded consistently so future reports are more reliable.")
        return {"answer": "Suggestions based on available data:\n• " + "\n• ".join(suggestions[:3]), "supported": True}
    return {"answer": "I can answer questions about total sales/revenue, expenses, profit, orders, average order value, top products, best month, categories, business summary, and basic suggestions. Try one of the suggested questions.", "supported": False}
