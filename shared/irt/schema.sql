-- ==============================================================================
-- IRT Drift Monitoring System Schema
-- ==============================================================================
-- Purpose: Item Response Theory calibration, drift detection, DIF monitoring
-- Supports: Multi-language (en/ko/zh-Hans/zh-Hant), multi-tenant, PII masking
-- ==============================================================================

-- SCHEMA: shared_irt
CREATE SCHEMA IF NOT EXISTS shared_irt;

-- ==============================================================================
-- Items Master Table
-- ==============================================================================
-- Stores all test items with rich content (TipTap + MathLive format)
CREATE TABLE IF NOT EXISTS shared_irt.items (
  id                  BIGSERIAL PRIMARY KEY,
  id_str              TEXT UNIQUE,                        -- External/legacy identifier
  bank_id             TEXT NOT NULL,                      -- Pool/bank identifier (subject/country/language)
  lang                TEXT NOT NULL CHECK (lang IN ('en','ko','zh-Hans','zh-Hant')),
  stem_rich           JSONB,                              -- TipTap + MathLive rich text structure
  options_rich        JSONB,                              -- MCQ options in rich format
  answer_key          JSONB,                              -- Common answer representation (MCQ/fill-in/essay)
  topic_tags          TEXT[] DEFAULT '{}',                -- Topic hierarchy level 1
  subtopic_tags       TEXT[] DEFAULT '{}',                -- Topic hierarchy level 2
  curriculum_tags     TEXT[] DEFAULT '{}',                -- Curriculum alignment tags
  metadata            JSONB DEFAULT '{}',                 -- Flexible metadata
  is_anchor           BOOLEAN DEFAULT FALSE,              -- Anchor item for equating
  exposure_count      INTEGER DEFAULT 0,                  -- Item exposure tracking
  created_at          TIMESTAMPTZ DEFAULT now(),
  updated_at          TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE shared_irt.items IS 'Master item bank with rich content support';
COMMENT ON COLUMN shared_irt.items.is_anchor IS 'Anchor items have stable parameters for equating';
COMMENT ON COLUMN shared_irt.items.exposure_count IS 'Incremented on each administration';

-- ==============================================================================
-- Current Item Parameters
-- ==============================================================================
-- Most recent/valid IRT parameters (1PL/2PL/3PL models)
CREATE TABLE IF NOT EXISTS shared_irt.item_parameters_current (
  item_id             BIGINT PRIMARY KEY REFERENCES shared_irt.items(id) ON DELETE CASCADE,
  model               TEXT NOT NULL CHECK (model IN ('1PL','2PL','3PL')),
  a                   DOUBLE PRECISION,                   -- Discrimination (2PL/3PL)
  b                   DOUBLE PRECISION NOT NULL,          -- Difficulty
  c                   DOUBLE PRECISION,                   -- Guessing (3PL)
  a_se                DOUBLE PRECISION,                   -- Standard error for a
  b_se                DOUBLE PRECISION,                   -- Standard error for b
  c_se                DOUBLE PRECISION,                   -- Standard error for c
  theta_min           DOUBLE PRECISION DEFAULT -4.0,      -- Ability range lower bound
  theta_max           DOUBLE PRECISION DEFAULT  4.0,      -- Ability range upper bound
  version             INTEGER NOT NULL DEFAULT 1,         -- Parameter version number
  effective_from      TIMESTAMPTZ NOT NULL DEFAULT now(), -- When these params become active
  note                TEXT,                               -- Calibration notes
  updated_at          TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE shared_irt.item_parameters_current IS 'Current active IRT parameters';
COMMENT ON COLUMN shared_irt.item_parameters_current.version IS 'Incremented on parameter updates';

-- ==============================================================================
-- Windows (Observation Periods)
-- ==============================================================================
-- Time windows for cohort-based calibration and drift analysis
CREATE TABLE IF NOT EXISTS shared_irt.windows (
  id                  BIGSERIAL PRIMARY KEY,
  label               TEXT NOT NULL,                      -- e.g., '2025-10 monthly'
  start_at            TIMESTAMPTZ NOT NULL,
  end_at              TIMESTAMPTZ NOT NULL,
  population_tags     TEXT[] DEFAULT '{}',                -- Cohort/country/language/subscription filters
  created_at          TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT windows_label_unique UNIQUE (label),
  CONSTRAINT windows_dates_valid CHECK (end_at > start_at)
);

COMMENT ON TABLE shared_irt.windows IS 'Time windows for calibration cohorts';
COMMENT ON COLUMN shared_irt.windows.population_tags IS 'Filters applied to select calibration sample';

-- ==============================================================================
-- Item Calibration History
-- ==============================================================================
-- Per-window calibration results with drift detection flags
CREATE TABLE IF NOT EXISTS shared_irt.item_calibration (
  id                  BIGSERIAL PRIMARY KEY,
  item_id             BIGINT NOT NULL REFERENCES shared_irt.items(id) ON DELETE CASCADE,
  window_id           BIGINT NOT NULL REFERENCES shared_irt.windows(id) ON DELETE CASCADE,
  model               TEXT NOT NULL CHECK (model IN ('1PL','2PL','3PL')),
  a_hat               DOUBLE PRECISION,                   -- Estimated discrimination
  b_hat               DOUBLE PRECISION NOT NULL,          -- Estimated difficulty
  c_hat               DOUBLE PRECISION,                   -- Estimated guessing
  a_ci_low            DOUBLE PRECISION,                   -- 95% CI lower bound for a
  a_ci_high           DOUBLE PRECISION,                   -- 95% CI upper bound for a
  b_ci_low            DOUBLE PRECISION,                   -- 95% CI lower bound for b
  b_ci_high           DOUBLE PRECISION,                   -- 95% CI upper bound for b
  c_ci_low            DOUBLE PRECISION,                   -- 95% CI lower bound for c
  c_ci_high           DOUBLE PRECISION,                   -- 95% CI upper bound for c
  n_responses         INTEGER NOT NULL,                   -- Sample size for this calibration
  loglik              DOUBLE PRECISION,                   -- Model log-likelihood
  drift_flag          TEXT DEFAULT NULL,                  -- 'a','b','c','DIF','INFO' if drift detected
  dif_metadata        JSONB DEFAULT '{}',                 -- DIF analysis: group Δb, Bayes Factor, p-values
  created_at          TIMESTAMPTZ DEFAULT now(),
  CONSTRAINT item_calibration_window_unique UNIQUE (item_id, window_id)
);

COMMENT ON TABLE shared_irt.item_calibration IS 'Historical calibration results per window';
COMMENT ON COLUMN shared_irt.item_calibration.drift_flag IS 'Type of drift detected (a/b/c/DIF/INFO)';
COMMENT ON COLUMN shared_irt.item_calibration.dif_metadata IS 'Differential Item Functioning analysis results';

-- ==============================================================================
-- Drift Alerts
-- ==============================================================================
-- Active alerts for parameter drift requiring review
CREATE TABLE IF NOT EXISTS shared_irt.drift_alerts (
  id                  BIGSERIAL PRIMARY KEY,
  item_id             BIGINT NOT NULL REFERENCES shared_irt.items(id) ON DELETE CASCADE,
  window_id           BIGINT NOT NULL REFERENCES shared_irt.windows(id) ON DELETE CASCADE,
  metric              TEXT NOT NULL,                      -- e.g., 'Δb','Δa','Δc','DIF','INFO'
  value               DOUBLE PRECISION,                   -- Magnitude of drift
  threshold           DOUBLE PRECISION,                   -- Threshold that was exceeded
  severity            TEXT CHECK (severity IN ('low','medium','high')) NOT NULL,
  message             TEXT,                               -- Human-readable alert message
  resolved_at         TIMESTAMPTZ,                        -- When alert was acknowledged/resolved
  created_at          TIMESTAMPTZ DEFAULT now()
);

COMMENT ON TABLE shared_irt.drift_alerts IS 'Active drift alerts requiring review';
COMMENT ON COLUMN shared_irt.drift_alerts.metric IS 'Drift metric: Δb (difficulty shift), DIF (group bias), INFO (information curve change)';
COMMENT ON COLUMN shared_irt.drift_alerts.resolved_at IS 'NULL means alert is still active';

-- ==============================================================================
-- Item Responses (Anonymized, Multi-tenant)
-- ==============================================================================
-- Raw response data with PII masking
CREATE TABLE IF NOT EXISTS shared_irt.item_responses (
  id                  BIGSERIAL PRIMARY KEY,
  org_id              TEXT NOT NULL,                      -- Multi-tenant organization ID
  user_id_hash        TEXT NOT NULL,                      -- Hashed/anonymized user ID (PII masked)
  session_id          TEXT,                               -- Test session identifier
  item_id             BIGINT NOT NULL REFERENCES shared_irt.items(id) ON DELETE CASCADE,
  started_at          TIMESTAMPTZ,                        -- When item was presented
  answered_at         TIMESTAMPTZ NOT NULL DEFAULT now(), -- When response was submitted
  is_correct          BOOLEAN,                            -- Binary scoring (MCQ)
  score               DOUBLE PRECISION,                   -- Partial credit scoring (essay/constructed response)
  response_payload    JSONB DEFAULT '{}',                 -- Raw response data
  lang                TEXT NOT NULL CHECK (lang IN ('en','ko','zh-Hans','zh-Hant')),
  extra               JSONB DEFAULT '{}'                  -- Flexible metadata (device, browser, etc.)
);

COMMENT ON TABLE shared_irt.item_responses IS 'Anonymized item response data';
COMMENT ON COLUMN shared_irt.item_responses.user_id_hash IS 'PII-masked user identifier';
COMMENT ON COLUMN shared_irt.item_responses.score IS 'For partial credit models (polytomous IRT)';

-- ==============================================================================
-- Performance Indexes
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_item_responses_item 
  ON shared_irt.item_responses(item_id);

CREATE INDEX IF NOT EXISTS idx_item_responses_window 
  ON shared_irt.item_responses(answered_at);

CREATE INDEX IF NOT EXISTS idx_item_responses_org_user 
  ON shared_irt.item_responses(org_id, user_id_hash);

CREATE INDEX IF NOT EXISTS idx_items_bank_lang 
  ON shared_irt.items(bank_id, lang);

CREATE INDEX IF NOT EXISTS idx_drift_alerts_unresolved 
  ON shared_irt.drift_alerts(item_id, window_id) 
  WHERE resolved_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_item_calibration_item_window 
  ON shared_irt.item_calibration(item_id, window_id);

-- ==============================================================================
-- Utility Views
-- ==============================================================================

-- View: Items with current parameters
CREATE OR REPLACE VIEW shared_irt.v_items_with_params AS
SELECT 
  i.id,
  i.id_str,
  i.bank_id,
  i.lang,
  i.topic_tags,
  i.subtopic_tags,
  i.is_anchor,
  i.exposure_count,
  p.model,
  p.a,
  p.b,
  p.c,
  p.a_se,
  p.b_se,
  p.c_se,
  p.version AS param_version,
  p.effective_from,
  i.created_at,
  i.updated_at
FROM shared_irt.items i
LEFT JOIN shared_irt.item_parameters_current p ON i.id = p.item_id;

COMMENT ON VIEW shared_irt.v_items_with_params IS 'Convenient view of items with their current IRT parameters';

-- View: Active drift alerts
CREATE OR REPLACE VIEW shared_irt.v_active_drift_alerts AS
SELECT 
  da.id,
  da.item_id,
  i.id_str,
  i.bank_id,
  da.window_id,
  w.label AS window_label,
  da.metric,
  da.value,
  da.threshold,
  da.severity,
  da.message,
  da.created_at
FROM shared_irt.drift_alerts da
JOIN shared_irt.items i ON da.item_id = i.id
JOIN shared_irt.windows w ON da.window_id = w.id
WHERE da.resolved_at IS NULL
ORDER BY da.severity DESC, da.created_at DESC;

COMMENT ON VIEW shared_irt.v_active_drift_alerts IS 'All unresolved drift alerts';
