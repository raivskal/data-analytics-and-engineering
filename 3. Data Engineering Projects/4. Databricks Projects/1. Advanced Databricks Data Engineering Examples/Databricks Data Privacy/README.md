# Databricks Data Privacy

Protecting sensitive data inside the lakehouse with **Unity Catalog** and **Delta Lake Change Data Feed**: restricting access, masking PII, breaking the link between identities and records, and propagating privacy-safe changes downstream.

---

## What is covered

* Securing data in Unity Catalog — catalogs, schemas, tables, volumes, and least-privilege grants
* PII data security — detecting, masking, and restricting access to personal data
* **Pseudonymization** with a lookup table, so records can be analysed without exposing identifiers
* **Anonymization** of user attributes such as age
* Using **Change Data Feed (CDF)** to process record changes and propagate them into downstream tables
* Lab: propagating changes with CDF

---

## Notebooks

| Notebook | Type | Description |
|----------|------|-------------|
| `DP 1.1 - Securing Data in Unity Catalog.ipynb` | Demo | Unity Catalog objects and access control |
| `DP 1.2 - PII Data Security.ipynb` | Demo | Identifying and protecting PII |
| `DP 1.2.1 - Pseudonymized PII Lookup Table.ipynb` | Demo | Replacing identifiers through a lookup table |
| `DP 1.2.2 - Anonymized Users Age.ipynb` | Demo | Anonymizing an age attribute |
| `DP 1.3 - Processing Records from CDF and Propagating Changes.ipynb` | Demo | Reading CDF and pushing changes downstream |
| `DP 1.4L - Propagating Changes with CDF Lab.ipynb` | Lab | Hands-on change propagation exercise |

---

## Prerequisites

* A Databricks workspace with **Unity Catalog** enabled
* Permission to create catalogs/schemas (or a pre-created sandbox schema)
* Delta tables with `delta.enableChangeDataFeed = true` for the CDF notebooks
* Access to the workshop data used by the demo notebooks, or equivalent tables of your own

---

## Notes

* The notebooks use placeholders such as `<catalog>.<schema>` — set them to your own catalog and schema before running.
* Grant statements assume a small set of demo users/groups; adjust them to principals that exist in your workspace.

---

## Tools & Technologies

* Unity Catalog — grants, row filters, column masks, dynamic views
* Delta Lake — Change Data Feed, table history and versioning
* Spark SQL and Python
