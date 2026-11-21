# ⚡ Inventra — Intelligent Financial & Inventory Management

**Inventra** is an AI-driven, weather-aware financial and inventory management system designed for small and medium-sized businesses (SMEs). Built with **LangGraph**, **Gemini 3.8 Flash**, **FAISS**, **SQLite**, **MCP (Model Context Protocol)**, and **Streamlit**, it transitions businesses from reactive spreadsheet tracking to proactive, forecast-driven supply chain and budget optimization.

---

## 🌟 Key Features

- **Supervisor-Routed Multi-Agent Architecture (LangGraph):**
  - **Supervisor Orchestrator:** Evaluates incoming natural language queries and dynamically routes between fast analytical lookups (`quick_data_lookup`) and full predictive workflows (`full_forecast_pipeline`).
  - **Data Understanding Agent:** Queries historical sales, inventory thresholds, financial ledgers, and vendor metrics via LangChain `@tool` functions, enriched with semantic climate advisories from **FAISS**.
  - **Weather Forecasting Agent:** Evaluates regional meteorological forecasts (`north`, `south`, `east`, `west`, `central`) and classifies operational risk levels.
  - **Decision & Optimization Agent:** Combines operational records with weather telemetry using **Pydantic** structured outputs to predict SKU demand surges, recommend reorder quantities, and calculate capital impact.
- **MCP-Enabled Smart Ticketing (`FastMCP`):**
  - Automatically generates and routes structured procurement/low-stock action tickets (`ticket_id`, `sku`, `rationale`, `forecasted_demand`, `recommended_qty`, `financial_impact`, `vendor_id`) into SQLite and exposes MCP tools for external integrations.
- **Hybrid Storage & Persistent Audit Trail:**
  - Ingests CSV datasets (`inventory.csv`, `sales.csv`, `finance.csv`, `vendors.csv`) into **SQLite** with automatic schema migration, pairs them with a **FAISS** vector store, and logs every agent decision in `audit_logs`.
- **Interactive Executive Dashboard (Streamlit + Plotly):**
  - Features live KPI cards, one-click regional weather stress tests, interactive demand vs. reorder charts, ticket lifecycle management (`OPEN` → `APPROVED` → `DISPATCHED` → `CLOSED`), and CSV/JSON audit exports.

---

## 📂 Project Structure

```text
inventra/
├── requirements.txt             # Python dependencies
├── README.md                    # Project documentation
├── app.py                       # Main Streamlit dashboard & user workflow
├── ui_theme.py                  # Executive UI styling & HTML component renderers
│
├── data/                        # Source business datasets
│   ├── finance.csv              # Financial ledger (sales & purchase transactions)
│   ├── inventory.csv            # SKU catalog, quantities, reorder thresholds & regions
│   ├── sales.csv                # Historical SKU sales volumes & revenue
│   └── vendors.csv              # Supplier quality scores, lead times & reliability
│
├── database/                    # Hybrid relational + vector storage layer
│   ├── setup_db.py              # CSV-to-SQLite loader, schema migration & ticket updates
│   ├── vector_store.py          # Cached FAISS semantic retriever for climate advisories
│
├── agents/                      # LangGraph multi-agent orchestration
│   ├── agents.py                # Standalone LangChain agent
│   ├── state.py                 # TypedDict state & Pydantic validation schemas
│   └── graph.py                 # Supervisor router, specialist nodes & retry logic
│
└── mcp_server/                  # Model Context Protocol (MCP) server
    ├── tools.py                 # LangChain tools over CSV datasets & sample weather
    └── ticket_server.py         # Exposes create_action_ticket & list_open_tickets tools
```

The `.env`, virtual environment, Python caches, and generated SQLite database are local-only and are not committed.

---

## 🛠️ Tech Stack & Dependencies

- **Python 3.12+**
- **LLM & Embeddings:** Google Gemini API (`gemini-3.8-flash` & `models/gemini-embedding-001`) via `langchain-google-genai`
- **Agent Orchestration:** `langgraph` & `langchain-core`
- **Action Protocol:** `mcp` (MCP Python SDK v1 `FastMCP`)
- **Storage & Retrieval:** `sqlite3`, `faiss-cpu`, `pandas`
- **Validation & Resilience:** `pydantic`, `tenacity`, `python-dotenv`
- **Frontend & Visualization:** `streamlit`, `plotly`

---

## 🚀 Getting Started

### 1. Clone or Navigate to the Project Directory
```bash
cd inventra
```

### 2. Create a Virtual Environment *(Recommended)*
```powershell
py -m venv .venv
```

### 3. Install Dependencies
```bash
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 5. Run the Streamlit Application
```bash
.\.venv\Scripts\python.exe -m streamlit run app.py
```
On first launch, `init_db()` automatically loads the CSV files from `data/` into `database/inventra.db`.

### *(Optional)* Run the Standalone MCP Server
To expose Inventra's ticketing tools over standard MCP stdio transport for external clients:
```bash
python mcp_server/ticket_server.py
```

---

## 💡 Example Queries to Try

- **Full Weather Forecast & Auto-Ticketing (`full_forecast_pipeline`):**
  > *"Forecast inventory for the south region given heavy rain expected, check low-stock items, and raise MCP reorder tickets."*
- **Budget & Demand Simulation (`full_forecast_pipeline`):**
  > *"Forecast next 30 days inventory for a severe heatwave in the west region and show expected budget impact."*
- **Fast Operational Lookup (`quick_data_lookup`):**
  > *"List our top 5 vendors by quality score and summarize current low-stock items across all regions."*
