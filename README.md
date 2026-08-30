# E-Commerce Sales Data Pipeline

An automated ETL (Extract → Transform → Load) pipeline that pulls daily order
data, cleans and validates it, loads it into a relational database, and
powers a KPI dashboard — refreshed automatically on a schedule.

## Problem
Manually pulling, cleaning, and re-analyzing sales data every day doesn't
scale. This project automates that entire cycle, so KPIs stay current
without anyone re-running scripts by hand.

## Architecture

```
[Orders API] --> extract.py --> data/raw_orders_*.json
                                        |
                                        v
                                  transform.py  (clean, validate, dedupe)
                                        |
                                        v
                             data/processed_orders.csv
                                        |
                                        v
                                    load.py
                                        |
                                        v
                              data/pipeline.db (SQLite)
                            ├── orders  (fact table)
                            └── daily_sales_summary  (aggregate table)
                                        |
                                        v
                          dashboard/build_charts.py  -->  KPI Dashboard
```

Automated daily via **GitHub Actions** (`.github/workflows/daily_pipeline.yml`)
— no manual intervention required after setup.

## What each stage does

| Stage | Script | What it does |
|---|---|---|
| Extract | `scripts/extract.py` | Pulls daily order data from the source API |
| Transform | `scripts/transform.py` | Deduplicates, fills known-safe missing values, validates quantity/price, computes gross/net revenue |
| Load | `scripts/load.py` | Loads clean data into SQLite: a fact table (`orders`) and a pre-aggregated reporting table (`daily_sales_summary`) |
| Visualize | `dashboard/build_charts.py` | Builds the KPI dashboard directly from the database |
| Automate | `.github/workflows/daily_pipeline.yml` | Runs the full pipeline daily and commits the refreshed data back to the repo |

## Data cleaning decisions (documented, not hidden)
- Duplicate `order_id` rows are dropped (can occur on API retries)
- Missing `region` is labeled `"Unknown"` — never silently dropped or guessed
- Missing `discount_pct` is treated as `0` (no discount recorded)
- Rows with invalid `quantity <= 0` or `unit_price <= 0` are dropped and logged

## Results (from the 91-day sample run)
- 7,145 orders processed with zero remaining nulls after cleaning
- ₹13.4M total net revenue tracked across 5 categories and 5 regions
- Dashboard refresh time: full pipeline runs in under 5 seconds locally

## Tech stack
Python (pandas, matplotlib), SQLite, GitHub Actions, Power BI (for the
interactive version of the dashboard — connect Power BI Desktop directly to
`data/pipeline.db`)

## Running it yourself
```bash
pip install -r requirements.txt
python scripts/extract.py
python scripts/transform.py
python scripts/load.py
python dashboard/build_charts.py
```

To point this at a **real live API** instead of the bundled sample data
generator, edit `fetch_from_api()` in `scripts/extract.py` — the function
is documented inline with the exact `requests.get(...)` call to swap in.
No other script needs to change, since the rest of the pipeline only
depends on the JSON shape returned.

## Next steps
- Swap SQLite for Postgres (Supabase/Neon free tier) for a cloud-hosted version
- Add data-quality alerts (e.g. Slack notification if a daily extract has 0 rows)
