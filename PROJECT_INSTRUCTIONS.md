# Support Ticket AI - Project Instructions
## Project Identity
Project name: support-ticket-ai
Goal: Build an AI engineering assessment app for support ticket analytics, anomaly detection, and RAG using a local Ollama LLM.
The app must demonstrate:
- Clean backend architecture
- Local LLM integration
- RAG pipeline
- Ticket analytics
- Anomaly detection
- Streamlit UI
- Production-aware engineering practices
## Fixed Project Structure
Do not change this structure:
support-ticket-ai/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── api/
│   │   ├── routes_health.py
│   │   ├── routes_query.py
│   │   └── routes_anomalies.py
│   ├── core/
│   │   ├── database.py
│   │   ├── ingestion.py
│   │   ├── analytics.py
│   │   ├── anomalies.py
│   │   ├── rag.py
│   │   ├── llm.py
│   │   └── schemas.py
│   └── data/
│       ├── support_tickets.csv
│       ├── tickets.db
│       └── chroma/
├── ui/
│   └── streamlit_app.py
├── scripts/
│   ├── ingest.py
│   └── start.py
├── tests/
│   ├── test_analytics.py
│   ├── test_anomalies.py
│   └── test_api.py
├── README.md
├── PROJECT_INSTRUCTIONS.md
├── project_state.md
├── requirements.txt
├── .env.example
└── docker-compose.yml
Never create backend/ or frontend/.
Backend API code belongs under app/.
Streamlit UI belongs under ui/.
Runnable helper scripts belong under scripts/.
Tests belong under tests/.
## Current Runtime Assumptions
Virtual environment name: .venv
Ollama base URL:
http://localhost:11434
Chat model:
qwen2.5:7b
Embedding model:
nomic-embed-text
## Engineering Rules
Avoid hardcoded values in business logic.
Use configuration/env values for:
- URLs
- model names
- database paths
- vector store paths
- retry counts
- timeout values
- thresholds
- app-level settings
Constants are allowed only when they are local, obvious, and not environment-dependent.
## Reliability Rules
Add retry logic for recoverable failures only, such as:
- Ollama API calls
- temporary network/API failures
- safe file IO retries
- transient database/vector store access errors
Do not retry:
- validation errors
- malformed input
- missing required columns
- deterministic programming errors
Retry behavior must use bounded attempts and clear failure messages.
## Logging Rules
Use structured, readable logging.
Logs should include:
- operation name
- error code
- error message
- exception details where useful
- timing for important operations
- enough context to debug without exposing secrets
Use consistent error-code prefixes:
CFG_*  = configuration errors  
ING_*  = ingestion errors  
DB_*   = database errors  
LLM_*  = Ollama/model errors  
RAG_*  = retrieval/vector errors  
API_*  = API route errors  
ANOM_* = anomaly detection errors  
UI_*   = Streamlit/UI errors  
## Error Handling Rules
API errors must be clear and predictable.
Handle these gracefully:
- Ollama unavailable
- missing CSV file
- invalid CSV format
- missing required CSV columns
- database initialization failure
- empty database
- vector store unavailable
- empty retrieval results
- invalid user query
- anomaly detection with insufficient data
## Code Quality Rules
Use:
- type hints
- small functions
- readable names
- simple comments for important logic
- Pydantic/FastAPI schemas for request/response validation where appropriate
Avoid:
- unnecessary abstraction
- over-engineering
- hidden magic
- huge functions
- unexplained business logic
- rewriting working code without reason
Comments should explain why important logic exists, not obvious syntax.
## Data and Ingestion Rules
Ingestion should be idempotent where possible.
Rerunning ingestion should not blindly duplicate ticket data.
Validate CSV data before inserting into the database.
Keep the generated/sample ticket data realistic enough to support:
- analytics
- anomaly detection
- RAG answers
- interview explanation
## RAG Rules
RAG flow should be explainable:
1. Load ticket/document data
2. Chunk meaningful text
3. Generate embeddings using Ollama embedding model
4. Store embeddings in ChromaDB
5. Retrieve relevant chunks for a user question
6. Send retrieved context plus question to Ollama chat model
7. Return grounded answer
Answers should avoid pretending when no relevant context is found.
## Project State Maintenance
The coding agent must maintain project_state.md.
If project_state.md does not exist, create it during the first implementation prompt.
After every implementation task:
- inspect what changed
- update project_state.md
- surgically append/remove only the changed state
- do not rewrite the whole file unless necessary
- keep it concise and accurate
project_state.md must track:
- current completed work
- implemented files
- pending files/features
- known issues
- last successful run/test
- next recommended step
## Agent Workflow
Before modifying files:
1. Read PROJECT_INSTRUCTIONS.md.
2. Read project_state.md if it exists.
3. Inspect the files that will be changed.
During implementation:
1. Modify only files required for the current task.
2. Preserve existing working behavior.
3. Do not change project structure.
4. Do not implement future phases early.
After implementation:
1. Summarize changed files.
2. Mention commands to run/test.
3. Update project_state.md.
4. State the next recommended step.