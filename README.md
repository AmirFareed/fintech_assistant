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

### Also running on Oracle Cloud (Always Free)

Migrated here to fix Render free-tier cold-start latency, and to get enough
headroom to run with `ENABLE_VECTOR_RETRIEVAL=true` (Render's 512MB tier
required leaving it `false` — see `render.yaml`). Shares the same Ampere A1
Always Free VM as the `onboarding-verification` backend, each app in its own
container behind the same [Caddy](https://caddyserver.com/) instance, which
handles HTTPS for both.

**Deployment shape on the VM:**

- **Docker container** `fintech-assistant`, built from this repo's own
  `Dockerfile`, run with `--restart=always`. Bound to `127.0.0.1:8001` only -
  not exposed directly to the internet, same as the onboarding backend on
  `127.0.0.1:8000`.
- **Caddy** (`/etc/caddy/Caddyfile` on the VM) reverse-proxies
  `https://chat.<vm-ip-with-dashes>.sslip.io` to `127.0.0.1:8001`, obtaining
  and renewing its own Let's Encrypt certificate automatically - a second
  site block alongside the onboarding backend's, no new domain needed.
- **Secrets** live in `~/fintech-assistant/.env` on the VM (mode `600`,
  never committed), built from the same variables as `.env.example`. Notable
  production differences from the Render config in `render.yaml`:
  `ENABLE_VECTOR_RETRIEVAL=true` (not `false`), and `SECRET_KEY` /
  `ADMIN_PASSWORD` are VM-specific, generated on deploy rather than reused
  from Render's.
- The VM is single-core (`nproc` = 1) and shared with another app, so no
  extra Gunicorn workers are configured - the Dockerfile's default single
  worker is deliberate here, not an oversight.

**Redeploying after a code change** - simpler than the onboarding backend's
recipe because this repo is public, so the VM can `git pull` directly
instead of needing the source copied over from a dev machine:

```bash
ssh -i <key> ubuntu@<vm-ip> "cd ~/fintech-assistant \
  && git pull \
  && docker build -t fintech-assistant:latest . \
  && docker stop fintech-assistant && docker rm fintech-assistant \
  && docker run -d --name fintech-assistant --restart=always \
       -p 127.0.0.1:8001:5000 --env-file ~/fintech-assistant/.env \
       fintech-assistant:latest"
```

If `database/schema.sql` or the Supabase `match_chunks` RPC changed, apply
those in the Supabase SQL editor first - this repo's deploy step never
touches Supabase itself.
