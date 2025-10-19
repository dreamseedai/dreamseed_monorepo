-- seedtest RLS policies and helpers
-- Apply order: helpers -> backfill -> enable RLS -> policies

-- 0) Context schema and helpers
CREATE SCHEMA IF NOT EXISTS seedtest;

CREATE OR REPLACE FUNCTION seedtest.current_org_id()
RETURNS int LANGUAGE plpgsql STABLE AS $$DECLARE v text;
BEGIN
  BEGIN
    v := current_setting('seedtest.org_id', true);
  EXCEPTION WHEN others THEN
    RETURN NULL;
  END;
  IF v IS NULL OR v = '' THEN
    RETURN NULL;
  END IF;
  RETURN v::int;
END $$;

CREATE OR REPLACE FUNCTION seedtest.is_admin()
RETURNS boolean LANGUAGE sql STABLE AS $$
  SELECT current_user IN ('seedtest_admin');$$;

-- 1) Backfill/augment org_id (example: responses from attempts)
ALTER TABLE IF EXISTS responses ADD COLUMN IF NOT EXISTS org_id int;
UPDATE responses r
SET org_id = a.org_id
FROM attempts a
WHERE r.attempt_id = a.id
  AND (r.org_id IS NULL OR r.org_id <> a.org_id);

-- Optionally enforce NOT NULL when data hygiene is complete
-- ALTER TABLE responses ALTER COLUMN org_id SET NOT NULL;

-- 2) Enable RLS
ALTER TABLE IF EXISTS attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS item_bank ENABLE ROW LEVEL SECURITY;

-- 3) attempts policies
DROP POLICY IF EXISTS attempts_policy_read ON attempts;
CREATE POLICY attempts_policy_read ON attempts
  FOR SELECT
  USING (
    seedtest.is_admin()
    OR org_id = seedtest.current_org_id()
    OR org_id IS NULL
  );

DROP POLICY IF EXISTS attempts_policy_write ON attempts;
CREATE POLICY attempts_policy_write ON attempts
  FOR INSERT, UPDATE
  USING (seedtest.is_admin() OR org_id = seedtest.current_org_id())
  WITH CHECK (
    seedtest.is_admin()
    OR org_id = seedtest.current_org_id()
  );

-- 4) responses policies
DROP POLICY IF EXISTS responses_policy_read ON responses;
CREATE POLICY responses_policy_read ON responses
  FOR SELECT
  USING (
    seedtest.is_admin()
    OR org_id = seedtest.current_org_id()
    OR org_id IS NULL
  );

DROP POLICY IF EXISTS responses_policy_write ON responses;
CREATE POLICY responses_policy_write ON responses
  FOR INSERT, UPDATE
  USING (seedtest.is_admin() OR org_id = seedtest.current_org_id())
  WITH CHECK (
    seedtest.is_admin()
    OR org_id = seedtest.current_org_id()
  );

-- 5) item_bank policies (owner_org_id)
DROP POLICY IF EXISTS item_bank_policy_read ON item_bank;
CREATE POLICY item_bank_policy_read ON item_bank
  FOR SELECT
  USING (
    seedtest.is_admin()
    OR owner_org_id = seedtest.current_org_id()
    OR owner_org_id IS NULL
  );

DROP POLICY IF EXISTS item_bank_policy_write ON item_bank;
CREATE POLICY item_bank_policy_write ON item_bank
  FOR INSERT, UPDATE
  USING (seedtest.is_admin() OR owner_org_id = seedtest.current_org_id())
  WITH CHECK (
    seedtest.is_admin()
    OR owner_org_id = seedtest.current_org_id()
  );


