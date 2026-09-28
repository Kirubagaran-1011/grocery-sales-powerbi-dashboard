"""
Cleans the raw grocery files and builds a star schema for Power BI:

    dim_date, dim_product, dim_customer, fact_sales, fact_inventory

Run:  python python/clean_and_model.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW, CLEAN = ROOT / "data" / "raw", ROOT / "data" / "clean"
CLEAN.mkdir(parents=True, exist_ok=True)
log = []

# ---------- products ----------
products = pd.read_csv(RAW / "products_raw.csv")
products["category"] = products["category"].str.strip().str.title().str.replace("&", "&", regex=False)
products["product_name"] = products["product_name"].str.strip()
products = products.drop_duplicates("product_id")
products["margin_pct"] = ((products["unit_price"] - products["unit_cost"]) / products["unit_price"] * 100).round(1)

# ---------- customers ----------
customers = pd.read_csv(RAW / "customers_raw.csv", parse_dates=["joined_date"])
customers = customers.drop_duplicates("customer_id")
customers = pd.concat([customers, pd.DataFrame([{"customer_id": 0, "customer_name": "Walk-in Customer", "area": "Unknown",
                                                 "membership": "None", "joined_date": pd.NaT}])], ignore_index=True)

# ---------- sales ----------
sales = pd.read_csv(RAW / "sales_raw.csv", parse_dates=["order_date"])
n0 = len(sales)
sales = sales.drop_duplicates()
log.append(f"Removed {n0 - len(sales)} exact duplicate rows")

bad = (sales["quantity"] <= 0).sum()
sales = sales[sales["quantity"] > 0]
log.append(f"Removed {bad} rows with invalid quantity")

blank_pay = sales["payment_mode"].isna().sum()
sales["payment_mode"] = sales["payment_mode"].fillna("Unknown").str.strip().str.title()
sales["payment_mode"] = sales["payment_mode"].replace({"Upi": "UPI"})
log.append(f"Filled {blank_pay} blank payment modes with 'Unknown'")

sales["customer_id"] = sales["customer_id"].fillna(0).astype(int)      # 0 = walk-in
sales = sales.merge(products[["product_id", "unit_cost"]], on="product_id", how="left")
sales["gross_amount"] = (sales["quantity"] * sales["unit_price"]).round(2)
sales["discount_amount"] = (sales["gross_amount"] * sales["discount_pct"] / 100).round(2)
sales["revenue"] = (sales["gross_amount"] - sales["discount_amount"]).round(2)
sales["cost"] = (sales["quantity"] * sales["unit_cost"]).round(2)
sales["profit"] = (sales["revenue"] - sales["cost"]).round(2)
sales["line_id"] = range(1, len(sales) + 1)
fact_sales = sales[["line_id", "order_id", "order_date", "customer_id", "product_id", "quantity", "unit_price",
                    "discount_pct", "payment_mode", "gross_amount", "discount_amount", "revenue", "cost", "profit"]]

# ---------- inventory ----------
inv = pd.read_csv(RAW / "inventory_raw.csv", parse_dates=["month_end"])
inv = inv.merge(products[["product_id", "reorder_level"]], on="product_id")
inv["below_reorder"] = (inv["closing_stock"] <= inv["reorder_level"]).astype(int)
inv["stockout"] = (inv["closing_stock"] == 0).astype(int)
fact_inventory = inv

# ---------- date dimension ----------
d = pd.DataFrame({"date": pd.date_range(fact_sales["order_date"].min(), fact_sales["order_date"].max())})
d["year"] = d["date"].dt.year
d["quarter"] = "Q" + d["date"].dt.quarter.astype(str)
d["month_number"] = d["date"].dt.month
d["month_name"] = d["date"].dt.strftime("%b")
d["year_month"] = d["date"].dt.strftime("%Y-%m")
d["day_name"] = d["date"].dt.day_name()
d["is_weekend"] = (d["date"].dt.dayofweek >= 5).astype(int)
dim_date = d

# ---------- save ----------
dim_date.to_csv(CLEAN / "dim_date.csv", index=False)
products.to_csv(CLEAN / "dim_product.csv", index=False)
customers.to_csv(CLEAN / "dim_customer.csv", index=False)
fact_sales.to_csv(CLEAN / "fact_sales.csv", index=False)
fact_inventory.to_csv(CLEAN / "fact_inventory.csv", index=False)

print("Cleaning log:")
for line in log:
    print(" -", line)
print(f"\nfact_sales rows: {len(fact_sales):,}   revenue: {fact_sales['revenue'].sum():,.0f}   profit: {fact_sales['profit'].sum():,.0f}")
print("Saved star schema files to", CLEAN)
