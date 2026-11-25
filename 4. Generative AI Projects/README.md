# Generative AI Projects

A hands-on tour of the generative-AI stack, from tool protocols and model APIs up to shipped apps. It starts with an MCP server and raw Hugging Face models, moves through LangChain/LlamaIndex retrieval and text-to-SQL, then into multi-agent frameworks (CrewAI, AutoGen, Google ADK), and finishes by serving it all through Django, Django REST, Streamlit and Tkinter.

Each folder is self-contained study material: notebooks plus the small datasets, PDFs and zipped projects they use.

---

## What is in here

| # | Folder | Focus | Core libraries | Model(s) |
|---|--------|-------|----------------|----------|
| 1 | `1. MCP example` | Exposing tools to an agent over the Model Context Protocol | `fastmcp`, `langchain-mcp-adapters` | Gemini 2.0 Flash |
| 2 | `2. Hugging Face` | Transformers pipelines, Gradio UIs, code agents | `transformers`, `gradio`, `smolagents`, `torch` | HF models + Gemini 2.0 Flash |
| 3 | `3. LangChain fundamentals. Text to SQL solutions` | Chains, document loading, SQL agents | `langchain`, `langchain-google-genai`, `sqlalchemy` | Gemini 2.0 Flash |
| 4 | `4. LlamaIndex and RAG` | Retrieval-augmented generation over documents | `llama-index`, `chromadb`, `tavily` | Gemini 2.0 Flash |
| 5 | `5. CrewAI and Multi Agent AI solutions` | Crews, tools, flows, hierarchical collaboration | `crewai`, `tavily-python` | Gemini 1.5 / 2.0 Flash |
| 6 | `6. AutoGen and Googe ADK` | Conversational agents and ADK multi-agent systems | `autogen`, `google-adk` | Gemini 2.0 Flash |
| 7 | `7. Django fundamentals with databases` | Django + SQLite, and a LangChain chatbot inside Django | `django`, `langchain-google-genai` | Gemini 2.0 Flash |
| 8 | `8. REST API with Django REST, Postman. Apps with Streamlit, React Native and Tkinter` | Serving agents over REST, plus Streamlit / Tkinter / console chat clients and a local-model RAG | `djangorestframework`, `streamlit`, `langchain-ollama`, `llama-index` | Gemini 1.5 Pro, `tinyllama` (Ollama) |

---

## 1. MCP example

`MCP.ipynb` builds a **Model Context Protocol** server with `FastMCP`, exposes its tools, and then consumes them from a LangChain agent using `langchain_mcp_adapters` — the pattern behind "let the model call my functions" without hard-coding each integration.

| File | What it does |
|------|--------------|
| `MCP.ipynb` | Define an MCP server with FastMCP → connect the client → bind the discovered tools to a Gemini 2.0 Flash agent |

**Concepts:** tool discovery at runtime, stdio transport between client and server, why MCP beats writing one bespoke tool wrapper per model.

---

## 2. Hugging Face

Three notebooks covering the "use open models directly" end of the spectrum.

| File | What it does |
|------|--------------|
| `HFTransformers.ipynb` | Hugging Face `transformers` **pipelines** end to end: `sentiment-analysis`, `summarization`, `question-answering`, `text-generation` (with `torch` and `datasets`) |
| `Gradio.ipynb` | Gradio UI patterns — `Interface`, `Blocks`, event listeners, and a `ChatInterface` chat backed by Gemini 2.0 Flash |
| `SmolAgents.ipynb` | `smolagents` **CodeAgent** and **ToolCallingAgent** with `InferenceClientModel`, wrapping the transformer pipelines as tools (notebook is written in Latvian: *Kodēšanas aģenti* = code agents) |
| `diabetes.csv` | Tabular dataset reused in this folder and in section 3 |

**Takeaway:** the same task can be solved by a hosted model (Gemini) or by a small local pipeline — the agent framework is what stays constant.

---

## 3. LangChain fundamentals. Text to SQL solutions

| File | What it does |
|------|--------------|
| `LangchainMU.ipynb` | Warm-up exercise: `PromptTemplate` with multiple input variables |
| `LangChain.ipynb` | Core LangChain building blocks with `ChatGoogleGenerativeAI` (Gemini 2.0 Flash), plus document loading — `PyPDFLoader` reads the three invoice PDFs (`invoice_1001329.pdf`, `invoice_2001321.pdf`, `invoice_3452334.pdf`) |
| `LangChainSQL.ipynb` | **Text-to-SQL agent**: load `diabetes.csv` into SQLite via `SQLDatabase`, expose `QuerySQLDataBaseTool`, and let the agent write and run the query |
| `diabetes.csv` | The table the SQL agent queries |

**Why it matters:** the SQL notebook is the canonical "ask a question in English, get a query" pattern — schema introspection, tool-constrained execution, and the model iterating until the query is valid.

---

## 4. LlamaIndex and RAG

`Llamaindex.ipynb` builds a retrieval-augmented pipeline over real documents.

| Content | Detail |
|---------|--------|
| `data.zip` → `data/` | `2023_canadian_budget.pdf`, `ag-studio.pdf`, `paul_graham_essay.txt` |
| Index | `SimpleDirectoryReader` → `VectorStoreIndex` persisted in **Chroma** |
| Retrieval | Query engine over the index, with **Tavily** available for web lookups |
| Model | Gemini 2.0 Flash |

**What it demonstrates:** ingestion → chunking → embeddings → vector store → retrieval → grounded answer, plus the hybrid pattern where the agent can also search the web when the documents do not contain the answer.

---

## 5. CrewAI and Multi Agent AI solutions

Five crew notebooks, one flows notebook, and a tools notebook — the widest folder in the section.

| File | Focus |
|------|-------|
| `1_research_write_article.ipynb` | Two-role crew: a researcher gathers material, a writer turns it into an article |
| `2_customer_support.ipynb` | Support crew handling customer inquiries |
| `3_tools_customer_outreach.ipynb` | Outreach crew where agents call **custom tools**; the briefs it works from are in `instructions.zip` |
| `4_tasks_event_planning.ipynb` | Event-planning crew using a **Chroma** vector store for retrieval |
| `5_collaboration_financial_analysis.ipynb` | Crew running with `Process.hierarchical` — a manager agent delegates to specialists |
| `CrewAI_flows.ipynb` | The deterministic counterpart: `Flow` objects plus `Process.sequential` for predictable, code-controlled pipelines |
| `Tavily.ipynb` | `TavilySearch` as a crew tool (a "Market Researcher" role) |
| `config.zip` | `config/agents.yaml` + `config/tasks.yaml` — YAML-defined crew (`poem_writer` role, `write_poem` task) |
| `instructions.zip` | `enterprise_solutions_framework.md`, `small_business_engagement.md`, `tech_startups_outreach.md` |

**The distinction worth internalising:** crews let agents decide *who does what*; flows let you decide. The folder shows both, because production systems usually need the second for the parts that must be reproducible.

---

## 6. AutoGen and Googe ADK

Two frameworks, one notebook plus eight small ADK projects.

**`AutoGen.ipynb`** — Microsoft AutoGen conversation patterns: `AssistantAgent` + `UserProxyAgent`, then team orchestration with `RoundRobinGroupChat` (fixed turn order) and `SelectorGroupChat` (a model picks the next speaker).

**`Google_ADK/`** — eight progressively harder agents built on `google.adk` with Gemini 2.0 Flash. Each folder is a runnable ADK app (`agent.py` + `__init__.py` + `.env`) and is launched with the ADK CLI.

| Folder | Agent | What it teaches |
|--------|-------|-----------------|
| `1/my_agent` | Minimal `LlmAgent` | The smallest possible ADK agent |
| `2/greeting_agent` | Greeting agent | Instructions/persona on a single agent |
| `3/tool_agent` | Tool-using agent | Attaching function tools the model can call |
| `4/manager` | Manager + 3 `sub_agents` (`funny_nerd`, `news_analyst`, `stock_analyst`) and `tools/tools.py` | Agent delegation — a coordinator routing to specialists |
| `5/lead_qualification_agent` | `SequentialAgent` with `validator` → `scorer` → `recommender` | A deterministic pipeline of agents |
| `6/system_monitor_agent` | `ParallelAgent` (CPU / disk / memory info agents, each with `tools.py`) → `synthesizer_agent` | Fan-out, then summarise |
| `7/linkedin_post_agent` | `LoopAgent` + `SequentialAgent`: generator → refiner → reviewer (reviewer has tools) | Iterate until a reviewer accepts |
| `8/question_answering_agent` | Q&A agent + `basic_stateful_session.py` | Session state and multi-turn memory |

**Pattern worth noting:** ADK's `SequentialAgent`, `ParallelAgent` and `LoopAgent` are the same three control-flow primitives as any workflow engine — the interesting part is that each node is an LLM.

---

## 7. Django fundamentals with databases

Two Django projects that put LLM code inside a real web app.

| Project | Contents |
|---------|----------|
| `Blog/` | Classic Django CRUD blog: `Category`, `Tag` and `Post` models with slug-based URLs, class-based views (`ListView`, `DetailView`, `CreateView`, `UpdateView`, `DeleteView`), templates (`post_list`, `post_detail`, `post_form`, `post_confirm_delete`, `category_detail`, `category_list`, `comment_form`), a custom template filter and SQLite |
| `DjangoChatBot/` | Chatbot inside Django: `chat/langchain_chat.py` calls Gemini 2.0 Flash through `ChatGoogleGenerativeAI`, converts the Markdown reply to HTML, and `chat/templates/chat.html` renders the conversation; key read from `settings.GOOGLE_API_KEY` (`.env`) |

```bash
cd "Blog"            # or "DjangoChatBot"
pip install django
python manage.py migrate
python manage.py runserver
```

For the chatbot, add `GOOGLE_API_KEY=...` to `.env` first — `settings.py` loads it at startup.

---

## 8. REST API with Django REST, Postman. Apps with Streamlit, React Native and Tkinter

The "ship it" folder: one API plus several clients, all talking to an LLM.

| Item | Contents |
|------|----------|
| `BlogAPI.zip` | Django + **Django REST Framework** project `blog_crew` exposing a **CrewAI crew** through an API: `crew_api/crew/{agents,tasks,crew}.py` define the crew, `serializers.py` / `views.py` / `urls.py` expose it (tested with Postman) |
| `Chatbot/app.py` | **Streamlit** chat UI over Gemini 1.5 Pro with `SystemMessage` history and `st.chat_message` rendering; `Chatbot/pages/app_2.py` is a second Streamlit page |
| `Ollama/chat_bot.py` | Console chat loop against a **local** model (`tinyllama` via `langchain-ollama`) |
| `Ollama/app.py`, `Ollama/app_tk_bt.py` | **Tkinter** desktop chat clients over the same local model |
| `Ollama/index_rag.py` | LlamaIndex RAG over `data/paul_graham_essay.txt`, with the index persisted in `storage/` |
| `apple.jpg` | Sample image used by the client apps |

**The point of the folder:** the model is only one line of code — the work is in the transport (REST), the state (chat history), and the UI (Streamlit, Tkinter, mobile).

```bash
# local model for the Ollama clients
ollama pull tinyllama
ollama serve

pip install streamlit langchain-ollama llama-index
streamlit run Chatbot/app.py
python Ollama/chat_bot.py
python Ollama/index_rag.py
```

For the REST API, extract the archive first — it ships its own `requirements.txt`, `.env` and even a nested `.git` directory:

```bash
unzip BlogAPI.zip && cd BlogAPI
pip install -r requirements.txt
python manage.py migrate && python manage.py runserver
```

---

## What you need to run any of it

**Python 3.10+** for everything, plus:

| Requirement | Needed by | Notes |
|---|---|---|
| `GOOGLE_API_KEY` | Sections 1–8 | Gemini 2.0 Flash (most notebooks) and Gemini 1.5 Pro (`Chatbot/app.py`). Set it in `.env` or as an environment variable |
| `TAVILY_API_KEY` | Sections 4 and 5 | Web-search tool in the RAG notebook and the CrewAI `Tavily.ipynb` |
| **Ollama** + `ollama pull tinyllama` | Section 8 (`Ollama/`) | Local model, no API key required |
| **ADK CLI** (`google-adk`) | Section 6 | Launch any `Google_ADK/<n>/` project with `adk web` or `adk run` |
| Unzipping | Sections 4, 5, 8 | `data.zip`, `config.zip`, `instructions.zip`, `BlogAPI.zip` |

Install per notebook rather than globally — each one has its own `!pip install` line at the top:

```bash
# typical per-folder setup
python -m venv .venv && .venv\Scripts\Activate.ps1     # Windows
pip install langchain langchain-google-genai python-dotenv
pip install crewai tavily-python
pip install llama-index llama-index-vector-stores-chroma chromadb
pip install transformers torch datasets gradio smolagents
pip install google-adk autogen-agentchat
pip install django djangorestframework streamlit langchain-ollama
```

---

## How the pieces fit

| If you want to… | Go to |
|---|---|
| Let a model call your functions over a standard protocol | `1. MCP example` |
| Use open models locally / build a quick UI | `2. Hugging Face` |
| Ask questions of a database or a PDF | `3. LangChain fundamentals. Text to SQL solutions` |
| Ground answers in your own documents | `4. LlamaIndex and RAG` |
| Split a job across cooperating agents | `5. CrewAI and Multi Agent AI solutions` |
| Control the agent graph deterministically | `6. AutoGen and Googe ADK` (Sequential / Parallel / Loop agents) |
| Put an LLM behind a web app | `7. Django fundamentals with databases` |
| Serve it as an API and connect real clients | `8. REST API with Django REST, Postman. Apps with Streamlit, React Native and Tkinter` |

---

## Notes and caveats

* **The `.env` files are placeholders.** Ten of them exist (eight in `Google_ADK`, one in `DjangoChatBot`, one in `Chatbot`) and they contain only variable *names* — `GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI`, nothing secret. Add your own key, and if you fork this repo keep real keys out of git.
* **Archives need extracting**: `data.zip` (documents for RAG), `config.zip` (YAML crew definition), `instructions.zip` (outreach briefs), `BlogAPI.zip` (the Django REST project, which also contains its own `.git` folder — remove or re-init it if you vendor the project into another repo).
* **Some material is in Latvian** — e.g. `SmolAgents.ipynb` headings (*Kodēšanas aģenti* = code agents, *Transformētāju rīki* = transformer tools); the code itself is English.
* **Local artifacts are committed**: `db.sqlite3` files in the Django projects, plus LlamaIndex `storage/*.json` in `Ollama/`. They are safe to delete — Django recreates the database with `migrate`, and `index_rag.py` rebuilds the vector store.
* **This is learning material, not a library.** Notebooks were written as course practice, so installs happen inside cells (`!pip install ...`) and there is no shared `requirements.txt` at the section root.
* **Model names age fast.** Where a notebook pins `gemini-1.5` or `gemini-2.0-flash`, expect to swap in the current model name.

---

## Tools & Technologies

* **Model access** — Google Gemini (via `langchain-google-genai`, `google.adk`), Hugging Face `transformers` / `smolagents`, local models through **Ollama**
* **Orchestration** — LangChain, LlamaIndex, CrewAI (crews + flows), Microsoft AutoGen, Google Agent Development Kit
* **Protocols & retrieval** — Model Context Protocol (`FastMCP`), Chroma vector store, Tavily web search
* **Serving** — Django, Django REST Framework, Streamlit, Tkinter, Postman
* **Data handling** — pandas, SQLAlchemy/SQLite, `PyPDFLoader`, `SimpleDirectoryReader`



