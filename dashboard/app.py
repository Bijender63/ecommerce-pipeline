"""
app.py
------
Interactive KPI dashboard for the E-Commerce Sales Pipeline.

Reads directly from data/pipeline.db (the same database the ETL pipeline
loads). Run locally with:

    streamlit run dashboard/app.py

Deploy for free (to get a shareable link for your resume/GitHub) via
Streamlit Community Cloud: https://streamlit.io/cloud
  1. Push this repo to GitHub (already done)
  2. Go to share.streamlit.io, sign in with GitHub
  3. "New app" -> select this repo -> main file path: dashboard/app.py
  4. Deploy -> you get a public URL like yourapp.streamlit.app
"""

import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "pipeline.db")

st.set_page_config(page_title="E-Commerce Sales Dashboard", layout="wide")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        "SELECT order_date, category, region, total_orders, total_units, "
        "gross_revenue, net_revenue FROM daily_sales_summary",
        conn, parse_dates=["order_date"],
    )
    conn.close()
    return df


df = load_data()

st.title("E-Commerce Sales Pipeline")
st.caption("Live data from an automated ETL pipeline (Python + SQLite + GitHub Actions)")

# ---------------- Sidebar filters ----------------
st.sidebar.header("Filters")

min_date, max_date = df["order_date"].min(), df["order_date"].max()
date_range = st.sidebar.date_input(
    "Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date,
)

categories = sorted(df["category"].unique())
selected_categories = st.sidebar.multiselect("Category", categories, default=categories)

regions = sorted(df["region"].unique())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

# Apply filters
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

mask = (
    (df["order_date"] >= pd.to_datetime(start_date))
    & (df["order_date"] <= pd.to_datetime(end_date))
    & (df["category"].isin(selected_categories))
    & (df["region"].isin(selected_regions))
)
filtered = df[mask]

# ---------------- KPI cards ----------------
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Net Revenue", f"₹{filtered['net_revenue'].sum():,.0f}")
col2.metric("Total Orders", f"{int(filtered['total_orders'].sum()):,}")
col3.metric("Total Units Sold", f"{int(filtered['total_units'].sum()):,}")
avg_order_value = (
    filtered["net_revenue"].sum() / filtered["total_orders"].sum()
    if filtered["total_orders"].sum() > 0 else 0
)
col4.metric("Avg Order Value", f"₹{avg_order_value:,.0f}")

st.divider()

# ---------------- Charts ----------------
left, right = st.columns(2)

with left:
    daily = filtered.groupby("order_date", as_index=False)["net_revenue"].sum()
    fig_trend = px.line(
        daily, x="order_date", y="net_revenue",
        title="Daily Net Revenue Trend", labels={"net_revenue": "Net Revenue (₹)", "order_date": "Date"},
    )
    fig_trend.update_traces(hovertemplate="%{x|%b %d, %Y}<br>₹%{y:,.0f}<extra></extra>")
    st.plotly_chart(fig_trend, use_container_width=True)

    by_region = filtered.groupby("region", as_index=False)["net_revenue"].sum().sort_values("net_revenue")
    fig_region = px.bar(
        by_region, x="net_revenue", y="region", orientation="h",
        title="Revenue by Region", labels={"net_revenue": "Net Revenue (₹)", "region": ""},
    )
    st.plotly_chart(fig_region, use_container_width=True)

with right:
    by_category = filtered.groupby("category", as_index=False)["net_revenue"].sum().sort_values("net_revenue", ascending=False)
    fig_cat = px.bar(
        by_category, x="category", y="net_revenue",
        title="Revenue by Category", labels={"net_revenue": "Net Revenue (₹)", "category": ""},
    )
    st.plotly_chart(fig_cat, use_container_width=True)

    daily_orders = filtered.groupby("order_date", as_index=False)["total_orders"].sum()
    fig_orders = px.line(
        daily_orders, x="order_date", y="total_orders",
        title="Daily Order Volume", labels={"total_orders": "Orders", "order_date": "Date"},
    )
    st.plotly_chart(fig_orders, use_container_width=True)

st.divider()

# ---------------- Category x Region heatmap ----------------
pivot = filtered.pivot_table(
    index="category", columns="region", values="net_revenue", aggfunc="sum", fill_value=0
)
fig_heat = px.imshow(
    pivot, text_auto=".2s", aspect="auto",
    title="Revenue Heatmap — Category vs Region",
    labels=dict(color="Net Revenue (₹)"),
)
st.plotly_chart(fig_heat, use_container_width=True)

# ---------------- Raw data (expandable) ----------------
with st.expander("View underlying summary data"):
    st.dataframe(filtered.sort_values("order_date", ascending=False), use_container_width=True)
