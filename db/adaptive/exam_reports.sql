-- Stores full JSON reports for exam sessions for audits/analytics
CREATE TABLE IF NOT EXISTS exam_reports (
  session_id TEXT PRIMARY KEY,
  exam_id INTEGER,
  user_id INTEGER,
  report_json JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
