"""
load.py
-------
Step 3 of the pipeline: LOAD.

Loads the cleaned processed_orders.csv into a real relational database
(SQLite here for a zero-setup, fully portable portfolio project — the
same script works against Postgres by just swapping the connection
string, since we use SQLAlchemy).

Also builds a small `daily_sales_summary` table (an aggregate/reporting
table) — this is exactly the kind of "analytics-ready" table a BI tool
like Power BI would connect to directly, rather than hitting raw
transactional data every time.
"""

import os
import sqlite3
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DB_PATH = os.path.join(DATA_DIR, "pipeline.db")

# NOTE: uses Python's built-in sqlite3 module directly (pandas.to_sql accepts
# a raw sqlite3.Connection, not only a SQLAlchemy engine). To point this at
# Postgres/MySQL in production, install SQLAlchemy + the relevant driver and
# swap `conn` for `create_engine("postgresql://...")` — no other code changes
# needed, since to_sql()'s interface is the same either way.


def run():
    df = pd.read_csv(os.path.join(DATA_DIR, "processed_orders.csv"), parse_dates=["order_date", "order_timestamp"])

    conn = sqlite3.connect(DB_PATH)

    # 1. Load the clean, order-level fact table
    df.to_sql("orders", conn, if_exists="replace", index=False)

    # 2. Build and load a daily aggregate summary table (what a dashboard actually queries)
    summary = (
        df.groupby(["order_date", "category", "region"])
        .agg(
            total_orders=("order_id", "count"),
            total_units=("quantity", "sum"),
            gross_revenue=("gross_amount", "sum"),
            net_revenue=("net_amount", "sum"),
        )
        .reset_index()
    )
    summary.to_sql("daily_sales_summary", conn, if_exists="replace", index=False)

    n_orders = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    n_summary = conn.execute("SELECT COUNT(*) FROM daily_sales_summary").fetchone()[0]
    conn.close()

    print(f"Loaded {n_orders} rows into 'orders' table")
    print(f"Loaded {n_summary} rows into 'daily_sales_summary' table")
    print(f"Database ready at: {DB_PATH}")


if __name__ == "__main__":
    run()
