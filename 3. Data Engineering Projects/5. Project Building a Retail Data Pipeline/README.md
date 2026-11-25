# Building a Retail Data Pipeline

An ETL pipeline built for **Walmart** e-commerce analysis: grocery sales are combined with complementary economic data to study supply and demand around public holidays such as the Super Bowl, Labour Day, Thanksgiving, and Christmas.

---

## Business context

Walmart's e-commerce business reached roughly $80 billion (about 13% of total sales) by the end of 2022, and public holidays are one of the strongest drivers of weekly sales. To plan supply and demand around those peaks, the data team needs a repeatable pipeline that produces a clean, analysis-ready table plus a monthly sales aggregate.

---

## Sources

| Source | Description |
|--------|-------------|
| `grocery_sales` (PostgreSQL) | Weekly sales per store and department: `"index"`, `"Store_ID"`, `"Date"`, `"Weekly_Sales"`, `"Dept"`, `"IsHoliday"` |
| `extra_data.parquet` | Complementary economic indicators (`CPI`, `Unemployment`) keyed by the same `index` |

---

## Pipeline design

The notebook is organised as four functions plus a validation step, so each stage can be tested independently:

1. **`extract(store_data, extra_data)`** — reads the Parquet file and merges it with the `grocery_sales` table on `index`.
2. **`transform(raw_data)`** — fills missing `CPI`, `Weekly_Sales`, and `Unemployment` values with their column means, parses `Date`, and derives a `Month` column.
3. **`avg_weekly_sales_per_month(clean_data)`** — chains `groupby()`, `agg()`, `reset_index()`, and `round()` to compute the average weekly sales per month (`Avg_Sales`).
4. **`load(full_data, full_data_file_path, agg_data, agg_data_file_path)`** — writes both DataFrames to CSV with `index=False`.
5. **`validation(file_path)`** — raises an exception if an expected output file is missing.

---

## Outputs

`clean_data.csv` — one row per store / department / week:

| Column | Description |
|--------|-------------|
| `Store_ID` | Store number |
| `Dept` | Department number |
| `Weekly_Sales` | Sales for that store and department for the week |
| `IsHoliday` | Holiday-week flag |
| `CPI` | Consumer Price Index |
| `Unemployment` | Unemployment rate |
| `Month` | Month extracted from `Date` |

`agg_data.csv` — average weekly sales per month:

| Column | Description |
|--------|-------------|
| `Month` | Calendar month |
| `Avg_Sales` | Mean weekly sales across all stores and departments in that month |

---

## Contents

| File | Description |
|------|-------------|
| `notebook.ipynb` | Full pipeline: `extract`, `transform`, `avg_weekly_sales_per_month`, `load`, `validation` |
| `extra_data.parquet` | Complementary economic data merged on `index` |
| `clean_data.csv` | Output of the transformation stage |
| `agg_data.csv` | Monthly average weekly sales aggregate |
| `walmartecomm.jpg` | Project illustration |

---

## Running the notebook

```bash
pip install pandas pyarrow
jupyter notebook notebook.ipynb
```

Run the cells in order. The first cell queries the `grocery_sales` table, so it requires the project's PostgreSQL connection (or an existing `grocery_sales` DataFrame); the remaining cells read `extra_data.parquet` from the same folder and write `clean_data.csv` and `agg_data.csv`.

---

## Tools & Technologies

* **Language** — Python, SQL
* **Libraries** — pandas, `pyarrow` (Parquet), `os`
* **Storage** — PostgreSQL, Parquet, CSV
* **Environment** — Jupyter Notebook
