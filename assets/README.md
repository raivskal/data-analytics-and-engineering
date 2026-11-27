# Assets

Icons and diagrams used by the README files in this repository.

```
assets/
├── icons/       one SVG per technology (brand colour baked in)
├── diagrams/    section-level diagrams, one .svg + one .drawio each
├── images/      screenshots used by the READMEs (e.g. the Power BI SUMMARY page)
└── README.md    this file
```

Per-project diagrams live next to their README instead, in `<project>/images/`,
so each project folder stays self-contained.

## How they are built

Everything here except the screenshots is generated from `tools/diagram_specs.py`
by `tools/build_diagrams.py`:

```bash
python tools/build_diagrams.py                # rebuild every diagram
python tools/build_diagrams.py --icons-only   # refresh assets/icons
python tools/build_diagrams.py --only 03-de-etl-flow
python tools/build_diagrams.py --refresh      # re-download every icon
```

Each diagram is emitted twice from the same layout:

* **`.svg`** — what the READMEs display. Every logo is inlined as vector paths,
  so the file has no external references at all: it renders the same on GitHub,
  on GitHub Pages, in VS Code preview, in print, and offline.
* **`.drawio`** — the editable version, for [app.diagrams.net](https://app.diagrams.net)
  or draw.io Desktop. Icons are referenced by URL there, so the file stays small.

To rasterise a diagram (for a slide deck, for example):

```bash
npm install @resvg/resvg-js
node -e "const{Resvg}=require('@resvg/resvg-js'),fs=require('fs'),f=process.argv[1];fs.writeFileSync(f.replace(/svg$/,'png'),new Resvg(fs.readFileSync(f,'utf8'),{fitTo:{mode:'zoom',value:2}}).render().asPng())" assets/diagrams/03-de-etl-flow.svg
```

## Icon sources and licences

| Source | Icons | Licence / note |
|---|---|---|
| [Simple Icons](https://simpleicons.org) (via `cdn.simpleicons.org`) | Python, pandas, NumPy, SciPy, scikit-learn, TensorFlow, Keras, Plotly, Jupyter, SQLite, Apache Airflow, Kafka, Spark, Databricks, Docker, PostgreSQL, DuckDB, Streamlit, pytest, GitHub Actions, LangChain, CrewAI, Hugging Face, Ollama, Django, Gradio, Postman, Google Gemini | Icon set released under CC0; the marks themselves are trademarks of their owners |
| [Iconify](https://iconify.design) — `devicon`, `logos`, `simple-icons`, `thesvg` sets | Power BI, dbt, matplotlib, seaborn, Excel, LlamaIndex | Each set keeps its own licence; logos are trademarks of their owners |
| Drawn for this repository | XGBoost, CatBoost, Delta Lake, Unity Catalog, Auto Loader, sqlfluff, Soda, Tavily, Chroma, DAX, DIM, SLICER, Tkinter, openpyxl, `requests`, CSV/Parquet, notebooks | Simple rounded tiles with a short label, used where no usable mark is published |

The logos are used here to identify the tools a project is built with. They
remain the property of their respective owners; nothing in this repository
grants a licence to reuse them.
