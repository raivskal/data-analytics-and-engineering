# Databricks Projects

A set of Databricks projects built on Delta Lake and **Delta Live Tables (DLT)**, covering the advanced platform features a data engineer is expected to know: deployment automation with Asset Bundles, Unity Catalog data privacy, query performance tuning, structured streaming, and Change Data Capture ETL.

---

## Projects

| # | Project | What it covers |
|---|---------|----------------|
| 1 | [Advanced Databricks Data Engineering Examples](1.%20Advanced%20Databricks%20Data%20Engineering%20Examples) | Workshop-style demo and lab notebooks on Databricks Asset Bundles, Unity Catalog data privacy, performance optimization, and streaming / DLT |
| 2 | [Databricks ETL workflow with Change Data Capture](2.%20Databricks%20ETL%20workflow%20with%20Change%20Data%20Capture) | Medallion pipeline in DLT SQL using Change Data Feed and `APPLY CHANGES` (AUTO CDC) |
| 3 | [Simple Databricks ETL workflow with SQL](3.%20Simple%20Databricks%20ETL%20workflow%20with%20SQL) | Minimal DLT SQL pipeline that ingests the Million Song Dataset with `read_files` and builds derived tables |

---

## Folder structure

```
4. Databricks Projects/
├── 1. Advanced Databricks Data Engineering Examples/
│   ├── Automated deployment with Databricks Asset Bundles/
│   ├── Databricks Data Privacy/
│   ├── Databricks Performance Optimization/
│   └── Databricks Streaming/
├── 2. Databricks ETL workflow with Change Data Capture/
│   ├── ecommerce_etl.ipynb
│   ├── raw_customers.csv
│   └── raw_orders.csv
└── 3. Simple Databricks ETL workflow with SQL/
    └── databricks_etl_sql.ipynb
```

---

## Prerequisites

* A **Databricks workspace** with **Unity Catalog** enabled (catalogs, schemas, and volumes)
* **Delta Live Tables / Lakeflow Declarative Pipelines** available in the workspace
* A cluster or SQL warehouse running a recent Databricks Runtime — the CDC examples rely on Change Data Feed and `APPLY CHANGES`, and the performance examples use liquid clustering
* The Databricks CLI and a Databricks personal access token — only for the Asset Bundles notebooks

---

## How to run

1. Import the notebooks into your workspace (`Workspace → Import`, or sync the repo with **Databricks Repos**).
2. Attach a cluster or SQL warehouse and choose your target catalog/schema where the notebooks use placeholders such as `<catalog>.<schema>`.
3. Run the notebooks top to bottom. Project 1 contains `Demo - ...` walkthroughs next to `Lab - ...` exercises; the `.zip` files are Databricks Asset Bundle sources referenced by the deployment labs.

---

## Tools & Technologies

* **Platform** — Databricks, Unity Catalog, Databricks Asset Bundles
* **Storage format** — Delta Lake (Change Data Feed, liquid clustering)
* **Pipelines** — Delta Live Tables (SQL and Python), Auto Loader, structured streaming
* **Languages** — Python (PySpark), SQL
