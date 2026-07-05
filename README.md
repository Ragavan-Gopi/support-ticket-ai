# Support Ticket AI

## Short Summary
An AI engineering assessment app for support ticket analytics, anomaly detection, and Retrieval-Augmented Generation (RAG) using a local Ollama LLM. It demonstrates a full-stack, production-aware approach to processing, analyzing, and querying ticket data naturally.

## Key Features
- **FastAPI backend**: Robust, typed, and easily extensible API serving the core features.
- **SQLite ticket database**: Relational store for ticket metadata and tabular analytics.
- **CSV ingestion**: Robust idempotent data loading from raw CSVs.
- **Analytics dashboard metrics**: Insights on volume, resolution times, and SLAs.
- **Statistical anomaly detection**: Automated pipeline identifying high-volume days, outliers, and priority escalations.
- **Local Ollama LLM wrapper**: Secure, local AI text generation using `qwen2.5:7b`.
- **ChromaDB vector store**: Local vector storage for RAG semantic search.
- **RAG retrieval and grounded Q&A**: Hybrid semantic queries providing sourced, natural language answers.
- **Streamlit UI**: A clean, beginner-readable frontend dashboard.
- **Pytest test suite**: Practical, offline-safe automated tests for analytics and API logic.

## Architecture Overview
The application follows a clean, decoupled data flow:
1. **Data Ingestion**: `CSV -> Ingestion Pipeline -> SQLite Tickets Table` (Powers standard analytics and anomaly detection).
2. **Vector Indexing**: `SQLite Tickets -> Text Chunking -> Ollama Embeddings -> ChromaDB Vector Store`.
3. **Retrieval-Augmented Q&A**: `User Query -> Vector Search (ChromaDB) -> Top-K Context + Query -> Ollama Chat Model -> Grounded Answer`.
4. **Presentation**: `FastAPI Endpoints -> HTTP REST -> Streamlit UI`.

## Project Structure
```text
support-ticket-ai/
├── app/                  # FastAPI backend and core logic
│   ├── api/              # API Route definitions
│   ├── core/             # Business logic (DB, RAG, LLM, Anomalies)
│   ├── data/             # CSVs, SQLite db, and Chroma directory
│   └── main.py           # FastAPI application entrypoint
├── scripts/              # Helper scripts
│   ├── ingest.py         # CSV ingestion script
│   └── start.py          # Quickstart CLI helper
├── tests/                # Automated pytest suite
├── ui/                   # Streamlit frontend
│   └── streamlit_app.py
├── .env.example          # Environment variables template
├── PROJECT_INSTRUCTIONS.md # Permanent engineering rulebook
├── project_state.md      # Development tracker
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Docker configurations (omitted/explained)
└── README.md             # This file
```

## Prerequisites
- **Python 3.10+** (Tested on Windows PowerShell; Python 3.14.0 was used during development)
- **Ollama** installed and running locally.
- **Required Ollama Models**:
  - `qwen2.5:7b` (For chat/generation)
  - `nomic-embed-text` (For vector embeddings)

## Setup Instructions for Windows PowerShell
1. **Create and Activate Virtual Environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. **Install Requirements**:
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. **Setup Environment Variables**:
   Copy `.env.example` to `.env` (optional, as the app has safe defaults).
4. **Pull Ollama Models**:
   Ensure Ollama is running, then pull the necessary models:
   ```powershell
   ollama pull qwen2.5:7b
   ollama pull nomic-embed-text
   ```
5. **Run Data Ingestion**:
   ```powershell
   python scripts/ingest.py
   ```

## Environment Variables
Configured via `.env` (refer to `.env.example`):
- `OLLAMA_BASE_URL`: http://localhost:11434
- `OLLAMA_CHAT_MODEL`: qwen2.5:7b
- `OLLAMA_EMBED_MODEL`: nomic-embed-text
- `OLLAMA_TIMEOUT`: 120 (seconds)
- `OLLAMA_MAX_RETRIES`: 3
- `DATA_DIR`: app/data
- `DB_PATH`: app/data/tickets.db
- `CHROMA_DIR`: app/data/chroma
- `CHROMA_COLLECTION_NAME`: support_tickets
- `API_BASE_URL`: http://127.0.0.1:8000
- `API_TIMEOUT`: 10 (seconds) - *Note: Local Ask AI/RAG generation can take longer on CPU; you may need to increase this if you experience timeouts.*

## Running the Application
Alternatively, you can run `python scripts/start.py` to view these commands.

**Terminal 1: Start the FastAPI Backend**
```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

**Terminal 2: Start the Streamlit UI**
```powershell
.\.venv\Scripts\python.exe -m streamlit run ui\streamlit_app.py
```

## Running Tests
Tests are built with pytest and are designed to run safely completely offline (no LLM required).
```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```
*Latest known result: 10 passed.*

## API Endpoints
The backend exposes the following REST endpoints:
- `GET /` - Root status
- `GET /health/` - Backend API health
- `GET /health/ollama` - Local Ollama connectivity check
- `GET /query/status` - RAG subsystem state (DB and Chroma metrics)
- `POST /query/retrieve` - Semantic search for tickets
- `POST /query/ask` - RAG-powered natural language Q&A
- `POST /query/index` - Trigger ticket vectorization
- `GET /anomalies/status` - Anomaly engine state
- `GET /anomalies/report` - Comprehensive JSON anomaly report
- `GET /anomalies/summary` - Compact anomaly dashboard metrics
- `GET /anomalies/analytics` - Baseline descriptive analytics

## Known Operational Note
- **✅ Chroma Index State**: The submitted/demo database is fully indexed with 500/500 tickets ready for full RAG search.
- **Re-indexing**: Re-indexing can still be triggered with `POST /query/index` or the Streamlit Admin Indexing Control.
- **Performance**: Full re-indexing may take significant time because all vector embeddings are generated locally through the Ollama instance.

## How to Re-index Tickets
To rebuild or refresh the vector index, you can either:
1. Use the **Admin Indexing Control** expander section inside the Streamlit UI.
2. Send an HTTP POST to `/query/index` with an empty body (omitting the `limit` key).
*Warning: Full indexing may take time on standard hardware.*

## Interview Explanation
*Compact talking points on design decisions:*
- **Why FastAPI**: Lightweight, strongly typed (Pydantic), auto-generating docs, and built for modern asynchronous APIs.
- **Why SQLite**: Zero-configuration, zero-dependency, serverless relational database perfect for local analytic aggregations.
- **Why ChromaDB**: Purpose-built, lightweight local vector database optimized for storing embeddings and semantic retrieval.
- **Why Ollama**: Enables completely local, private, and free LLM execution (preventing data leakage and removing third-party API costs).
- **What RAG means here**: When a user asks a question, the system semantically searches past tickets (Retrieval), augments the LLM prompt with those past solutions (Augmented), and instructs the LLM to synthesize a grounded answer (Generation).
  - *Hybrid Routing Note*: Aggregate/count questions (e.g. "How many total tickets?") are deterministically routed and answered through SQLite analytics, while descriptive ticket-pattern questions use the RAG flow.
- **How Anomaly Detection works**: It leverages classic statistical methods (Z-scores and thresholds over aggregations) instead of heavy ML models, ensuring the engine is fast, explainable, and deterministic.
- **How reliability is handled**: Environment configuration fallbacks, unified structured logging (`ANOM_`, `RAG_`), graceful HTTP error trapping separating UI failures from API logic, and offline-safe automated tests.

## Limitations and Future Improvements
- **Indexing Time**: Full indexing is already completed for this demo, but rebuilding the vector index may take time because embeddings are generated locally.
- **Local LLM Speed**: Response latency scales entirely with local CPU/GPU hardware.
- **Anomaly Logic**: Currently uses foundational statistical thresholding; could be upgraded to ML-based isolation forests.
- **Future Enhancements**: Authentication/authorization, Docker containerization for deployment, richer Streamlit charts (e.g. Altair/Plotly), and automated RAG evaluation metrics.
