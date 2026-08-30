"""
extract.py
----------
Step 1 of the pipeline: EXTRACT.

In production, this script calls a real REST API (e.g. a store's sales API,
OpenWeather, Alpha Vantage, etc.) using `requests.get(...)`. To run this
pipeline against a REAL API on your own machine (with internet access),
replace the `fetch_from_api()` function below with an actual API call —
the rest of the pipeline (transform/load) does not need to change at all,
since it only cares about the JSON shape returned.

For demo/portfolio purposes (and because this build environment has no
internet access), fetch_from_api() generates data with the same structure
a real e-commerce orders API would return, so the rest of the pipeline is
100% real and functional.

Output: data/raw_orders_<date>.json
"""

import json
import random
import datetime
import os

RAW_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
PRODUCTS = [
    ("SKU-1001", "Wireless Mouse", "Electronics", 799),
    ("SKU-1002", "Bluetooth Speaker", "Electronics", 1999),
    ("SKU-1003", "Notebook Set", "Stationery", 249),
    ("SKU-1004", "Office Chair", "Furniture", 5499),
    ("SKU-1005", "LED Desk Lamp", "Furniture", 899),
    ("SKU-1006", "Yoga Mat", "Fitness", 599),
    ("SKU-1007", "Water Bottle", "Fitness", 349),
    ("SKU-1008", "Backpack", "Accessories", 1499),
    ("SKU-1009", "Phone Case", "Accessories", 299),
    ("SKU-1010", "USB-C Cable", "Electronics", 199),
]
REGIONS = ["North", "South", "East", "West", "Central"]


def fetch_from_api(target_date: datetime.date) -> list[dict]:
    """
    Simulates the JSON payload a real orders API would return for a given day.

    TO USE A REAL API INSTEAD:
        import requests
        resp = requests.get(
            "https://api.yourstore.com/v1/orders",
            params={"date": target_date.isoformat()},
            headers={"Authorization": f"Bearer {os.environ['API_KEY']}"}
        )
        resp.raise_for_status()
        return resp.json()["orders"]
    """
    random.seed(target_date.toordinal())  # deterministic per day, like real historical data
    num_orders = random.randint(40, 120)
    orders = []
    for i in range(num_orders):
        sku, name, category, price = random.choice(PRODUCTS)
        qty = random.choices([1, 2, 3, 4], weights=[60, 25, 10, 5])[0]
        # occasional data-quality issues on purpose, so transform.py has real cleaning to do
        discount_pct = random.choice([0, 0, 0, 5, 10, 15, None])
        region = random.choice(REGIONS + [None])  # None simulates missing region field
        orders.append({
            "order_id": f"ORD-{target_date.strftime('%Y%m%d')}-{i:04d}",
            "order_timestamp": datetime.datetime.combine(
                target_date, datetime.time(random.randint(0, 23), random.randint(0, 59))
            ).isoformat(),
            "sku": sku,
            "product_name": name,
            "category": category,
            "unit_price": price,
            "quantity": qty,
            "discount_pct": discount_pct,
            "region": region,
        })
    return orders


def run(days_back: int = 90):
    os.makedirs(RAW_DATA_DIR, exist_ok=True)
    today = datetime.date.today()
    all_files = []
    for d in range(days_back, -1, -1):
        target_date = today - datetime.timedelta(days=d)
        orders = fetch_from_api(target_date)
        out_path = os.path.join(RAW_DATA_DIR, f"raw_orders_{target_date.isoformat()}.json")
        with open(out_path, "w") as f:
            json.dump({"date": target_date.isoformat(), "orders": orders}, f, indent=2)
        all_files.append(out_path)
    print(f"Extracted {len(all_files)} daily files into {RAW_DATA_DIR}")
    return all_files


if __name__ == "__main__":
    run()
