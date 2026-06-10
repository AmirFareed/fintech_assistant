-- Run this in your Supabase SQL editor before starting the app.
-- Safe to run multiple times (uses IF NOT EXISTS / ADD COLUMN IF NOT EXISTS).

-- ── Feedback ──────────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS feedback (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_text      TEXT,
    rating          INTEGER NOT NULL,   -- 1 = thumbs up, -1 = thumbs down
    comment         TEXT,
    intent          TEXT,
    service         TEXT,
    session_id      TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ── Token usage ───────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS token_usage (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id          TEXT,
    prompt_tokens       INTEGER DEFAULT 0,
    completion_tokens   INTEGER DEFAULT 0,
    total_tokens        INTEGER DEFAULT 0,
    model               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ── Extend user_queries with extra columns ────────────────────────────────────
ALTER TABLE user_queries ADD COLUMN IF NOT EXISTS session_id       TEXT;
ALTER TABLE user_queries ADD COLUMN IF NOT EXISTS response_language TEXT;
ALTER TABLE user_queries ADD COLUMN IF NOT EXISTS had_result        BOOLEAN;
ALTER TABLE user_queries ADD COLUMN IF NOT EXISTS response_time_ms  INTEGER;
