# Fintech Assistant

Flask chatbot for PSID-based digital-payment guidance, backed by Supabase and Groq.

## Project structure

```text
fintech_assistant-main/
├── README.md                 Project documentation and setup
├── requirements.txt         Python dependencies
├── .env.example             Environment variable template
├── .env                     Local secrets (ignored by Git)
├── .gitignore               Git exclusions
├── config.yaml              Non-secret application defaults
├── main.py                  Local application entry point
├── api/                     Flask routes, UI blueprints, templates, and assets
├── ingestion/               File parsing and ingestion pipeline
├── chunking/                Text splitting and overlap logic
├── embeddings/              Embedding model adapter
├── vectordb/                Supabase client and vector persistence helpers
├── retrieval/               Keyword/vector search and intent routing
├── prompts/                 Prompt templates and response construction
├── llm/                     LLM clients and chat orchestration
├── utils/                   Configuration and language helpers
├── data/                    Source knowledge-base documents
├── database/                Database schema
├── scripts/                 Setup, refresh, ingestion, and maintenance commands
├── tests/                   Unit and integration tests
├── logs/                    Runtime log location
└── services/                Backward-compatible aliases for older imports
```

The implementation lives in the responsibility-based packages. `app.py`, `config.py`, and `services/` remain as compatibility shims so existing deployment commands and integrations do not fail during migration.

## Setup

1. Create and activate a Python 3.11 or 3.12 virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Copy `.env.example` to `.env` and enter the Supabase and LLM credentials. Never commit `.env`.
4. Create the database objects using `database/schema.sql`.
5. Start the app:

   ```bash
   python main.py
   ```

The default URL is `http://localhost:5000`. `/healthz` is the lightweight liveness endpoint, while `/health` also checks Supabase connectivity.

## Configuration

Safe defaults such as chunk size, retrieval count, model names, and timeouts live in `config.yaml`. Environment variables override YAML values, and secrets belong only in `.env` or the hosting provider's secret manager.

For memory-constrained hosting, use `LLM_PROVIDER=groq` and `ENABLE_VECTOR_RETRIEVAL=false`.

## Maintenance commands

Run scripts from the repository root:

```bash
python -m scripts.reset_and_setup_fintech
python -m scripts.ingest_fintech
python -m scripts.refresh_fintech_rag
python -m scripts.embed_chunks
python -m scripts.setup_services
```

The scripts read source documents from `data/`.

## Tests

```bash
python -m pytest
```

The configured test run writes a self-contained `test_report.html`, which is ignored by Git.

## Deployment

The included Docker, Compose, Render, and Procfile definitions start Gunicorn with `main:app`. On Render, use `/healthz` as the health-check path and configure the variables listed in `.env.example`.

Uploaded files are written to `uploads/`. This directory is ignored by Git and is ephemeral on hosts without persistent disks.
