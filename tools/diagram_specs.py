"""Layout specs for the README diagrams (consumed by tools/build_diagrams.py).

Each spec has rows. A row lays its nodes out horizontally, evenly spaced and
centred; `band` draws a dashed lane behind the row, `edges` draws a horizontal
arrow with a small label between two nodes, `links` connect rows vertically,
and `connectors` draw straight relationship lines (star schema).

Node keys: id, title, sub ("\n" for a second line), icons (names from the
registry in build_diagrams.py), accent (left accent bar colour).
"""
from __future__ import annotations

SLATE = "#4b6b7b"
PY = "#3776ab"
PANDA = "#150458"
STATS = "#7a93d1"
ML = "#f7931e"
DL = "#ff6f00"
VIZ = "#3f4f75"
PBI = "#f2c811"
PBI_TEAL = "#118dff"
DOC = "#243b53"
PG = "#336791"
DBT = "#ff694a"
AIRFLOW = "#017cee"
STREAM = "#ff4b4b"
DBX = "#ff3621"
CI = "#2088ff"
QUALITY = "#0a9396"
GEN = "#4285f4"
FRAME = "#1c3c3c"
DJANGO = "#0c4b33"
SPARK = "#e25a1c"
KAFKA = "#1f2b36"


SPECS = [
    # ------------------------------------------------------------------ 01 --
    {
        "slug": "01-analytics-ml-flow",
        "name": "Data analytics and machine learning: from raw data to a validated model",
        "caption": "Data analytics & machine learning | 7 folders | 33 notebooks",
        "out": "assets/diagrams/01-analytics-ml-flow",
        "width": 1400,
        "node_w": 186,
        "rows": [
            {
                "band": "FROM DATA TO MODEL",
                "nodes": [
                    {"id": "src", "title": "Data sources",
                     "sub": "CSV · REST API\nExcel exports",
                     "icons": ["csv", "requests", "openpyxl"], "accent": SLATE},
                    {"id": "py", "title": "Python",
                     "sub": "scripts · notebooks",
                     "icons": ["python", "jupyter"], "accent": PY},
                    {"id": "pandas", "title": "pandas · NumPy",
                     "sub": "clean · reshape\njoin · aggregate",
                     "icons": ["pandas", "numpy"], "accent": PANDA},
                    {"id": "stats", "title": "Statistics",
                     "sub": "CLT · z-scores\nhypothesis tests",
                     "icons": ["scipy"], "accent": STATS},
                    {"id": "ml", "title": "Machine learning",
                     "sub": "regression\nclassify · cluster",
                     "icons": ["scikitlearn", "xgboost", "catboost"], "accent": ML},
                    {"id": "dl", "title": "Neural networks",
                     "sub": "ANN · CNN",
                     "icons": ["tensorflow", "keras"], "accent": DL},
                    {"id": "viz", "title": "Visualisation",
                     "sub": "charts · dashboards",
                     "icons": ["matplotlib", "seaborn", "plotly"], "accent": VIZ},
                ],
                "edges": [("src", "py", "load"), ("py", "pandas", "wrangle"),
                          ("pandas", "stats", "describe"), ("stats", "ml", "fit"),
                          ("ml", "dl", "deepen"), ("dl", "viz", "report")],
            },
        ],
    },

    # ------------------------------------------------------------------ 02 --
    {
        "slug": "01-folder-map",
        "name": "Folder map: foundations first, then the model families",
        "caption": "Folder map | order follows the original course",
        "out": "assets/diagrams/01-folder-map",
        "width": 1200,
        "node_w": 216,
        "rows": [
            {
                "band": "FOUNDATIONS",
                "nodes": [
                    {"id": "f1", "title": "1 · Python",
                     "sub": "API use · files\nTkinter GUI",
                     "icons": ["python", "requests", "tkinter"], "accent": PY},
                    {"id": "f2", "title": "2 · pandas",
                     "sub": "DataFrames · NaNs\ntime series · charts",
                     "icons": ["pandas", "numpy", "plotly"], "accent": PANDA},
                    {"id": "f3", "title": "3 · Statistics",
                     "sub": "sampling · CLT\nBayes · tests",
                     "icons": ["scipy", "seaborn", "notebook"], "accent": STATS},
                ],
                "edges": [("f1", "f2", "next"), ("f2", "f3", "next")],
            },
            {
                "band": "MODELLING",
                "nodes": [
                    {"id": "m4", "title": "4 · Regression",
                     "sub": "polynomial · SVR\ntrees · forests",
                     "icons": ["scikitlearn", "xgboost", "catboost"], "accent": ML},
                    {"id": "m5", "title": "5 · Classification",
                     "sub": "KNN · SVM · Bayes\ntuning · boosting",
                     "icons": ["scikitlearn", "xgboost"], "accent": "#e8590c"},
                    {"id": "m6", "title": "6 · Clustering",
                     "sub": "K-means\nhierarchical",
                     "icons": ["scikitlearn", "scipy"], "accent": "#9c36b5"},
                    {"id": "m7", "title": "7 · Neural nets",
                     "sub": "ANN · CNN\nchurn · images",
                     "icons": ["tensorflow", "keras"], "accent": DL},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------ 03 --
    {
        "slug": "02-powerbi-flow",
        "name": "Power BI report: from sources to a navigable six-page report",
        "caption": "Power BI demo | 36 tables, 37 measures, 6 report pages",
        "out": "assets/diagrams/02-powerbi-flow",
        "width": 1400,
        "node_w": 190,
        "rows": [
            {
                "band": "REPORT PIPELINE",
                "nodes": [
                    {"id": "src", "title": "Sources",
                     "sub": "Excel · CSV\nretail sample",
                     "icons": ["excel", "csv"], "accent": "#217346"},
                    {"id": "pq", "title": "Power Query",
                     "sub": "shape · clean\ncombine queries",
                     "icons": ["powerbi"], "accent": PBI_TEAL},
                    {"id": "model", "title": "Data model",
                     "sub": "36 tables\n5 dims · 2 facts",
                     "icons": ["powerbi", "excel"], "accent": DOC},
                    {"id": "dax", "title": "DAX measures",
                     "sub": "iterators · rank\nTREATAS · what-if",
                     "icons": ["dax"], "accent": PBI},
                    {"id": "pages", "title": "Report pages",
                     "sub": "6 pages · 1280×720\n160 visuals",
                     "icons": ["powerbi", "chiclet"], "accent": "#e8a33d"},
                    {"id": "nav", "title": "Navigation",
                     "sub": "5 bookmarks\nfilter reset",
                     "icons": ["powerbi"], "accent": PBI_TEAL},
                ],
                "edges": [("src", "pq", "import"), ("pq", "model", "load"),
                          ("model", "dax", "relate"), ("dax", "pages", "render"),
                          ("pages", "nav", "wire")],
            },
        ],
    },

    # ------------------------------------------------------------------ 04 --
    {
        "slug": "02-powerbi-star-schema",
        "name": "Power BI data model: five dimensions, two fact tables, one measure table",
        "caption": "Data model | star schema around the two fact tables",
        "out": "assets/diagrams/02-powerbi-star-schema",
        "width": 1140,
        "height": 552,
        "rows": [
            {
                "fixed": True,
                "nodes": [
                    {"id": "cal", "title": "Calendar", "sub": "date dimension",
                     "icons": ["dim"], "accent": PBI_TEAL, "x": 60, "y": 60, "w": 200},
                    {"id": "cust", "title": "Customer Lookup", "sub": "customer attributes",
                     "icons": ["dim"], "accent": PBI_TEAL, "x": 60, "y": 230, "w": 200},
                    {"id": "store", "title": "Store Lookup", "sub": "store · geo · lat/long",
                     "icons": ["dim"], "accent": PBI_TEAL, "x": 60, "y": 400, "w": 200},
                    {"id": "sales", "title": "Sales by Store", "sub": "fact · transactions",
                     "icons": ["powerbi"], "accent": "#e8a33d", "x": 470, "y": 110, "w": 200},
                    {"id": "food", "title": "Food Inventory", "sub": "fact · stock · unsold",
                     "icons": ["powerbi"], "accent": "#e8a33d", "x": 470, "y": 330, "w": 200},
                    {"id": "prod", "title": "Product Lookup", "sub": "product hierarchy",
                     "icons": ["dim"], "accent": PBI_TEAL, "x": 870, "y": 60, "w": 200},
                    {"id": "emp", "title": "Employee Lookup", "sub": "staff dimension",
                     "icons": ["dim"], "accent": PBI_TEAL, "x": 870, "y": 230, "w": 200},
                    {"id": "meas", "title": "Measure Table", "sub": "28 measures\n+ 9 what-if / table",
                     "icons": ["dax"], "accent": PBI, "x": 870, "y": 400, "w": 200},
                ],
            },
        ],
        "connectors": [
            {"from": (0, 0), "to": (0, 3)}, {"from": (0, 0), "to": (0, 4)},
            {"from": (0, 1), "to": (0, 3)},
            {"from": (0, 2), "to": (0, 3)}, {"from": (0, 2), "to": (0, 4)},
            {"from": (0, 5), "to": (0, 3)}, {"from": (0, 5), "to": (0, 4)},
            {"from": (0, 6), "to": (0, 3)},
            {"from": (0, 7), "to": (0, 3)},
        ],
    },

    # ------------------------------------------------------------------ 05 --
    {
        "slug": "03-de-etl-flow",
        "name": "Data engineering stack: sources to serving, with quality and CI/CD",
        "caption": "Data engineering | ETL / ELT stack across the seven projects",
        "out": "assets/diagrams/03-de-etl-flow",
        "width": 1400,
        "node_w": 186,
        "rows": [
            {
                "band": "QUALITY, DELIVERY, OBSERVABILITY",
                "nodes": [
                    {"id": "ci", "title": "CI / CD",
                     "sub": "lint · test · deploy",
                     "icons": ["githubactions", "docker", "sqlfluff"], "accent": CI},
                    {"id": "dq", "title": "Data quality",
                     "sub": "unit + data tests",
                     "icons": ["pytest", "soda"], "accent": QUALITY},
                    {"id": "obs", "title": "Monitoring",
                     "sub": "lag · freshness · DLQ",
                     "icons": ["dlq", "streamlit"], "accent": "#b3261e"},
                ],
            },
            {
                "band": "INGEST → WAREHOUSE → SERVE",
                "nodes": [
                    {"id": "src", "title": "Sources",
                     "sub": "YouTube API v3\nKafka · CSV",
                     "icons": ["requests", "apachekafka", "csv"], "accent": SLATE},
                    {"id": "ing", "title": "Ingestion",
                     "sub": "extract · validate\nland raw",
                     "icons": ["python"], "accent": PY},
                    {"id": "orc", "title": "Orchestration",
                     "sub": "Airflow DAGs\nDatabricks jobs",
                     "icons": ["apacheairflow", "databricks"], "accent": AIRFLOW},
                    {"id": "wh", "title": "Warehouse",
                     "sub": "PostgreSQL · DuckDB\nDelta Lake",
                     "icons": ["postgresql", "duckdb", "deltalake"], "accent": PG},
                    {"id": "tr", "title": "Transformation",
                     "sub": "dbt models\nPySpark jobs",
                     "icons": ["dbt", "apachespark"], "accent": DBT},
                    {"id": "srv", "title": "Serving",
                     "sub": "Streamlit dashboards\nPlotly charts",
                     "icons": ["streamlit", "plotly"], "accent": STREAM},
                ],
                "edges": [("src", "ing", "extract"), ("ing", "orc", "schedule"),
                          ("orc", "wh", "land"), ("wh", "tr", "transform"),
                          ("tr", "srv", "serve")],
            },
        ],
        "links": [
            {"from": (0, 0), "to": (1, 2), "label": "deploys", "dashed": True},
            {"from": (0, 1), "to": (1, 4), "label": "validates", "dashed": True},
            {"from": (0, 2), "to": (1, 5), "label": "watches", "dashed": True},
        ],
    },

    # ------------------------------------------------------------------ 06 --
    {
        "slug": "03-de-project-map",
        "name": "The seven data engineering projects and their stacks",
        "caption": "Seven projects | what each one is built with",
        "out": "assets/diagrams/03-de-project-map",
        "width": 1440,
        "node_w": 176,
        "rows": [
            {
                "band": "PROJECTS",
                "nodes": [
                    {"id": "p1", "title": "1 · ELT",
                     "sub": "YouTube API →\nPostgreSQL",
                     "icons": ["apacheairflow", "docker", "postgresql"], "accent": AIRFLOW},
                    {"id": "p2", "title": "2 · Warehouse",
                     "sub": "dbt marts ·\nKPI dashboard",
                     "icons": ["duckdb", "dbt", "streamlit"], "accent": "#e0b400"},
                    {"id": "p3", "title": "3 · Supplement",
                     "sub": "merge 4 CSVs\ninto one table",
                     "icons": ["pandas", "csv", "notebook"], "accent": PANDA},
                    {"id": "p4", "title": "4 · Databricks",
                     "sub": "DLT · Unity Catalog\nDelta Lake",
                     "icons": ["databricks", "deltalake", "apachespark"], "accent": DBX},
                    {"id": "p5", "title": "5 · Retail",
                     "sub": "ETL + validation\nfor holiday demand",
                     "icons": ["postgresql", "parquet", "pandas"], "accent": PG},
                    {"id": "p6", "title": "6 · Workflows",
                     "sub": "PySpark order\ncleaning",
                     "icons": ["apachespark", "parquet"], "accent": SPARK},
                    {"id": "p7", "title": "7 · Streaming",
                     "sub": "Kafka → warehouse\nwith replay proof",
                     "icons": ["apachekafka", "postgresql", "dbt"], "accent": KAFKA},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------ 07 --
    {
        "slug": "04-genai-flow",
        "name": "Generative AI stack: clients, orchestration, tools and models",
        "caption": "Generative AI | clients → orchestration → tools → models",
        "out": "assets/diagrams/04-genai-flow",
        "width": 1400,
        "node_w": 210,
        "rows": [
            {
                "band": "APPLICATION STACK",
                "nodes": [
                    {"id": "ui", "title": "Clients",
                     "sub": "Streamlit · Gradio\nDjango · Tkinter",
                     "icons": ["streamlit", "gradio", "tkinter"], "accent": STREAM},
                    {"id": "api", "title": "API layer",
                     "sub": "Django REST\nPostman tests",
                     "icons": ["django", "postman"], "accent": DJANGO},
                    {"id": "orch", "title": "Orchestration",
                     "sub": "chains · RAG\ncrews · agent teams",
                     "icons": ["langchain", "llamaindex", "crewai"], "accent": FRAME},
                    {"id": "tools", "title": "Tools & memory",
                     "sub": "MCP servers · Chroma\nTavily · SQLite",
                     "icons": ["mcp", "chromadb", "tavily"], "accent": "#7b4bff"},
                    {"id": "models", "title": "Models",
                     "sub": "Gemini 2.0 Flash\nHF · tinyllama",
                     "icons": ["googlegemini", "huggingface", "ollama"], "accent": GEN},
                ],
                "edges": [("ui", "api", "HTTP"), ("api", "orch", "invoke"),
                          ("orch", "tools", "call"), ("tools", "models", "ground")],
            },
        ],
    },

    # ------------------------------------------------------------------ 08 --
    {
        "slug": "04-agent-patterns",
        "name": "Google ADK agent patterns: sequential, parallel and loop",
        "caption": "Agent patterns | the three ADK control-flow primitives",
        "out": "assets/diagrams/04-agent-patterns",
        "width": 1200,
        "node_w": 200,
        "rows": [
            {
                "band": "SEQUENTIAL AGENT · FIXED ORDER",
                "nodes": [
                    {"id": "v", "title": "validator",
                     "sub": "checks the input",
                     "icons": ["googlegemini"], "accent": "#1a73e8"},
                    {"id": "s", "title": "scorer",
                     "sub": "scores the lead",
                     "icons": ["googlegemini"], "accent": "#1a73e8"},
                    {"id": "r", "title": "recommender",
                     "sub": "writes the plan",
                     "icons": ["googlegemini"], "accent": "#1a73e8"},
                ],
                "edges": [("v", "s", "next"), ("s", "r", "next")],
            },
            {
                "band": "PARALLEL AGENT · FAN-OUT, THEN SYNTHESISE",
                "nodes": [
                    {"id": "info", "title": "CPU · disk · memory",
                     "sub": "three sub-agents\nrun at once",
                     "icons": ["python", "sqlite"], "accent": QUALITY},
                    {"id": "syn", "title": "synthesizer",
                     "sub": "merges the reports",
                     "icons": ["googlegemini"], "accent": "#1a73e8"},
                ],
                "edges": [("info", "syn", "reports")],
            },
            {
                "band": "LOOP AGENT · ITERATE UNTIL ACCEPTED",
                "nodes": [
                    {"id": "g", "title": "generator",
                     "sub": "drafts the post",
                     "icons": ["googlegemini"], "accent": "#188038"},
                    {"id": "f", "title": "refiner",
                     "sub": "tightens wording",
                     "icons": ["googlegemini"], "accent": "#188038"},
                    {"id": "rev", "title": "reviewer",
                     "sub": "accepts or rejects",
                     "icons": ["googlegemini"], "accent": "#188038"},
                ],
                "edges": [("g", "f", "next"), ("f", "rev", "next"),
                          ("rev", "g", "revise")],
            },
        ],
    },

    # ------------------------------------------------------------------ 09 --
    {
        "slug": "elt-architecture",
        "name": "YouTube API ELT pipeline: API to PostgreSQL warehouse",
        "caption": "Project 1 | ELT with Python, Docker and Apache Airflow",
        "out": "3. Data Engineering Projects/1. ELT pipeline utilizing Python, Docker, and Apache Airflow/images/elt-architecture",
        "width": 1240,
        "node_w": 178,
        "rows": [
            {
                "band": "ELT FLOW",
                "nodes": [
                    {"id": "api", "title": "YouTube API v3",
                     "sub": "channel + video\nmetrics",
                     "icons": ["requests"], "accent": SLATE},
                    {"id": "py", "title": "Python extract",
                     "sub": "modular scripts\nstaging schema",
                     "icons": ["python"], "accent": PY},
                    {"id": "af", "title": "Airflow DAG",
                     "sub": "scheduled tasks\nDockerised",
                     "icons": ["apacheairflow", "docker"], "accent": AIRFLOW},
                    {"id": "pg", "title": "PostgreSQL",
                     "sub": "staging → core\nincremental upserts",
                     "icons": ["postgresql"], "accent": PG},
                    {"id": "dq", "title": "Quality checks",
                     "sub": "Soda + pytest",
                     "icons": ["soda", "pytest"], "accent": QUALITY},
                    {"id": "ci", "title": "GitHub Actions",
                     "sub": "build · test\ndeploy",
                     "icons": ["githubactions"], "accent": CI},
                ],
                "edges": [("api", "py", "extract"), ("py", "af", "schedule"),
                          ("af", "pg", "load"), ("pg", "dq", "validate"),
                          ("dq", "ci", "gate")],
            },
        ],
    },

    # ------------------------------------------------------------------ 10 --
    {
        "slug": "dwh-architecture",
        "name": "DuckDB warehouse: ingestion, dbt models, Streamlit dashboard",
        "caption": "Project 2 | DuckDB + dbt + Streamlit with CI/CD",
        "out": "3. Data Engineering Projects/2. Data Warehouse designed using DuckDB and Streamlit with CI-CD automation/images/dwh-architecture",
        "width": 1240,
        "node_w": 190,
        "rows": [
            {
                "band": "CI / CD · GITHUB ACTIONS",
                "nodes": [
                    {"id": "lint", "title": "sqlfluff",
                     "sub": "SQL lint", "icons": ["sqlfluff"], "accent": QUALITY},
                    {"id": "seed", "title": "Ingestion run",
                     "sub": "seeds raw schema", "icons": ["python"], "accent": PY},
                    {"id": "build", "title": "dbt build",
                     "sub": "compile + test", "icons": ["dbt"], "accent": DBT},
                ],
            },
            {
                "band": "LOCAL WAREHOUSE",
                "nodes": [
                    {"id": "gen", "title": "ingestion.py",
                     "sub": "mock customers\norders · events",
                     "icons": ["python"], "accent": PY},
                    {"id": "raw", "title": "DuckDB raw",
                     "sub": "dev.duckdb",
                     "icons": ["duckdb"], "accent": "#c9a200"},
                    {"id": "stg", "title": "dbt staging",
                     "sub": "stg_customers\nstg_orders · stg_events",
                     "icons": ["dbt"], "accent": DBT},
                    {"id": "mart", "title": "dbt marts",
                     "sub": "dim_customers\nfct_orders",
                     "icons": ["dbt", "duckdb"], "accent": "#e05c4b"},
                    {"id": "dash", "title": "Streamlit",
                     "sub": "KPIs · Plotly charts",
                     "icons": ["streamlit", "plotly"], "accent": STREAM},
                ],
                "edges": [("gen", "raw", "load"), ("raw", "stg", "model"),
                          ("stg", "mart", "build"), ("mart", "dash", "serve")],
            },
        ],
        "links": [
            {"from": (0, 0), "to": (1, 2), "label": "lint", "dashed": True},
            {"from": (0, 2), "to": (1, 3), "label": "build", "dashed": True},
        ],
    },

    # ------------------------------------------------------------------ 11 --
    {
        "slug": "supplement-merge",
        "name": "Supplement experiments: four sources merged into one table",
        "caption": "Project 3 | four CSVs → one analysis-ready DataFrame",
        "out": "3. Data Engineering Projects/3. Data Engineering Pipeline for Supplement Experiments/images/merge-flow",
        "width": 1180,
        "node_w": 200,
        "rows": [
            {
                "band": "SOURCE FILES",
                "nodes": [
                    {"id": "health", "title": "user_health_data",
                     "sub": "wearable metrics\nper user per day",
                     "icons": ["csv"], "accent": SLATE},
                    {"id": "sup", "title": "supplement_usage",
                     "sub": "one row per\nintake event",
                     "icons": ["csv"], "accent": SLATE},
                    {"id": "exp", "title": "experiments",
                     "sub": "experiment\nmetadata",
                     "icons": ["csv"], "accent": SLATE},
                    {"id": "prof", "title": "user_profiles",
                     "sub": "demographics",
                     "icons": ["csv"], "accent": SLATE},
                ],
            },
            {
                "band": "ONE FUNCTION · merge_all_data()",
                "nodes": [
                    {"id": "load", "title": "Extract",
                     "sub": "read_csv ×4\nparse dates",
                     "icons": ["pandas"], "accent": PANDA},
                    {"id": "merge", "title": "Merge",
                     "sub": "join on user_id,\ndate, experiment_id",
                     "icons": ["pandas"], "accent": PANDA},
                    {"id": "transform", "title": "Transform",
                     "sub": "age groups\nmg → g · No intake",
                     "icons": ["pandas", "numpy"], "accent": "#e8590c"},
                    {"id": "out", "title": "One row per user/day",
                     "sub": "12 columns\nanalysis-ready",
                     "icons": ["notebook"], "accent": "#f37626"},
                ],
                "edges": [("load", "merge", "join"), ("merge", "transform", "clean"),
                          ("transform", "out", "return")],
            },
        ],
        "links": [
            {"from": (0, 0), "to": (1, 0), "label": "read", "dashed": True},
            {"from": (0, 3), "to": (1, 1), "label": "read", "dashed": True},
        ],
    },

    # ------------------------------------------------------------------ 12 --
    {
        "slug": "databricks-projects",
        "name": "Databricks projects: advanced examples, CDC ETL, declarative SQL",
        "caption": "Project 4 | three Databricks / Delta Live Tables projects",
        "out": "3. Data Engineering Projects/4. Databricks Projects/images/project-map",
        "width": 1200,
        "node_w": 250,
        "rows": [
            {
                "band": "PROJECTS",
                "nodes": [
                    {"id": "adv", "title": "1 · Advanced examples",
                     "sub": "bundles · privacy\nperformance · streaming",
                     "icons": ["databricks", "githubactions"], "accent": DBX},
                    {"id": "cdc", "title": "2 · CDC ETL",
                     "sub": "AUTO CDC · CDF\nmedallion in DLT SQL",
                     "icons": ["deltalake", "autoloader"], "accent": "#00add4"},
                    {"id": "sql", "title": "3 · Simple SQL ETL",
                     "sub": "read_files → songs_raw\n→ prepared tables",
                     "icons": ["databricks", "apachespark"], "accent": "#ff6f00"},
                ],
                "edges": [("adv", "cdc", "next"), ("cdc", "sql", "next")],
            },
        ],
    },

    # ------------------------------------------------------------------ 13 --
    {
        "slug": "databricks-modules",
        "name": "Advanced Databricks examples: four workshop modules",
        "caption": "Project 4.1 | four modules, demo + lab notebooks",
        "out": "3. Data Engineering Projects/4. Databricks Projects/1. Advanced Databricks Data Engineering Examples/images/modules",
        "width": 1240,
        "node_w": 260,
        "rows": [
            {
                "band": "MODULES",
                "nodes": [
                    {"id": "dab", "title": "Asset Bundles",
                     "sub": "package · deploy\nversion-control jobs",
                     "icons": ["databricks", "githubactions"], "accent": DBX},
                    {"id": "priv", "title": "Data Privacy",
                     "sub": "grants · masks\npseudonymisation · CDF",
                     "icons": ["unitycatalog", "deltalake"], "accent": "#1b3139"},
                    {"id": "perf", "title": "Performance",
                     "sub": "liquid clustering\nshuffles · UDFs",
                     "icons": ["apachespark", "deltalake"], "accent": "#e25a1c"},
                    {"id": "str", "title": "Streaming",
                     "sub": "Auto Loader\nwatermarks · DLT",
                     "icons": ["autoloader", "apachespark"], "accent": "#ff3621"},
                ],
            },
        ],
    },

    # ------------------------------------------------------------------ 14 --
    {
        "slug": "bundle-flow",
        "name": "Databricks Asset Bundles: validate, deploy, run",
        "caption": "Asset Bundles | bundle as code, one definition per environment",
        "out": "3. Data Engineering Projects/4. Databricks Projects/1. Advanced Databricks Data Engineering Examples/Automated deployment with Databricks Asset Bundles/images/bundle-flow",
        "width": 1200,
        "node_w": 210,
        "rows": [
            {
                "band": "BUNDLE LIFECYCLE",
                "nodes": [
                    {"id": "src", "title": "databricks.yml",
                     "sub": "jobs · pipelines\nnotebooks",
                     "icons": ["databricks"], "accent": DBX},
                    {"id": "val", "title": "bundle validate",
                     "sub": "schema + config\ncheck",
                     "icons": ["databricks"], "accent": "#ff6f60"},
                    {"id": "dep", "title": "bundle deploy",
                     "sub": "dev · staging\nproduction targets",
                     "icons": ["databricks", "githubactions"], "accent": CI},
                    {"id": "run", "title": "bundle run",
                     "sub": "workflow / job\nexecutes",
                     "icons": ["databricks", "apachespark"], "accent": "#e25a1c"},
                ],
                "edges": [("src", "val", "check"), ("val", "dep", "promote"),
                          ("dep", "run", "execute")],
            },
        ],
    },

    # ------------------------------------------------------------------ 15 --
    {
        "slug": "privacy-flow",
        "name": "Databricks data privacy: grants, masking, pseudonymisation, CDF",
        "caption": "Data privacy | protect PII, then propagate changes safely",
        "out": "3. Data Engineering Projects/4. Databricks Projects/1. Advanced Databricks Data Engineering Examples/Databricks Data Privacy/images/privacy-flow",
        "width": 1240,
        "node_w": 190,
        "rows": [
            {
                "band": "GOVERNANCE PIPELINE",
                "nodes": [
                    {"id": "pii", "title": "Raw PII tables",
                     "sub": "names · emails\nuser attributes",
                     "icons": ["deltalake"], "accent": "#1b3139"},
                    {"id": "uc", "title": "Unity Catalog",
                     "sub": "catalogs · schemas\nleast-privilege grants",
                     "icons": ["unitycatalog"], "accent": "#0b7285"},
                    {"id": "mask", "title": "Masks & filters",
                     "sub": "column masks\nrow filters · views",
                     "icons": ["unitycatalog", "deltalake"], "accent": "#5f3dc4"},
                    {"id": "pseudo", "title": "Pseudonymise",
                     "sub": "lookup table\nid → surrogate",
                     "icons": ["deltalake"], "accent": "#c2255c"},
                    {"id": "anon", "title": "Anonymise",
                     "sub": "age buckets\nnon-identifying",
                     "icons": ["deltalake"], "accent": "#e8590c"},
                    {"id": "cdf", "title": "Propagate with CDF",
                     "sub": "Change Data Feed\n→ downstream",
                     "icons": ["deltalake", "apachespark"], "accent": "#00add4"},
                ],
                "edges": [("pii", "uc", "secure"), ("uc", "mask", "restrict"),
                          ("mask", "pseudo", "hide"), ("pseudo", "anon", "aggregate"),
                          ("anon", "cdf", "publish")],
            },
        ],
    },

    # ------------------------------------------------------------------ 16 --
    {
        "slug": "perf-flow",
        "name": "Databricks performance: small files, clustering, shuffles, UDFs",
        "caption": "Performance | diagnose, then fix the five usual suspects",
        "out": "3. Data Engineering Projects/4. Databricks Projects/1. Advanced Databricks Data Engineering Examples/Databricks Performance Optimization/images/perf-flow",
        "width": 1240,
        "node_w": 200,
        "rows": [
            {
                "band": "OPTIMISATION LADDER",
                "nodes": [
                    {"id": "small", "title": "File explosion",
                     "sub": "many small\nwrites",
                     "icons": ["deltalake"], "accent": "#c92a2a"},
                    {"id": "opt", "title": "OPTIMIZE",
                     "sub": "compact files\nstatistics",
                     "icons": ["deltalake", "apachespark"], "accent": "#e8590c"},
                    {"id": "clu", "title": "Liquid clustering",
                     "sub": "prune files\nat query time",
                     "icons": ["deltalake"], "accent": "#00add4"},
                    {"id": "shuf", "title": "Shuffle control",
                     "sub": "AQE · broadcast\npartitioning",
                     "icons": ["apachespark"], "accent": "#e25a1c"},
                    {"id": "udf", "title": "Vectorised UDFs",
                     "sub": "native > python\n> pandas UDF",
                     "icons": ["apachespark"], "accent": "#ff6f00"},
                    {"id": "fast", "title": "Faster queries",
                     "sub": "measured in\nSpark UI",
                     "icons": ["databricks"], "accent": "#2f9e44"},
                ],
                "edges": [("small", "opt", "compact"), ("opt", "clu", "cluster"),
                          ("clu", "shuf", "less IO"), ("shuf", "udf", "less CPU"),
                          ("udf", "fast", "measure")],
            },
        ],
    },

    # ------------------------------------------------------------------ 17 --
    {
        "slug": "streaming-flow",
        "name": "Databricks streaming: Auto Loader to a bronze/silver/gold pipeline",
        "caption": "Streaming | Auto Loader, watermarks, DLT expectations",
        "out": "3. Data Engineering Projects/4. Databricks Projects/1. Advanced Databricks Data Engineering Examples/Databricks Streaming/images/streaming-flow",
        "width": 1200,
        "node_w": 200,
        "rows": [
            {
                "band": "MEDALLION PIPELINE",
                "nodes": [
                    {"id": "files", "title": "Landing files",
                     "sub": "cloud storage\nor volume",
                     "icons": ["parquet"], "accent": SLATE},
                    {"id": "al", "title": "Auto Loader",
                     "sub": "incremental\nfile discovery",
                     "icons": ["autoloader", "apachespark"], "accent": "#ff3621"},
                    {"id": "bronze", "title": "bronze_*",
                     "sub": "raw · append-only\nstreaming tables",
                     "icons": ["deltalake"], "accent": "#8d6e63"},
                    {"id": "silver", "title": "silver_*",
                     "sub": "cleansed · deduped\nexpectations enforced",
                     "icons": ["deltalake", "apachespark"], "accent": "#607d8b"},
                    {"id": "gold", "title": "gold_*",
                     "sub": "aggregated\nanalysis-ready",
                     "icons": ["deltalake", "databricks"], "accent": "#c9a227"},
                ],
                "edges": [("files", "al", "discover"), ("al", "bronze", "stream"),
                          ("bronze", "silver", "clean"), ("silver", "gold", "aggregate")],
            },
        ],
    },

    # ------------------------------------------------------------------ 18 --
    {
        "slug": "cdc-flow",
        "name": "Change data capture: bronze CDF, AUTO CDC, silver and gold",
        "caption": "CDC ETL | APPLY CHANGES keeps current state plus full history",
        "out": "3. Data Engineering Projects/4. Databricks Projects/2. Databricks ETL workflow with Change Data Capture/images/cdc-flow",
        "width": 1240,
        "node_w": 200,
        "rows": [
            {
                "band": "DELTA LIVE TABLES · SQL",
                "nodes": [
                    {"id": "raw", "title": "Raw change events",
                     "sub": "raw_orders\nraw_customers",
                     "icons": ["csv"], "accent": SLATE},
                    {"id": "bronze", "title": "bronze_*_cdc",
                     "sub": "streaming tables\nCDF enabled",
                     "icons": ["deltalake", "autoloader"], "accent": "#8d6e63"},
                    {"id": "auto", "title": "APPLY CHANGES",
                     "sub": "KEYS order_id\nSEQUENCE BY ingestion_ts",
                     "icons": ["deltalake"], "accent": "#00add4"},
                    {"id": "silver", "title": "silver_orders",
                     "sub": "current state\n+ enriched",
                     "icons": ["deltalake", "apachespark"], "accent": "#607d8b"},
                    {"id": "gold", "title": "gold_sales",
                     "sub": "revenue by\ncountry",
                     "icons": ["deltalake", "databricks"], "accent": "#c9a227"},
                ],
                "edges": [("raw", "bronze", "ingest"), ("bronze", "auto", "keys"),
                          ("auto", "silver", "dedupe"), ("silver", "gold", "aggregate")],
            },
        ],
    },

    # ------------------------------------------------------------------ 19 --
    {
        "slug": "dlt-sql-flow",
        "name": "Simple DLT SQL pipeline: read_files to derived tables",
        "caption": "Simple SQL ETL | streaming table plus derived tables",
        "out": "3. Data Engineering Projects/4. Databricks Projects/3. Simple Databricks ETL workflow with SQL/images/dlt-sql-flow",
        "width": 1100,
        "node_w": 210,
        "rows": [
            {
                "band": "PIPELINE",
                "nodes": [
                    {"id": "src", "title": "Million Song Dataset",
                     "sub": "/databricks-datasets\n/songs",
                     "icons": ["parquet"], "accent": SLATE},
                    {"id": "raw", "title": "songs_raw",
                     "sub": "STREAM read_files\nstreaming table",
                     "icons": ["autoloader", "deltalake"], "accent": "#ff3621"},
                    {"id": "prep", "title": "songs_prepared",
                     "sub": "artist · title\ntempo · signature",
                     "icons": ["deltalake", "apachespark"], "accent": "#607d8b"},
                    {"id": "top", "title": "top_artists_by_year",
                     "sub": "songs per artist\nper year",
                     "icons": ["deltalake", "databricks"], "accent": "#c9a227"},
                ],
                "edges": [("src", "raw", "read"), ("raw", "prep", "clean"),
                          ("prep", "top", "group")],
            },
        ],
    },

    # ------------------------------------------------------------------ 20 --
    {
        "slug": "retail-pipeline",
        "name": "Retail data pipeline: PostgreSQL and Parquet to clean and aggregated CSV",
        "caption": "Project 5 | extract, transform, aggregate, load, validate",
        "out": "3. Data Engineering Projects/5. Project Building a Retail Data Pipeline/images/pipeline-flow",
        "width": 1240,
        "node_w": 200,
        "rows": [
            {
                "band": "SOURCES",
                "nodes": [
                    {"id": "pg", "title": "grocery_sales",
                     "sub": "PostgreSQL table\nweekly sales",
                     "icons": ["postgresql"], "accent": PG},
                    {"id": "parquet", "title": "extra_data.parquet",
                     "sub": "CPI · unemployment\nkeyed by index",
                     "icons": ["parquet"], "accent": "#0e7490"},
                ],
            },
            {
                "band": "PIPELINE FUNCTIONS",
                "nodes": [
                    {"id": "extract", "title": "extract()",
                     "sub": "read + merge\non index",
                     "icons": ["pandas"], "accent": PANDA},
                    {"id": "transform", "title": "transform()",
                     "sub": "impute means\nparse Date · Month",
                     "icons": ["pandas"], "accent": "#e8590c"},
                    {"id": "agg", "title": "avg_weekly_\nsales_per_month()",
                     "sub": "groupby → agg\n→ round",
                     "icons": ["pandas", "numpy"], "accent": "#9c36b5"},
                    {"id": "load", "title": "load()",
                     "sub": "clean_data.csv\nagg_data.csv",
                     "icons": ["csv"], "accent": SLATE},
                    {"id": "valid", "title": "validation()",
                     "sub": "fails if an output\nfile is missing",
                     "icons": ["pytest"], "accent": QUALITY},
                ],
                "edges": [("extract", "transform", "clean"), ("transform", "agg", "aggregate"),
                          ("agg", "load", "write"), ("load", "valid", "check")],
            },
        ],
        "links": [
            {"from": (0, 0), "to": (1, 0), "label": "query", "dashed": True,
             "target_x": 0.3},
            {"from": (0, 1), "to": (1, 0), "label": "read", "dashed": True,
             "target_x": 0.72},
        ],
    },

    # ------------------------------------------------------------------ 21 --
    {
        "slug": "workflow-card",
        "name": "Simple workflows: Parquet in, cleaned Parquet out",
        "caption": "Project 6 | one focused workflow",
        "out": "3. Data Engineering Projects/6. Simple workflows/images/workflow-card",
        "width": 1000,
        "node_w": 220,
        "rows": [
            {
                "band": "SINGLE-PURPOSE WORKFLOW",
                "nodes": [
                    {"id": "in", "title": "orders_data.parquet",
                     "sub": "one row per order",
                     "icons": ["parquet"], "accent": "#0e7490"},
                    {"id": "spark", "title": "PySpark cleaning",
                     "sub": "business rules\nfrom the ML team",
                     "icons": ["apachespark"], "accent": "#e25a1c"},
                    {"id": "out", "title": "orders_data_clean",
                     "sub": "forecast-ready\nParquet",
                     "icons": ["parquet", "notebook"], "accent": "#2f9e44"},
                ],
                "edges": [("in", "spark", "read"), ("spark", "out", "overwrite")],
            },
        ],
    },

    # ------------------------------------------------------------------ 22 --
    {
        "slug": "cleaning-flow",
        "name": "PySpark order cleaning: night orders out, states derived",
        "caption": "Project 6.1 | clean Voltmart orders for demand forecasting",
        "out": "3. Data Engineering Projects/6. Simple workflows/Cleaning data with Pyspark/images/cleaning-flow",
        "width": 1240,
        "node_w": 200,
        "rows": [
            {
                "band": "CLEANING RULES",
                "nodes": [
                    {"id": "raw", "title": "orders_data.parquet",
                     "sub": "order history\nlast year",
                     "icons": ["parquet"], "accent": "#0e7490"},
                    {"id": "night", "title": "Drop night orders",
                     "sub": "00:00–05:00 out\n+ time_of_day",
                     "icons": ["apachespark"], "accent": "#e25a1c"},
                    {"id": "lower", "title": "Normalise product",
                     "sub": "lowercase\nremove TVs",
                     "icons": ["apachespark"], "accent": "#ff6f00"},
                    {"id": "state", "title": "Derive state",
                     "sub": "split address\n→ purchase_state",
                     "icons": ["apachespark"], "accent": "#e8590c"},
                    {"id": "out", "title": "orders_data_clean",
                     "sub": "typed · lowercase\noverwrite",
                     "icons": ["parquet", "notebook"], "accent": "#2f9e44"},
                ],
                "edges": [("raw", "night", "filter"), ("night", "lower", "clean"),
                          ("lower", "state", "parse"), ("state", "out", "write")],
            },
        ],
    },

    # ------------------------------------------------------------------ 23 --
    {
        "slug": "kafka-pipeline",
        "name": "Streaming pipeline: Kafka to PostgreSQL warehouse with dbt and monitoring",
        "caption": "Project 7 | Kafka → warehouse, exactly-once as observed",
        "out": "3. Data Engineering Projects/7. Streaming Pipeline - Kafka to Data Warehouse/images/pipeline-flow",
        "width": 1440,
        "node_w": 190,
        "rows": [
            {
                "band": "TRANSPORT, FAILURE PATHS, OPERATIONS",
                "nodes": [
                    {"id": "kafka", "title": "Kafka (KRaft)",
                     "sub": "orders · payments\ncustomers.cdc",
                     "icons": ["apachekafka"], "accent": "#1f2b36"},
                    {"id": "dlq", "title": "DLQ & late events",
                     "sub": "raw.dlq\nraw.late_events",
                     "icons": ["dlq"], "accent": "#c0392b"},
                    {"id": "ops", "title": "ops schema",
                     "sub": "watermarks\npipeline metrics",
                     "icons": ["postgresql"], "accent": "#0b7285"},
                ],
            },
            {
                "band": "PIPELINE",
                "nodes": [
                    {"id": "prod", "title": "producer",
                     "sub": "acks=all\nidempotent",
                     "icons": ["apachekafka", "python"], "accent": "#3d3d3d"},
                    {"id": "load", "title": "stream-loader",
                     "sub": "guarded upsert\nschema validated",
                     "icons": ["python"], "accent": PY},
                    {"id": "raw", "title": "raw + landing",
                     "sub": "one row per record\ncurrent state",
                     "icons": ["postgresql"], "accent": PG},
                    {"id": "stg", "title": "dbt staging",
                     "sub": "typed views\nlate-arrival lookback",
                     "icons": ["dbt"], "accent": DBT},
                    {"id": "mart", "title": "dbt marts",
                     "sub": "fct_orders\ndim_customers · hourly",
                     "icons": ["dbt", "postgresql"], "accent": "#e05c4b"},
                    {"id": "dash", "title": "Streamlit",
                     "sub": "throughput · lag\nfreshness · DLQ",
                     "icons": ["streamlit"], "accent": STREAM},
                ],
                "edges": [("prod", "load", "JSON Schema"), ("load", "raw", "transaction"),
                          ("raw", "stg", "model"), ("stg", "mart", "build"),
                          ("mart", "dash", "read")],
            },
        ],
        "links": [
            {"from": (0, 0), "to": (1, 1), "label": "consumes", "dashed": True,
             "target_x": 0.3},
            {"from": (0, 1), "to": (1, 1), "label": "quarantine", "dashed": True,
             "target_x": 0.72},
            {"from": (0, 2), "to": (1, 5), "label": "feeds", "dashed": True},
        ],
    },
]
