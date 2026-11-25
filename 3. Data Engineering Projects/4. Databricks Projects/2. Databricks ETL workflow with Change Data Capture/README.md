# Databricks ETL Workflow with Change Data Capture

An end-to-end e-commerce ETL pipeline built with **Delta Live Tables (SQL)** and **Delta Lake Change Data Feed**, following the medallion architecture and applying changes with Delta's `APPLY CHANGES` (AUTO CDC) API.

---

## Pipeline design

| Layer | Table | What it does |
|-------|-------|--------------|
| Bronze | `bronze_orders_cdc` | Raw order events ingested as a streaming table with `delta.enableChangeDataFeed = true` |
| Bronze | `bronze_customers_cdc` | Raw customer events ingested as a streaming table with Change Data Feed enabled |
| Silver | `silver_orders` | Current-state view of completed orders, maintained by AUTO CDC: `KEYS (order_id)`, deletes applied when `order_status = 'CANCELLED'`, ordered by `SEQUENCE BY ingestion_ts` |
| Silver | `silver_orders_enriched` | Orders joined to customer attributes |
| Gold | `gold_sales_by_country` | Materialized view with revenue and order metrics per country |

Because the Bronze tables capture every insert, update, and delete, the Silver tables can be rebuilt deterministically from history, and the Gold view always reflects the latest state.

---

## Files

| File | Description |
|------|-------------|
| `ecommerce_etl.ipynb` | The full DLT pipeline: Bronze CDF streaming tables, Silver `APPLY CHANGES` transformations and enrichment, Gold materialized view |
| `raw_customers.csv` | Sample customer change records |
| `raw_orders.csv` | Sample order change records |

---

## Prerequisites

* A Databricks workspace with **Delta Live Tables** and **Unity Catalog** enabled
* A schema (and, for the CSV files, a volume or landing location) to hold the pipeline objects
* A recent Databricks Runtime — `APPLY CHANGES` and Change Data Feed require a runtime that supports them
* A DLT pipeline configured to run the notebook, normally in **continuous** mode so CDC is applied incrementally

---

## Running the pipeline

1. Create a DLT pipeline whose source is `ecommerce_etl.ipynb` and select a target catalog/schema.
2. Set the placeholder `<catalog>.<schema>` references to your own catalog and schema.
3. Start the pipeline. The Bronze tables ingest the raw CSVs, Silver applies the CDC changes, and Gold is refreshed as a materialized view.

---

## Notes

* `ingestion_ts` is the sequencing column: it determines which version of a record wins when several changes arrive for the same `order_id`.
* Cancelled orders are removed from `silver_orders` (not flagged), so downstream consumers read current, valid orders only.

---

## Tools & Technologies

* Delta Live Tables (declarative pipelines, streaming tables, materialized views)
* Delta Lake — Change Data Feed, `APPLY CHANGES INTO` (AUTO CDC)
* Spark SQL (DLT SQL)
