# Strategy for Small Grocery Market - Power BI Dashboard

An interactive Power BI dashboard that analyses **sales performance, inventory levels and customer purchasing behaviour** for a small grocery business. Raw sales data is cleaned and modelled (Python, Excel, Power BI) and measured with DAX to track revenue and stock trends.

> **Data note:** the files in `data/` are **synthetic sample data** created by `python/generate_grocery_data.py`, so the project can be run by anyone. Replace `data/raw/*.csv` with real store data to reuse it.

## Workflow
```
Raw CSVs -> Python cleaning -> Star schema (data/clean) -> Power BI model + DAX -> Dashboard
```

## Data cleaning steps
- Removed exact duplicate sales lines
- Removed invalid quantities (0 or negative)
- Filled blank payment modes with "Unknown" and standardised text (UPI, Cash, Card)
- Standardised category names (trim and consistent casing)
- Marked walk-in customers as ID 0 (kept in sales, excluded from customer metrics)
- Calculated revenue, cost and profit per line

## Data model (star schema)
`fact_sales` and `fact_inventory` connect to `dim_date`, `dim_product` and `dim_customer`.

## Dashboard pages
1. **Sales Overview:** revenue, profit, margin, orders, AOV, year-over-year trend
2. **Product and Category:** best sellers, margins, category share
3. **Inventory:** stock on hand, reorder alerts, stock-out frequency
4. **Customers:** repeat rate, AOV by membership, walk-in share

## Project structure
```
data/raw/            messy input files
data/clean/          cleaned star schema (load these into Power BI)
python/              generate_grocery_data.py, clean_and_model.py
sql/                 analysis_queries.sql (9 business queries)
powerbi/             dax_measures.md, dashboard_build_guide.md, (your .pbix + screenshots)
```

## Run it
```bash
pip install -r requirements.txt
python python/generate_grocery_data.py   # optional
python python/clean_and_model.py
```
Then follow `powerbi/dashboard_build_guide.md`.

## Tools
Power BI, DAX, Excel, SQL, Python (pandas)

## Author
Kirubagaran S
