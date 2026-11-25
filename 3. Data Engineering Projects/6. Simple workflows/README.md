# Simple Workflows

Small, single-purpose data workflows. Each sub-folder is a self-contained task with its own notebook, input data, and documented output requirements — the kind of focused job that shows up as one step of a larger pipeline.

---

## Workflows

| Workflow | Goal | Stack |
|----------|------|-------|
| [Cleaning data with Pyspark](Cleaning%20data%20with%20Pyspark) | Clean Voltmart's order history so the ML team can build a demand-forecasting model | PySpark |

---

## Structure

```
6. Simple workflows/
└── Cleaning data with Pyspark/
    ├── README.md
    ├── notebook.ipynb
    ├── orders_data.parquet
    └── ecommerce_analytics-1224x532.jpg
```

Each workflow folder documents its input schema, the cleaning/business rules that must be applied, and how to run the notebook.

---

## Tools & Technologies

* **Language** — Python
* **Engines** — Apache Spark / PySpark
* **Formats** — Parquet
