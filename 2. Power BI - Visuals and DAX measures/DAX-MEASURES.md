# DAX Measures — Catalog

Complete list of the measures the `PowerBI Demo Raivis.pbix` report references, grouped by the DAX technique each one demonstrates.

**How this list was produced:** the `.pbix` stores its report definition as readable JSON inside the archive, so measure names, their parent tables, and the visuals that use them were read directly from that definition. The measure **formulas** are not included — they live in the compressed VertiPaq model. To see the actual DAX, open the file in Power BI Desktop (Model view → `Measure Table` → select a measure) or connect DAX Studio.

**Page legend:** `SUMMARY` · `CUSTOMERS` · `PRODUCTS` · `P-FP` (`PRODUCTS - FIELD PAREMETERS`) · `EMPLOYEES` · `SCENARIO` (`SCENARIO ANALYSIS`)

The **Technique** column is inferred from each measure's name and from the visual that uses it — it describes the DAX pattern the measure is there to demonstrate, not the verbatim expression.

---

## 1. Core aggregation — `Measure Table` (7)

| Measure | Technique | Used on |
|---------|-----------|---------|
| `Revenue` | Base additive measure on the sales fact | SCENARIO |
| `Cost` | Cost of goods sold from the fact table | SCENARIO |
| `Profit` | Derived measure (revenue minus cost) | SCENARIO |
| `Customer Count` | `DISTINCTCOUNT` style headcount of customers | CUSTOMERS, PRODUCTS, P-FP, EMPLOYEES |
| `Average Products Sold` | Average basket size per customer | CUSTOMERS, EMPLOYEES |
| `Average Sales per Store` | Sales divided by the store count | CUSTOMERS, PRODUCTS, P-FP, EMPLOYEES |
| `Sales measure` | Generic placeholder measure used by the field-parameter slicers | SUMMARY, CUSTOMERS, PRODUCTS, P-FP, EMPLOYEES |

---

## 2. Iterators and moving windows — `Measure Table` (3)

| Measure | Technique | Used on |
|---------|-----------|---------|
| `Average Daily Sales (AVERAGEX)` | `AVERAGEX` over a daily date set | CUSTOMERS, PRODUCTS, P-FP, EMPLOYEES |
| `Average Monthly Sales (AVERAGEX)` | `AVERAGEX` over a monthly date set | CUSTOMERS, PRODUCTS, P-FP, EMPLOYEES |
| `Moving Average (AVERAGEX)` | Rolling average built with `AVERAGEX` over a date window | CUSTOMERS |

---

## 3. Ranking — `Measure Table` (2)

| Measure | Technique | Used on |
|---------|-----------|---------|
| `Products Sales Rank TOP (RANKX)` | `RANKX` over products to surface the top sellers | PRODUCTS |
| `Customer Name SalesRank` | `RANKX` over customer names | CUSTOMERS |

---

## 4. Filter control — `Measure Table` (3)

| Measure | Technique | Used on |
|---------|-----------|---------|
| `% of Sales (REMOVEFILTERS) 2` | Share of total after `REMOVEFILTERS` | CUSTOMERS |
| `% of Sales (REMOVEFILTERS) Products` | Share of total with the product filter removed | PRODUCTS, P-FP |
| `Customers who Purchased (CROSSFILTER)` | Cross-filter direction changed with `CROSSFILTER` | CUSTOMERS, PRODUCTS, P-FP, EMPLOYEES |

---

## 5. Goal tracking with `TREATAS` — `Measure Table` (8, all on SUMMARY)

Each goal measure maps a `DATATABLE` target onto the model with `TREATAS`; the paired `% to Goal` measure divides actual sales by that target.

| Goal measure | Paired measure | Used on |
|--------------|----------------|---------|
| `Food Goal (TREATAS)` | `Food % to Goal` | SUMMARY |
| `Beverage Goal (TREATAS)` | `Beverage % to Goal` | SUMMARY |
| `Bean Goal (TREATAS)` | `Bean % to Goal` | SUMMARY |
| `Merchendise Goal (TREATAS)` | `Merchendise % to Goal` | SUMMARY |

The goals themselves come from the calculated tables `Target Sales - March 2019 (DATATABLE)` and `Target Sales - April 2019 (DATATABLE)`; the four gauges on `SUMMARY` visualise the `% to Goal` measures.

---

## 6. Year-over-year — `Measure Table` (1)

| Measure | Technique | Used on |
|---------|-----------|---------|
| `Customer Sales YoY % Change` | Year-over-year comparison using the `Calendar` table | SUMMARY |

---

## 7. Scenario analysis — `Measure Table` (4)

| Measure | Technique | Used on |
|---------|-----------|---------|
| `Scenario Revenue` | Revenue adjusted by the what-if parameters | SCENARIO |
| `Scenario Costs` | Costs adjusted by the cost parameter | SCENARIO |
| `Scenario Profits` | Scenario revenue minus scenario costs | SCENARIO |
| `% change of Scenario` | Delta between base and scenario values | SCENARIO |

---

## 8. What-if deltas — `Cost Changes` / `Price Changes` / `Demand Changes` (6)

These live on their own single-column tables so the slicers on `SCENARIO ANALYSIS` can drive them.

| Table | Measure | Used on |
|-------|---------|---------|
| `Cost Changes` | `% Cost Change` | SCENARIO |
| `Cost Changes` | `Percent Cost Change` | SCENARIO |
| `Price Changes` | `% Price Change` | SCENARIO |
| `Price Changes` | `Percent Price Change` | SCENARIO |
| `Demand Changes` | `% Demand Change` | SCENARIO |
| `Demand Changes` | `Percent Demand Change` | SCENARIO |

---

## 9. Table functions inside measures — `Unsold Pastries (SUMMARIZE)` (3)

| Measure | Technique | Used on |
|---------|-----------|---------|
| `Food Sold (SUMMARIZE Table)` | Aggregation over a `SUMMARIZE` result | PRODUCTS |
| `Food Unsold (SUMMARIZE Table)` | Difference between inventory and units sold | PRODUCTS |
| `Lost Revenue (SUMMARIZE Table)` | Unsold quantity valued at selling price | PRODUCTS |

These three feed the `SimpleWaterfall` custom visual on the `PRODUCTS` page.

---

## Summary

| Group | Count |
|-------|-------|
| Core aggregation | 7 |
| Iterators / moving windows | 3 |
| Ranking | 2 |
| Filter control | 3 |
| `TREATAS` goal tracking | 8 |
| Year-over-year | 1 |
| Scenario analysis | 4 |
| What-if deltas | 6 |
| Table functions in measures | 3 |
| **Total** | **37** |

---

## Naming notes

Kept as-is from the model, because renaming would break the report references:

* `Merchendise …` (spelled with an extra `e`) in the goal and `% to Goal` measures.
* `% of Sales (REMOVEFILTERS) 2` — the trailing `2` indicates a second variant of the same idea.
* `Sales measure` — a generic placeholder consumed by the `Sales measures selection` field parameter.
