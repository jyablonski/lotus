-- +goose Up

ALTER TABLE source.users
    ADD COLUMN IF NOT EXISTS community_insights_opt_in BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS community_location_opt_in BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS community_country_code VARCHAR(8),
    ADD COLUMN IF NOT EXISTS community_region_code VARCHAR(32);

CREATE TABLE IF NOT EXISTS source.journal_community_projections (
    journal_id               INTEGER PRIMARY KEY REFERENCES source.journals(id) ON DELETE CASCADE,
    user_id                  UUID NOT NULL REFERENCES source.users(id) ON DELETE CASCADE,
    eligible_for_community   BOOLEAN NOT NULL DEFAULT FALSE,
    entry_local_date         DATE,
    primary_mood             VARCHAR(32),
    primary_sentiment        VARCHAR(32),
    theme_names              TEXT[] NOT NULL DEFAULT '{}',
    country_code             VARCHAR(8),
    region_code              VARCHAR(32),
    analysis_version         VARCHAR(64) NOT NULL DEFAULT 'v1',
    updated_at               TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at               TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jcp_eligible_date
    ON source.journal_community_projections (eligible_for_community, entry_local_date);

CREATE INDEX IF NOT EXISTS idx_jcp_region_date
    ON source.journal_community_projections (region_code, entry_local_date);

CREATE TABLE IF NOT EXISTS source.community_theme_rollups (
    id                SERIAL PRIMARY KEY,
    bucket_date       DATE NOT NULL,
    time_grain        VARCHAR(16) NOT NULL,
    scope_type        VARCHAR(16) NOT NULL,
    scope_value       VARCHAR(64) NOT NULL,
    theme_name        VARCHAR(100) NOT NULL,
    entry_count       INTEGER NOT NULL,
    unique_user_count INTEGER NOT NULL,
    rank              INTEGER NOT NULL,
    delta_vs_previous DECIMAL(8,4),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uniq_community_theme_rollup
        UNIQUE (bucket_date, time_grain, scope_type, scope_value, theme_name)
);

CREATE INDEX IF NOT EXISTS idx_ctr_bucket_scope
    ON source.community_theme_rollups (bucket_date, time_grain, scope_type, scope_value);

CREATE TABLE IF NOT EXISTS source.community_mood_rollups (
    id                SERIAL PRIMARY KEY,
    bucket_date       DATE NOT NULL,
    time_grain        VARCHAR(16) NOT NULL,
    scope_type        VARCHAR(16) NOT NULL,
    scope_value       VARCHAR(64) NOT NULL,
    mood_name         VARCHAR(100) NOT NULL,
    entry_count       INTEGER NOT NULL,
    unique_user_count INTEGER NOT NULL,
    rank              INTEGER NOT NULL,
    delta_vs_previous DECIMAL(8,4),
    updated_at        TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uniq_community_mood_rollup
        UNIQUE (bucket_date, time_grain, scope_type, scope_value, mood_name)
);

CREATE INDEX IF NOT EXISTS idx_cmr_bucket_scope
    ON source.community_mood_rollups (bucket_date, time_grain, scope_type, scope_value);

CREATE TABLE IF NOT EXISTS source.community_summaries (
    id                 SERIAL PRIMARY KEY,
    bucket_date        DATE NOT NULL,
    time_grain         VARCHAR(16) NOT NULL,
    scope_type         VARCHAR(16) NOT NULL,
    scope_value        VARCHAR(64) NOT NULL,
    summary_text       TEXT NOT NULL,
    source_theme_names TEXT[] NOT NULL DEFAULT '{}',
    source_mood_names  TEXT[] NOT NULL DEFAULT '{}',
    generation_method  VARCHAR(32) NOT NULL DEFAULT 'template',
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uniq_community_summary
        UNIQUE (bucket_date, time_grain, scope_type, scope_value)
);

CREATE INDEX IF NOT EXISTS idx_cs_bucket_scope
    ON source.community_summaries (bucket_date, time_grain, scope_type, scope_value);

CREATE TABLE IF NOT EXISTS source.community_prompt_sets (
    id                 SERIAL PRIMARY KEY,
    bucket_date        DATE NOT NULL,
    time_grain         VARCHAR(16) NOT NULL,
    scope_type         VARCHAR(16) NOT NULL,
    scope_value        VARCHAR(64) NOT NULL,
    prompt_set_json    JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_theme_names TEXT[] NOT NULL DEFAULT '{}',
    source_mood_names  TEXT[] NOT NULL DEFAULT '{}',
    generation_method  VARCHAR(32) NOT NULL DEFAULT 'template',
    updated_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at         TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT uniq_community_prompt_set
        UNIQUE (bucket_date, time_grain, scope_type, scope_value)
);

CREATE INDEX IF NOT EXISTS idx_cps_bucket_scope
    ON source.community_prompt_sets (bucket_date, time_grain, scope_type, scope_value);

-- +goose Down

DROP TABLE IF EXISTS source.community_prompt_sets;
DROP TABLE IF EXISTS source.community_summaries;
DROP TABLE IF EXISTS source.community_mood_rollups;
DROP TABLE IF EXISTS source.community_theme_rollups;
DROP TABLE IF EXISTS source.journal_community_projections;

ALTER TABLE source.users
    DROP COLUMN IF EXISTS community_region_code,
    DROP COLUMN IF EXISTS community_country_code,
    DROP COLUMN IF EXISTS community_location_opt_in,
    DROP COLUMN IF EXISTS community_insights_opt_in;
