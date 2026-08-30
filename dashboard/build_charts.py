"""
build_charts.py
----------------
Reads directly from the pipeline's SQLite database (data/pipeline.db) and
produces the KPI visuals a Power BI dashboard would show. This proves the
loaded data is genuinely analysis-ready, not just "stored."

In the real portfolio version, you'd instead open Power BI Desktop,
connect to data/pipeline.db (via an ODBC/SQLite connector) and build these
same visuals interactively — that's the version you'd screenshot and link
in your resume. This script is the quick, code-based proof that the data
supports it.
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DATA_DIR, "pipeline.db")
OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "dashboard")


def run():
    conn = sqlite3.connect(DB_PATH)
    daily = pd.read_sql(
        "SELECT order_date, SUM(net_revenue) as revenue, SUM(total_orders) as orders "
        "FROM daily_sales_summary GROUP BY order_date ORDER BY order_date",
        conn, parse_dates=["order_date"],
    )
    by_category = pd.read_sql(
        "SELECT category, SUM(net_revenue) as revenue FROM daily_sales_summary "
        "GROUP BY category ORDER BY revenue DESC", conn,
    )
    by_region = pd.read_sql(
        "SELECT region, SUM(net_revenue) as revenue FROM daily_sales_summary "
        "GROUP BY region ORDER BY revenue DESC", conn,
    )
    conn.close()

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("E-Commerce Sales Pipeline — KPI Dashboard", fontsize=15, fontweight="bold")

    # 1. Daily revenue trend
    axes[0, 0].plot(daily["order_date"], daily["revenue"], color="#1F3864", linewidth=1.5)
    axes[0, 0].set_title("Daily Net Revenue (last 91 days)")
    axes[0, 0].tick_params(axis="x", rotation=45)
    axes[0, 0].set_ylabel("₹ Net Revenue")

    # 2. Revenue by category
    axes[0, 1].barh(by_category["category"], by_category["revenue"], color="#2E6F95")
    axes[0, 1].set_title("Revenue by Category")
    axes[0, 1].invert_yaxis()

    # 3. Revenue by region
    axes[1, 0].bar(by_region["region"], by_region["revenue"], color="#4C8C60")
    axes[1, 0].set_title("Revenue by Region")

    # 4. Daily order volume trend
    axes[1, 1].plot(daily["order_date"], daily["orders"], color="#B5651D", linewidth=1.5)
    axes[1, 1].set_title("Daily Order Volume")
    axes[1, 1].tick_params(axis="x", rotation=45)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out_path = os.path.join(OUT_DIR, "kpi_dashboard.png")
    plt.savefig(out_path, dpi=150)
    print(f"Saved dashboard to {out_path}")

    print("\nKey numbers:")
    print(f"  Total net revenue (91 days): ₹{daily['revenue'].sum():,.0f}")
    print(f"  Total orders: {int(daily['orders'].sum()):,}")
    print(f"  Top category: {by_category.iloc[0]['category']} (₹{by_category.iloc[0]['revenue']:,.0f})")


if __name__ == "__main__":
    run()
