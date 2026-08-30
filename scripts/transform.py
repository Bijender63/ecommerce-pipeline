"""
transform.py
------------
Step 2 of the pipeline: TRANSFORM.

Reads every raw_orders_*.json file in data/, combines them, cleans and
validates the data, and produces one tidy DataFrame ready to load into
the database.

Cleaning rules applied (documented so this is auditable, not a black box):
  1. Drop exact duplicate order_id rows (can happen with API retries).
  2. Fill missing `region` with "Unknown" (never silently drop real orders).
  3. Fill missing `discount_pct` with 0 (no discount recorded = none applied).
  4. Compute `gross_amount` = unit_price * quantity.
  5. Compute `net_amount`   = gross_amount * (1 - discount_pct/100).
  6. Parse order_timestamp into a proper datetime and derive `order_date`.
  7. Validate: quantity > 0 and unit_price > 0 (drop + log anything invalid).

Output: data/processed_orders.csv  (also returned as a DataFrame)
"""

import glob
import json
import os
import pandas as pd

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_raw() -> pd.DataFrame:
    rows = []
    for path in sorted(glob.glob(os.path.join(DATA_DIR, "raw_orders_*.json"))):
        with open(path) as f:
            payload = json.load(f)
        rows.extend(payload["orders"])
    df = pd.DataFrame(rows)
    print(f"Loaded {len(df)} raw order rows from {DATA_DIR}")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)

    # 1. Drop duplicate order_ids
    df = df.drop_duplicates(subset="order_id")

    # 2 & 3. Fill known-safe missing values
    df["region"] = df["region"].fillna("Unknown")
    df["discount_pct"] = df["discount_pct"].fillna(0)

    # 6. Parse timestamp
    df["order_timestamp"] = pd.to_datetime(df["order_timestamp"])
    df["order_date"] = df["order_timestamp"].dt.date

    # 7. Validate numeric sanity — drop and report anything invalid
    invalid_mask = (df["quantity"] <= 0) | (df["unit_price"] <= 0)
    if invalid_mask.any():
        print(f"Dropping {invalid_mask.sum()} rows with invalid quantity/price")
    df = df[~invalid_mask]

    # 4 & 5. Derived financial fields
    df["gross_amount"] = df["unit_price"] * df["quantity"]
    df["net_amount"] = (df["gross_amount"] * (1 - df["discount_pct"] / 100)).round(2)

    after = len(df)
    print(f"Cleaned dataset: {before} -> {after} rows ({before - after} removed)")

    cols = [
        "order_id", "order_date", "order_timestamp", "sku", "product_name",
        "category", "region", "unit_price", "quantity", "discount_pct",
        "gross_amount", "net_amount",
    ]
    return df[cols].reset_index(drop=True)


def run() -> pd.DataFrame:
    raw = load_raw()
    clean_df = clean(raw)
    out_path = os.path.join(DATA_DIR, "processed_orders.csv")
    clean_df.to_csv(out_path, index=False)
    print(f"Saved processed data to {out_path}")
    return clean_df


if __name__ == "__main__":
    run()
