-- Analysis queries on the cleaned star schema (tables: fact_sales, dim_product, dim_customer,
-- dim_date, fact_inventory). Standard SQL; tested on SQLite. Import the CSVs into MySQL/SQL Server to use them there.

-- 1. Monthly revenue and profit
SELECT d.year_month,
       ROUND(SUM(f.revenue), 0) AS revenue,
       ROUND(SUM(f.profit), 0)  AS profit,
       ROUND(100.0 * SUM(f.profit) / SUM(f.revenue), 1) AS margin_pct
FROM fact_sales f
JOIN dim_date d ON d.date = DATE(f.order_date)
GROUP BY d.year_month
ORDER BY d.year_month;

-- 2. Category performance
SELECT p.category,
       SUM(f.quantity) AS units,
       ROUND(SUM(f.revenue), 0) AS revenue,
       ROUND(100.0 * SUM(f.profit) / SUM(f.revenue), 1) AS margin_pct,
       ROUND(100.0 * SUM(f.revenue) / (SELECT SUM(revenue) FROM fact_sales), 1) AS revenue_share_pct
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.category
ORDER BY revenue DESC;

-- 3. Top 10 products by profit
SELECT p.product_name, p.category, SUM(f.quantity) AS units, ROUND(SUM(f.profit), 0) AS profit
FROM fact_sales f
JOIN dim_product p ON p.product_id = f.product_id
GROUP BY p.product_id
ORDER BY profit DESC
LIMIT 10;

-- 4. Sales by day of week (weekend vs weekday behaviour)
SELECT d.day_name, COUNT(DISTINCT f.order_id) AS orders, ROUND(SUM(f.revenue), 0) AS revenue
FROM fact_sales f
JOIN dim_date d ON d.date = DATE(f.order_date)
GROUP BY d.day_name
ORDER BY revenue DESC;

-- 5. Average order value by customer membership
SELECT c.membership,
       COUNT(DISTINCT f.order_id) AS orders,
       ROUND(SUM(f.revenue) / COUNT(DISTINCT f.order_id), 1) AS avg_order_value
FROM fact_sales f
JOIN dim_customer c ON c.customer_id = f.customer_id
GROUP BY c.membership
ORDER BY avg_order_value DESC;

-- 6. Repeat customers (excluding walk-ins)
SELECT CASE WHEN orders >= 2 THEN 'Repeat' ELSE 'One-time' END AS customer_type, COUNT(*) AS customers
FROM (SELECT customer_id, COUNT(DISTINCT order_id) AS orders
      FROM fact_sales WHERE customer_id <> 0 GROUP BY customer_id)
GROUP BY customer_type;

-- 7. Products currently at or below reorder level (latest month)
SELECT p.product_name, p.category, i.closing_stock, i.reorder_level
FROM fact_inventory i
JOIN dim_product p ON p.product_id = i.product_id
WHERE i.month_end = (SELECT MAX(month_end) FROM fact_inventory)
  AND i.closing_stock <= i.reorder_level
ORDER BY i.closing_stock;

-- 8. Products with the most stock-out months
SELECT p.product_name, SUM(i.stockout) AS stockout_months, SUM(i.below_reorder) AS below_reorder_months
FROM fact_inventory i
JOIN dim_product p ON p.product_id = i.product_id
GROUP BY p.product_id
HAVING SUM(i.below_reorder) > 0
ORDER BY stockout_months DESC, below_reorder_months DESC
LIMIT 10;

-- 9. Month-over-month revenue growth (window function)
WITH m AS (
    SELECT d.year_month, SUM(f.revenue) AS revenue
    FROM fact_sales f JOIN dim_date d ON d.date = DATE(f.order_date)
    GROUP BY d.year_month
)
SELECT year_month, ROUND(revenue, 0) AS revenue,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year_month)) / LAG(revenue) OVER (ORDER BY year_month), 1) AS mom_growth_pct
FROM m
ORDER BY year_month;
