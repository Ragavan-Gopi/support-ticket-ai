# Project State

## Current Project Goal
Build an AI engineering assessment app for support ticket analytics, anomaly detection, and RAG using a local Ollama LLM.

## Environment Facts
- **Virtual environment name**: `.venv`
- **Ollama base URL**: `http://localhost:11434`
- **Chat model**: `qwen2.5:7b`
- **Embedding model**: `nomic-embed-text`
- **Dataset**: `app/data/support_tickets.csv`
- **Database**: SQLite at `app/data/tickets.db`

## Current Completed Work
- **Phase 1**: Foundation API is implemented and tested.
  - Endpoints working: `GET /`, `GET /health/`, `GET /health/ollama`, `GET /docs`
  - Ollama connectivity validated for chat and embedding generation.
- **Phase 2**: Database + CSV Ingestion Foundation is completed.
  - SQLite schema defined matching the CSV fields.
  - Idempotent ingestion pipeline created (`ticket_id` as primary key).
  - CLI script added to trigger ingestion logic manually.
- **Phase 3**: Analytics Foundation is completed.
  - Implemented reusable support-ticket analytics logic using actual SQLite schema.
  - Safely handles missing columns (e.g. SLA).
  - Provides a single `get_dashboard_metrics()` function.
- **Phase 4**: Anomaly Detection Foundation is completed.
  - Added simple, explainable statistical anomaly checks for volume spikes, categories, priorities, outliers, escalations, and recurring issues.
  - Returns structured dictionaries of anomalies with severity and reasons.
- **Phase 4.1**: Anomaly Detection Hardening is completed.
  - Improved severity logic for resolution time outliers (e.g., dynamically scoring high severity if > 5x average).
  - Ensured all thresholds are clearly parameterized.
- **Phase 5**: Ollama LLM Wrapper Foundation is completed.
  - Added clean, reusable Python wrappers for text generation and embeddings.
  - Uses configured Ollama models and handles failures with bounded retries.
- **Phase 6**: RAG/Vector Foundation is completed.
  - Implemented core RAG pipeline using ChromaDB.
  - Added idempotent batch indexing for tickets.
  - Added retrieval and question-answering functions combining ChromaDB and the Ollama LLM wrapper.
- **Phase 6.1**: Project Hygiene and Config Hardening is completed.
  - Cleaned up stale text in PROJECT_INSTRUCTIONS.md.
  - Hardened config.py to read from OS environment variables appropriately.
  - Hardened rag.py limits/top_k validation and SQL params.
- **Phase 6.2**: Micro Cleanup before API routes is completed.
  - Converted PROJECT_INSTRUCTIONS.md into a timeless rulebook by removing the known state section.
  - Fixed config.py path resolution so relative paths are always anchored to BASE_DIR.
  - Cleaned up extra blank lines in requirements.txt.
- **Phase 7**: FastAPI Query Route is completed.
  - Added request/response schemas in app/core/schemas.py.
  - Exposed RAG retrieve, ask, and index functionality through REST API endpoints in app/api/routes_query.py.
  - Integrated the query router into app/main.py.
- **Phase 7.1**: Query API Cleanup and Status Hardening is completed.
  - Hardened /query/status to report detailed operational information (DB count, Chroma index count).
  - Improved /query/index endpoint request parsing.
  - Removed remaining phase status metadata from PROJECT_INSTRUCTIONS.md.
- **Phase 8**: FastAPI Anomaly Route is completed.
  - Added request/response schemas in app/core/schemas.py for anomalies and analytics.
  - Exposed get_anomaly_report and get_dashboard_metrics through REST API endpoints in app/api/routes_anomalies.py.
  - Integrated the anomalies router into app/main.py.
- **Phase 9**: Streamlit UI Foundation is completed.
  - Built a Streamlit web app (ui/streamlit_app.py) consuming the FastAPI endpoints.
  - Added API_BASE_URL config support in .env.example.
  - Implemented dashboards for Analytics, Anomalies, RAG search, RAG QA, and indexing control.
- **Phase 9.1**: Streamlit UI and Schema Hardening is completed.
  - Scrubbed PROJECT_INSTRUCTIONS.md to remove legacy phase status text.
  - Replaced mutable defaults in app/core/schemas.py with Field(default_factory=...).
  - Improved ui/streamlit_app.py to correctly parse .env files and gracefully handle HTTP and business-logic errors during Q&A and analytics fetching.
- **Phase 9.2**: Streamlit UI Error-Handling Cleanup is completed.
  - Added API_TIMEOUT to .env.example with a safe default.
  - Normalized API_BASE_URL to prevent double slashes.
  - Standardized UI component handling to cleanly separate "_request_error" network failures from API-level application errors.
- **Phase 10**: Tests Foundation is completed.
  - Created practical, lightweight tests for analytics (tests/test_analytics.py), anomalies (tests/test_anomalies.py), and API routes (tests/test_api.py).
  - Ensured testing avoids Ollama generation calls and full indexing for performance.
- **Phase 10.1**: Tests/Repo Hygiene is completed.
  - Explicitly added pytest dependency into requirements.txt.
  - Hardened tests/test_api.py to validate API input limits without triggering Ollama embeddings.
  - Scrubbed locally generated test caches (.pytest_cache) for repository cleanliness.
- **Phase 11**: Final Documentation is completed.
  - Wrote comprehensive, professional README.md covering architecture, setup, APIs, tests, and interview explanations.
  - Created a simple scripts/start.py helper script for quick local startup commands.
- **Phase 12**: Final Validation + Submission Cleanup is completed.
  - Corrected README Python version documentation.
  - Provided explicit instructions via comments in docker-compose.yml on why Docker is intentionally omitted.
  - Executed final suite of compile checks, pytest executions, DB count assertions, and endpoint validations.
  - Recursively scrubbed all generated `__pycache__` and `.pytest_cache` directories.
- **Phase 12.1**: Final Perfection Pass is completed.
  - Hardened app/config.py environment variable parsing.
  - Improved /query/status and /anomalies/status operational honesty by handling missing DBs/indexes safely and returning degraded state.
  - Scrubbed requirements.txt to only contain absolute project dependencies with no bloat.
  - Added Anomaly Engine status metric to Streamlit UI.
- **Final Cleanup**: Micro-documentation fix applied to ensure `tests/test_api.py` is included in the PROJECT_INSTRUCTIONS.md project structure tree.
- **Final Polish**: Polished URL normalization in config.py and hardened status endpoints to gracefully degrade on None ticket_counts.
- **Final Indexing**: Full Chroma indexing manually completed. The vector store now natively reflects 500/500 tickets.
- **Anomaly Status Hardening**: Hardened /anomalies/status to query tickets table directly and degrade when ticket_count cannot be determined.
- **UI Bugfix**: Streamlit RAG actions were corrected to safely parse HTTP errors and correctly enforce POST for /query/retrieve, /query/ask, and /query/index.
- **UI Timeout Handling**: Improved Streamlit API timeout handling to catch and display a helpful message specifically for long-running local Ollama RAG generation tasks.
- **Hybrid RAG Analytics Routing**: Upgraded /query/ask with a heuristic router that intelligently redirects statistical/aggregate questions (like total ticket counts) directly to SQLite analytics logic, guaranteeing accurate deterministic answers instead of relying purely on retrieved document chunks.
- **UI Wording Polish**: Polished the Streamlit Ask AI section to clearly denote the "(Analytics + RAG)" hybrid approach and properly format SQLite analytics sources vs. ticket chunk sources.

## Files Implemented / Modified
- `app/core/database.py` (added `fetch_all` helper)
- `app/core/ingestion.py`
- `scripts/ingest.py`
- `app/core/analytics.py`
- `app/core/anomalies.py`
- `app/core/llm.py`
- `app/core/rag.py`
- `app/core/schemas.py`
- `app/api/routes_query.py`
- `app/api/routes_anomalies.py`
- `app/main.py`
- `ui/streamlit_app.py`
- `app/config.py`
- `.env.example`
- `requirements.txt`
- `PROJECT_INSTRUCTIONS.md`
- `project_state.md`
- `tests/test_analytics.py`
- `tests/test_anomalies.py`
- `tests/test_api.py`
- `README.md`
- `scripts/start.py`
- `docker-compose.yml`

## Last Successful Command Run
`.venv\Scripts\python.exe -m pytest tests -q` (And full validation suite: compileall, DB count, TestClient endpoints)

## Known Issues
- Note: Chroma index completed for 500/500 tickets.

## Next Recommended Step
Submit project / demo using README runbook.
