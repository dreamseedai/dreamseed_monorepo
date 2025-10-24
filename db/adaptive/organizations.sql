-- 0. Enable pgcrypto for UUID if needed
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Organizations
DROP TABLE IF EXISTS organizations CASCADE;
CREATE TABLE organizations (
  org_id       SERIAL PRIMARY KEY,
  name         TEXT NOT NULL,
  type         TEXT,
  region       TEXT
);

