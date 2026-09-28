"""
Creates SYNTHETIC raw data for a small grocery business (2024-2025):
products, customers, sales lines and monthly inventory snapshots.
The sales file is intentionally messy (duplicates, blanks, inconsistent text)
so the cleaning step has real work to do.
Replace data/raw/*.csv with your real data to reuse the pipeline.
"""
from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

# ---------------- products ----------------
catalog = {
    "Fruits & Vegetables": [("Tomato 1kg", 30), ("Onion 1kg", 35), ("Potato 1kg", 28), ("Banana 1 dozen", 55), ("Apple 1kg", 160), ("Carrot 500g", 32)],
    "Dairy": [("Milk 1L", 56), ("Curd 500g", 40), ("Butter 100g", 58), ("Paneer 200g", 90), ("Cheese Slice", 120)],
    "Bakery": [("Bread Loaf", 40), ("Bun Pack", 30), ("Cake Slice", 45), ("Biscuit Pack", 25)],
    "Beverages": [("Tea Powder 250g", 120), ("Coffee 200g", 210), ("Soft Drink 1L", 65), ("Fruit Juice 1L", 110)],
    "Snacks": [("Potato Chips", 20), ("Namkeen 200g", 50), ("Chocolate Bar", 40), ("Cookies", 35)],
    "Staples": [("Rice 5kg", 320), ("Wheat Flour 5kg", 240), ("Toor Dal 1kg", 150), ("Sunflower Oil 1L", 140), ("Sugar 1kg", 46)],
    "Household": [("Detergent 1kg", 130), ("Dish Wash Liquid", 95), ("Toilet Cleaner", 85)],
}
products = []
pid = 100
for cat, items in catalog.items():
    for name, price in items:
        pid += 1
        cost = round(price * rng.uniform(0.70, 0.88), 2)
        products.append({"product_id": pid, "product_name": name, "category": cat, "unit_price": price,
                         "unit_cost": cost, "reorder_level": int(rng.integers(20, 60))})
products = pd.DataFrame(products)

# messy category text (fixed in cleaning step)
messy = products.copy()
messy["category"] = messy["category"].map(lambda c: rng.choice([c, c.upper(), c.lower(), f" {c} "], p=[0.7, 0.1, 0.1, 0.1]))
messy.to_csv(RAW / "products_raw.csv", index=False)

# ---------------- customers ----------------
n_cust = 250
customers = pd.DataFrame({
    "customer_id": np.arange(5001, 5001 + n_cust),
    "customer_name": [f"Customer {i}" for i in range(1, n_cust + 1)],
    "area": rng.choice(["North Street", "South Street", "Market Road", "Temple Road", "Bus Stand"], n_cust),
    "membership": rng.choice(["Regular", "Loyalty", "Occasional"], n_cust, p=[0.5, 0.25, 0.25]),
    "joined_date": pd.to_datetime("2022-01-01") + pd.to_timedelta(rng.integers(0, 900, n_cust), unit="D"),
})
customers.to_csv(RAW / "customers_raw.csv", index=False)

# ---------------- sales ----------------
dates = pd.date_range("2024-01-01", "2025-12-31")
rows, order_id = [], 20000
cat_weight = {"Fruits & Vegetables": 1.4, "Dairy": 1.5, "Bakery": 1.0, "Beverages": 0.8, "Snacks": 1.0, "Staples": 0.7, "Household": 0.4}
weights = products["category"].map(cat_weight).to_numpy()
weights = weights / weights.sum()
for d in dates:
    base = 22 + (8 if d.dayofweek >= 5 else 0)                       # weekend boost
    base *= 1 + 0.12 * np.sin((d.month - 1) / 12 * 2 * np.pi)         # mild seasonality
    base *= 1 + 0.18 * (d.year - 2024)                                # growth in 2025
    if d.month in (10, 11, 1):                                        # festival / Pongal months
        base *= 1.25
    for _ in range(rng.poisson(base)):
        order_id += 1
        cust = int(rng.choice(customers["customer_id"])) if rng.random() > 0.15 else None   # 15% walk-in
        pay = rng.choice(["Cash", "UPI", "Card"], p=[0.45, 0.45, 0.10])
        disc = float(rng.choice([0, 0, 0, 5, 10]))
        for pi in rng.choice(len(products), size=rng.integers(1, 5), replace=False, p=weights):
            p = products.iloc[pi]
            rows.append({"order_id": order_id, "order_date": d.strftime("%Y-%m-%d"), "customer_id": cust,
                         "product_id": p.product_id, "quantity": int(rng.integers(1, 5)),
                         "unit_price": p.unit_price, "discount_pct": disc, "payment_mode": pay})
sales = pd.DataFrame(rows)

# add dirt
dup = sales.sample(frac=0.01, random_state=1)
sales = pd.concat([sales, dup], ignore_index=True)
sales.loc[sales.sample(frac=0.02, random_state=2).index, "payment_mode"] = None
sales["payment_mode"] = sales["payment_mode"].map(lambda v: v if not isinstance(v, str) or rng.random() > 0.05 else v.lower())
sales.loc[sales.sample(frac=0.005, random_state=3).index, "quantity"] = -1     # invalid returns entered as -1
sales.to_csv(RAW / "sales_raw.csv", index=False)

# ---------------- inventory (month-end snapshot) ----------------
sales_q = sales[sales["quantity"] > 0].copy()
sales_q["month"] = pd.to_datetime(sales_q["order_date"]).dt.to_period("M")
sold = sales_q.groupby(["month", "product_id"])["quantity"].sum().unstack(fill_value=0)

# reorder level = 60% of the average monthly demand (so low stock really happens)
avg_demand = sold.mean()
products["reorder_level"] = products["product_id"].map(lambda i: max(int(avg_demand[i] * 0.6), 5))
messy["reorder_level"] = products["reorder_level"]
messy.to_csv(RAW / "products_raw.csv", index=False)

inv_rows = []
stock = {int(p.product_id): int(avg_demand[p.product_id] * 1.6) for p in products.itertuples()}
for month, row in sold.iterrows():
    for p in products.itertuples():
        pid_ = int(p.product_id)
        stock[pid_] = max(stock[pid_] - int(row.get(pid_, 0)), 0)
        received = 0
        if stock[pid_] < p.reorder_level and rng.random() < 0.8:      # 20% of the time the order is missed
            target = int(avg_demand[pid_] * 1.6)
            received = target - stock[pid_]
            if rng.random() < 0.2:                                   # supplier delay -> partial delivery
                received = int(received * 0.5)
            stock[pid_] += received
        inv_rows.append({"month_end": month.end_time.strftime("%Y-%m-%d"), "product_id": pid_,
                         "units_received": int(received), "closing_stock": stock[pid_]})
pd.DataFrame(inv_rows).to_csv(RAW / "inventory_raw.csv", index=False)
print(f"products={len(products)} customers={len(customers)} sales_lines={len(sales)} inventory_rows={len(inv_rows)}")
