# Power BI Demo — Visuals & DAX Measures

A single Power BI Desktop report that demonstrates report design (visual types, slicers, bookmarks, navigation, field parameters) and a broad set of DAX patterns — iterators, ranking, filter manipulation, `TREATAS` goal tracking, scenario analysis, and DAX table functions — on a retail sales model.

> Measure names, page names, visual types, table names, and which measure is used on which page were all read out of the report definition packaged inside the `.pbix`. Full details in [DAX-MEASURES.md](DAX-MEASURES.md).

---

## Report file

| Property | Value |
|----------|-------|
| File | `PowerBI Demo Raivis.pbix` |
| Size | 5.70 MB |
| Last saved | 02.07.2026 |
| Created with | Power BI Desktop 2026.06 |
| Report format | PBIR (`Report/definition/…` layout inside the archive) |
| Pages | 6, each 1280 × 720 px |
| Model tables | 36 |
| Measures | 28 in `Measure Table`, plus 6 what-if deltas and 3 table-function measures |
| Custom visuals | `SimpleWaterfall`, `ChicletSlicer` |
| Bookmarks | 5 — `Clear Filter Page 1` … `Clear Filter Page 5` |

---

## Report pages

| Page | Visuals | What it demonstrates |
|------|---------|----------------------|
| `SUMMARY` | 32 — 6 cards, 4 gauges, 2 treemaps, line chart, map, 6 slicers, 2 text boxes, 7 images | Year KPI cards (`2017`, `2018`, `2019` plus the comparisons `2017 vs 2018` and `2018 vs 2019`); four gauges driven by the `TREATAS` goal measures; treemaps over the product hierarchy; a store map using `store_latitude` / `store_longitude`; a line chart with `Customer Sales YoY % Change` |
| `CUSTOMERS` | 27 — pivot table, combo chart, donut chart, 100% stacked column, 6 cards, 6 slicers | Customer segmentation by `Age Group` and `Customer Sales (High/Low)`; `Customer Name SalesRank`; `Moving Average (AVERAGEX)`; `% of Sales (REMOVEFILTERS) 2` |
| `PRODUCTS` | 25 — 2 pivot tables, SimpleWaterfall, 5 cards, 6 slicers | Product-group hierarchy drill-down; `Products Sales Rank TOP (RANKX)`; `% of Sales (REMOVEFILTERS) Products`; an unsold-pastry waterfall built from the `SUMMARIZE` measures |
| `PRODUCTS - FIELD PAREMETERS` | 25 — 8 slicers, pivot table, SimpleWaterfall, 5 cards | Field-parameter page: the `Sales measures selection` and `Parameter` tables let a viewer swap the measure shown in the pivot table and waterfall without editing the report |
| `EMPLOYEES` | 27 — waterfall, line chart, table, 6 cards, 7 slicers | Employee dimension (`first_name`, `last_name`, `position`) with per-employee averages and `Customers who Purchased (CROSSFILTER)` |
| `SCENARIO ANALYSIS` | 24 — 9 slicers, pivot table, line chart, 4 cards | What-if parameters `Cost Changes`, `Price Changes`, `Demand Changes` feed `Scenario Revenue / Costs / Profits` and `% change of Scenario`, summarised by three `% … Change` cards |

The field-parameter page is stored with the display name `PRODUCTS - FIELD PAREMETERS` (typo included) and is documented exactly as it appears in the file.

---

## Data model (36 tables)

| Group | Tables |
|-------|--------|
| Dimensions | `Calendar`, `Customer Lookup`, `Employee Lookup`, `Product Lookup`, `Store Lookup` |
| Facts | `Sales by Store`, `Food Inventory` |
| Measure table | `Measure Table` — every reusable measure lives here |
| DAX table-function demos | `DISTINCT Example`, `VALUES Example`, `ADDCOLUMNS Demo`, `SELECTCOLUMNS Demo`, `SUMMARIZE Demo`, `Unsold Pastries (SUMMARIZE)`, `Row Demo`, `DATATABLE Demo`, `GENERATESERIES Demo`, `Table Constructor Demo`, `CROSSJOIN Demo`, `EXCEPT Demo`, `New Employees (INTERSECT)`, `Repeat Customers Sales (INTERSECT Assignment)`, `UNION Demo`, `TREATAS Demo`, `Average Days`, `CALENDAR Demo`, `CALENDARAUTO Demo`, `4-5-4 Calendar`, `Date Table with CALENDARAUTO`, `Target Sales - March 2019 (DATATABLE)`, `Target Sales - April 2019 (DATATABLE)` |
| What-if & field parameters | `Sales measures selection`, `Parameter`, `Cost Changes`, `Price Changes`, `Demand Changes` |

The demo tables are named after the DAX function they illustrate — each is a calculated table whose result shows what that function returns against the same retail data. `4-5-4 Calendar` and `Date Table with CALENDARAUTO` contrast a hand-built date table with a generated one, and the two `Target Sales - … (DATATABLE)` tables supply the goals consumed by the `TREATAS` measures.

Model note: relationship auto-detection is **disabled** in the report settings, so relationships are defined manually — use the model view in Power BI Desktop as the source of truth for cardinality and filter direction.

---

## DAX measures

28 measures live in `Measure Table`, grouped here by the technique they demonstrate. The full catalog — every measure with the page it appears on — is in [DAX-MEASURES.md](DAX-MEASURES.md).

| Technique | Measures |
|-----------|----------|
| Core aggregation | `Revenue`, `Cost`, `Profit`, `Customer Count`, `Average Products Sold`, `Average Sales per Store`, `Sales measure` |
| Iterators / moving windows | `Average Daily Sales (AVERAGEX)`, `Average Monthly Sales (AVERAGEX)`, `Moving Average (AVERAGEX)` |
| Ranking | `Products Sales Rank TOP (RANKX)`, `Customer Name SalesRank` |
| Filter control | `% of Sales (REMOVEFILTERS) 2`, `% of Sales (REMOVEFILTERS) Products`, `Customers who Purchased (CROSSFILTER)` |
| Goal tracking with `TREATAS` | `Food / Beverage / Bean / Merchendise Goal (TREATAS)` plus the matching `% to Goal` measures |
| Year-over-year | `Customer Sales YoY % Change` |
| Scenario analysis | `Scenario Revenue`, `Scenario Costs`, `Scenario Profits`, `% change of Scenario` |
| What-if deltas | `Cost Changes` / `Price Changes` / `Demand Changes` → `% … Change`, `Percent … Change` |
| Table functions inside measures | `Food Sold (SUMMARIZE Table)`, `Food Unsold (SUMMARIZE Table)`, `Lost Revenue (SUMMARIZE Table)` |

---

## Bookmarks and navigation

Five bookmarks — `Clear Filter Page 1` to `Clear Filter Page 5` — are wired to reset buttons so a viewer can return a page to its default filter state. Each page also carries an image/text header (`SUMMARY`, `CUSTOMERS`, `PRODUCTS`, `EMPLOYEES`, `SCENARIO ANALYSIS`) that acts as navigation.

---

## How to open

1. Install **Power BI Desktop** (Windows only); the file was saved with the 2026.06 release, so a current version is recommended.
2. Open `PowerBI Demo Raivis.pbix` by double-clicking it.
3. The report is self-contained — the model data is imported into the file, so no database connection or gateway is required.
4. The two custom visuals are embedded in the file, but Power BI may still prompt to allow them; if either shows an error, import it from AppSource.

---

## Notes for version control

* `.pbix` is a binary container (a ZIP holding the compressed VertiPaq model plus the report definition) — Git cannot diff it meaningfully, and a one-visual change rewrites the whole file.
* The measure **formulas** live inside the compressed model, which is why [DAX-MEASURES.md](DAX-MEASURES.md) documents names, technique, and usage rather than code. To read the DAX itself, open the file in Power BI Desktop (Model view → measure) or connect DAX Studio.
* If you want the definition reviewable in Git, export the report as **PBIP** (`File → Save as → Power BI Project`); that produces the same PBIR folder layout these notes were generated from.
* Naming quirks kept as-is in the model: `Store Lookup.Neighorhood`, the `Merchendise …` measures, and the `PAREMETERS` page name.

---

## Contents

| File | Description |
|------|-------------|
| `README.md` | This overview: report structure, pages, model, how to open |
| `DAX-MEASURES.md` | Catalog of all 37 measures with technique and page usage |
| `PowerBI Demo Raivis.pbix` | The Power BI Desktop report |

---

## Tools & Technologies

* **BI tool** — Power BI Desktop (2026.06), PBIR report format
* **Language** — DAX (measures, calculated tables, what-if parameters, field parameters)
* **Data** — imported retail sample model (stores, products, customers, employees, sales transactions)
* **Custom visuals** — SimpleWaterfall, ChicletSlicer
* **Extras** — bookmarks for filter reset, page navigation buttons

