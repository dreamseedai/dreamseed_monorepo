-- Shadow table for staging updated IRT parameters before promotion
CREATE TABLE IF NOT EXISTS item_bank_shadow (
  id TEXT PRIMARY KEY,
  irt_a DOUBLE PRECISION,
  irt_b DOUBLE PRECISION,
  irt_c DOUBLE PRECISION,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
