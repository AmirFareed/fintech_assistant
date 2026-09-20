-- PostgreSQL + pgvector schema for the Fintech Assistant.
-- Requires PostgreSQL 13+ (gen_random_uuid() is built in) with the pgvector extension.
-- Applied by `python -m scripts.init_db` (and automatically by docker-compose on first start).
-- Safe to run multiple times.
--
-- The embedding dimension (384) matches BAAI/bge-small-en-v1.5. If you change
-- EMBEDDING_MODEL to a model with a different size, change it here and re-embed.

CREATE EXTENSION IF NOT EXISTS vector;

-- ── Knowledge base ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS departments (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name         TEXT NOT NULL,
    slug         TEXT NOT NULL UNIQUE,
    description  TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS services (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id  UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    service_name   TEXT NOT NULL,
    service_slug   TEXT NOT NULL,
    summary        TEXT,
    official_link  TEXT,
    fee_link       TEXT,
    keywords       TEXT[] NOT NULL DEFAULT '{}',
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (department_id, service_slug)
);

CREATE TABLE IF NOT EXISTS department_files (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id  UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    file_name      TEXT NOT NULL,
    storage_path   TEXT,
    version        TEXT,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE,
    uploaded_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id       UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    department_file_id  UUID REFERENCES department_files(id) ON DELETE CASCADE,
    service_id          UUID REFERENCES services(id) ON DELETE SET NULL,
    section_name        TEXT,
    chunk_text          TEXT NOT NULL,
    chunk_index         INTEGER NOT NULL DEFAULT 0,
    embedding           vector(384),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS chunks_department_idx ON chunks (department_id);
CREATE INDEX IF NOT EXISTS chunks_service_idx    ON chunks (service_id);
CREATE INDEX IF NOT EXISTS chunks_file_idx       ON chunks (department_file_id, chunk_index);
CREATE INDEX IF NOT EXISTS chunks_embedding_idx  ON chunks USING hnsw (embedding vector_cosine_ops);

-- Cosine-similarity search, optionally scoped to a department and/or service.
CREATE OR REPLACE FUNCTION match_chunks(
    query_embedding       vector(384),
    match_count           INTEGER DEFAULT 10,
    filter_department_id  UUID DEFAULT NULL,
    filter_service_id     UUID DEFAULT NULL
)
RETURNS TABLE (
    id                  UUID,
    department_id       UUID,
    department_file_id  UUID,
    service_id          UUID,
    section_name        TEXT,
    chunk_text          TEXT,
    chunk_index         INTEGER,
    similarity          DOUBLE PRECISION
)
LANGUAGE sql STABLE AS $$
    SELECT c.id, c.department_id, c.department_file_id, c.service_id,
           c.section_name, c.chunk_text, c.chunk_index,
           1 - (c.embedding <=> query_embedding) AS similarity
    FROM chunks c
    WHERE c.embedding IS NOT NULL
      AND (filter_department_id IS NULL OR c.department_id = filter_department_id)
      AND (filter_service_id    IS NULL OR c.service_id    = filter_service_id)
    ORDER BY c.embedding <=> query_embedding
    LIMIT match_count;
$$;

-- ── Analytics ─────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS user_queries (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text         TEXT NOT NULL,
    intent             TEXT,
    service            TEXT,
    session_id         TEXT,
    response_language  TEXT,
    had_result         BOOLEAN,
    response_time_ms   INTEGER,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS user_queries_created_idx ON user_queries (created_at DESC);

CREATE TABLE IF NOT EXISTS feedback (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text  TEXT,
    rating      INTEGER NOT NULL,   -- 1 = thumbs up, -1 = thumbs down
    comment     TEXT,
    intent      TEXT,
    service     TEXT,
    session_id  TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS feedback_created_idx ON feedback (created_at DESC);

CREATE TABLE IF NOT EXISTS token_usage (
    id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id         TEXT,
    prompt_tokens      INTEGER DEFAULT 0,
    completion_tokens  INTEGER DEFAULT 0,
    total_tokens       INTEGER DEFAULT 0,
    model              TEXT,
    created_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
