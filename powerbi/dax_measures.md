# DAX Measures - Grocery Dashboard

Create a blank table called `_Measures` (Home > Enter Data) and add all measures below into it, so they are easy to find.

## Model relationships (Model view)
| From (many) | To (one) | Direction |
|-------------|----------|-----------|
| `fact_sales[order_date]` | `dim_date[date]` | Single |
| `fact_sales[product_id]` | `dim_product[product_id]` | Single |
| `fact_sales[customer_id]` | `dim_customer[customer_id]` | Single |
| `fact_inventory[product_id]` | `dim_product[product_id]` | Single |
| `fact_inventory[month_end]` | `dim_date[date]` | Single |

Mark `dim_date` as a **date table** (Table tools > Mark as date table > `date`).

## Sales measures
```DAX
Revenue = SUM ( fact_sales[revenue] )

Total Cost = SUM ( fact_sales[cost] )

Gross Profit = SUM ( fact_sales[profit] )

Profit Margin % = DIVIDE ( [Gross Profit], [Revenue] )

Orders = DISTINCTCOUNT ( fact_sales[order_id] )

Units Sold = SUM ( fact_sales[quantity] )

Avg Order Value = DIVIDE ( [Revenue], [Orders] )

Discount Given = SUM ( fact_sales[discount_amount] )

Discount % of Gross = DIVIDE ( [Discount Given], SUM ( fact_sales[gross_amount] ) )
```

## Time intelligence
```DAX
Revenue LY =
CALCULATE ( [Revenue], SAMEPERIODLASTYEAR ( dim_date[date] ) )

Revenue YoY % =
DIVIDE ( [Revenue] - [Revenue LY], [Revenue LY] )

Revenue MTD = TOTALMTD ( [Revenue], dim_date[date] )

Revenue YTD = TOTALYTD ( [Revenue], dim_date[date] )

Revenue 3M Moving Avg =
DIVIDE (
    CALCULATE ( [Revenue], DATESINPERIOD ( dim_date[date], MAX ( dim_date[date] ), -3, MONTH ) ),
    3
)

Weekend Revenue Share =
DIVIDE ( CALCULATE ( [Revenue], dim_date[is_weekend] = 1 ), [Revenue] )
```

## Product and category
```DAX
Revenue % of Total =
DIVIDE ( [Revenue], CALCULATE ( [Revenue], ALLSELECTED ( dim_product ) ) )

Top Product by Profit =
VAR t =
    TOPN ( 1, ALLSELECTED ( dim_product[product_name] ), [Gross Profit], DESC )
RETURN
    CONCATENATEX ( t, dim_product[product_name], ", " )
```

## Customers
```DAX
Identified Customers =
CALCULATE ( DISTINCTCOUNT ( fact_sales[customer_id] ), fact_sales[customer_id] <> 0 )

Repeat Customers =
COUNTROWS (
    FILTER (
        VALUES ( fact_sales[customer_id] ),
        fact_sales[customer_id] <> 0 && CALCULATE ( DISTINCTCOUNT ( fact_sales[order_id] ) ) >= 2
    )
)

Repeat Customer Rate % = DIVIDE ( [Repeat Customers], [Identified Customers] )

Walk-in Revenue Share =
DIVIDE ( CALCULATE ( [Revenue], fact_sales[customer_id] = 0 ), [Revenue] )
```

## Inventory (uses the latest month in the current filter)
```DAX
Stock on Hand =
VAR lastMonth = MAX ( fact_inventory[month_end] )
RETURN CALCULATE ( SUM ( fact_inventory[closing_stock] ), fact_inventory[month_end] = lastMonth )

Products Below Reorder Level =
VAR lastMonth = MAX ( fact_inventory[month_end] )
RETURN CALCULATE ( SUM ( fact_inventory[below_reorder] ), fact_inventory[month_end] = lastMonth )

Stock-out Products =
VAR lastMonth = MAX ( fact_inventory[month_end] )
RETURN CALCULATE ( SUM ( fact_inventory[stockout] ), fact_inventory[month_end] = lastMonth )

Stock-out Months = SUM ( fact_inventory[stockout] )

Avg Monthly Units Sold =
DIVIDE ( [Units Sold], DISTINCTCOUNT ( dim_date[year_month] ) )

Stock Cover (months) =
DIVIDE ( [Stock on Hand], [Avg Monthly Units Sold] )
```

## Conditional colour (Format > Conditional formatting > Field value)
```DAX
Margin Colour =
SWITCH ( TRUE (), [Profit Margin %] >= 0.22, "#16a34a", [Profit Margin %] >= 0.18, "#f59e0b", "#ef4444" )
```
