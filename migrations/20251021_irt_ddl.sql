-- IRT updater supporting objects (PostgreSQL)
-- Staging view for per-item stats consumed by the batch updater
-- Adjust table/column names as needed, or materialize into a table if preferred.

-- Example base tables (for reference only):
--   items(question_id PRIMARY KEY, a DOUBLE PRECISION, b DOUBLE PRECISION, c DOUBLE PRECISION, topic TEXT)
--   responses(id SERIAL PRIMARY KEY, examinee_id TEXT, question_id TEXT, is_correct BOOLEAN, answered_at TIMESTAMPTZ)
--   questions(question_id PRIMARY KEY, solution_html TEXT, topic TEXT)

--   AVG(CASE WHEN r.is_correct THEN 1.0 ELSE 0.0 END) AS correct_rate,
--   COUNT(*)::bigint AS n_responses,
--   NULL::double precision AS log_likelihood,  -- optionally compute if you maintain per-item LL
--   NULL::double precision AS fisher_info_theta0 -- optional: fisher information at theta=0

--   NULL::double precision AS log_likelihood,
--   NULL::double precision AS fisher_info_theta0

-- 2) Ensure items table exists and has a unique key on question_id for upserts
-- CREATE TABLE IF NOT EXISTS items (
--   question_id TEXT PRIMARY KEY,
--   a DOUBLE PRECISION NOT NULL,
--   b DOUBLE PRECISION NOT NULL,
--   c DOUBLE PRECISION NOT NULL,
--   topic TEXT
-- );

          log_likelihood DOUBLE PRECISION,
          fisher_info_theta0 DOUBLE PRECISION,
CREATE TABLE IF NOT EXISTS item_param_changes (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL,
  changed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  question_id TEXT NOT NULL,
  old_a DOUBLE PRECISION,
  old_b DOUBLE PRECISION,
  old_c DOUBLE PRECISION,
  new_a DOUBLE PRECISION NOT NULL,
  new_b DOUBLE PRECISION NOT NULL,
  new_c DOUBLE PRECISION NOT NULL,
  n_responses BIGINT,
  log_likelihood DOUBLE PRECISION
);
CREATE INDEX IF NOT EXISTS idx_item_param_changes_run ON item_param_changes(run_id);
CREATE INDEX IF NOT EXISTS idx_item_param_changes_q ON item_param_changes(question_id);

-- 4) Grant minimal permissions (adjust roles)
-- GRANT SELECT ON irt_item_stats TO app_reader;
-- GRANT SELECT, INSERT, UPDATE ON items TO app_writer;
-- GRANT INSERT ON item_param_changes TO app_writer;
