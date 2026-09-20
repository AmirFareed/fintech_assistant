# Fintech Assistant

Flask chatbot for PSID-based digital-payment guidance, backed by PostgreSQL + pgvector and Groq.

## Project structure

The repo is two independent apps that only communicate over HTTP.

```text
fintech_assistant/
├── backend/                  Flask JSON API (no HTML, no static assets)
│   ├── api/                  Routes: public chat API, admin API, bearer-token auth
│   ├── ingestion/            File parsing and ingestion pipeline
│   ├── chunking/             Text splitting and overlap logic
│   ├── embeddings/           Embedding model adapter
│   ├── vectordb/             PostgreSQL/pgvector client and local file store
│   ├── retrieval/            Keyword/vector search and intent routing
│   ├── prompts/              Prompt templates and response construction
│   ├── llm/                  LLM clients and chat orchestration
│   ├── utils/                Configuration and language helpers
│   ├── services/             Backward-compatible aliases for older imports
│   ├── data/  database/  scripts/  tests/  logs/
│   ├── main.py  app.py       Entry points (Gunicorn: main:app)
│   └── config.yaml  .env.example  requirements.txt  Dockerfile
├── frontend/                 Static site (no build step, no Python)
│   ├── index.html            User chat page
│   ├── admin/                Admin panel (login, dashboard, queries, feedback, knowledge, test)
│   ├── widget/               Embeddable chat widget
│   ├── assets/               Shared CSS and images
│   ├── config.js             Backend URL (apiBaseUrl)
│   └── Dockerfile  nginx.conf
├── docker-compose.yml        Runs both
├── render.yaml               Render blueprint (backend web service + frontend static site)
└── README.md
```

### API contract

| Endpoint | Auth | Purpose |
| --- | --- | --- |
| `GET /healthz`, `GET /health` | – | Liveness / database check |
| `POST /api/chat`, `GET /api/suggestions`, `POST /api/feedback` | – | Public chat API |
| `POST /api/admin/login` | – | `{username, password}` → `{token}` |
| `GET /api/admin/{me,dashboard,queries,feedback,knowledge}` | Bearer | Admin data |
| `DELETE /api/admin/files/<id>` | Bearer | Delete a knowledge-base file |
| `POST /api/upload`, `GET /debug/retrieval` | Bearer | Ingest a file / debug retrieval |

Admin auth is a signed, expiring (12h) bearer token sent in the `Authorization` header; the frontend keeps it in `localStorage`. There are no cookies or server-side sessions, so the two apps can live on different origins.

## Setup

**Quickest way (Node required):** from the repo root, `npm run setup` once (creates `backend/.venv` and installs requirements), start the database (below), then `npm run dev` starts backend and frontend together (`npm start` does the same and opens Chrome) (`npm run dev:backend` / `npm run dev:frontend` run one). Ctrl+C stops both.

**Backend** (Python 3.11 or 3.12):

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env      # fill in database / LLM credentials; never commit .env
python main.py            # http://localhost:5000
```

**Database** (PostgreSQL 13+ with the pgvector extension). The quickest way is Docker:

```bash
npm run db:up      # starts pgvector/pgvector:pg16 on localhost:5432 (schema applied on first start)
npm run db:seed    # applies the schema, loads the Digital Payments services, ingests backend/data/*.txt
```

`DATABASE_URL` in `backend/.env` defaults to `postgresql://fintech:fintech@localhost:5432/fintech`, matching the compose service. To use your own server instead, install pgvector there, set `DATABASE_URL`, and run `npm run db:init` (schema only) or `db:seed`. The embedding column is `vector(384)` for `BAAI/bge-small-en-v1.5`; see the note in `backend/database/schema.sql` if you change the model.

Original uploaded knowledge-base files are kept on disk in `FILE_STORAGE_DIR` (default `backend/uploads/knowledge_base`); only their path is stored in Postgres.

`/healthz` is the lightweight liveness endpoint, while `/health` also checks database connectivity.

**Frontend** (any static file server):

```bash
cd frontend
# edit config.js so apiBaseUrl points at the backend (default http://localhost:5000)
python -m http.server 8080    # http://localhost:8080  (admin: /admin/login.html)
```

Set `WIDGET_ALLOWED_ORIGINS` in `backend/.env` to the frontend's origin (or `*`) so the browser is allowed to call the API.

**Everything with Docker:** `docker compose up --build` (frontend on `:8080`, backend on `:5000`, Postgres on `:5432`; set `apiBaseUrl` in `frontend/config.js` first, then run the seed once).

## Configuration

Safe defaults such as chunk size, retrieval count, model names, and timeouts live in `config.yaml`. Environment variables override YAML values, and secrets belong only in `.env` or the hosting provider's secret manager.

For memory-constrained hosting, use `LLM_PROVIDER=groq` and `ENABLE_VECTOR_RETRIEVAL=false`.

## Maintenance commands

Run scripts from `backend/`:

```bash
python -m scripts.reset_and_setup_fintech
python -m scripts.ingest_fintech
python -m scripts.refresh_fintech_rag
python -m scripts.embed_chunks
python -m scripts.setup_services
```

The scripts read source documents from `backend/data/`.

## Tests

```bash
cd backend
python -m pytest
```

The configured test run writes a self-contained `test_report.html`, which is ignored by Git.

## Deployment

Production layout: backend + PostgreSQL/pgvector on an Oracle Cloud VM (`docker-compose.prod.yml`, HTTPS via Caddy), static frontend on Render (`render.yaml`). Step-by-step guide, including firewall ports, Caddy config, CORS and redeploys: **[docs/DEPLOY.md](docs/DEPLOY.md)**.

Uploaded knowledge-base files are stored in `FILE_STORAGE_DIR` (default `backend/uploads/knowledge_base`); the production compose file keeps them in a Docker volume.
