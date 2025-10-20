-- 안전 가드
SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path TO public, seedtest;

-- 0) 스키마/헬퍼
CREATE SCHEMA IF NOT EXISTS seedtest;

CREATE OR REPLACE FUNCTION seedtest.current_org_id()
RETURNS int LANGUAGE plpgsql STABLE AS $RLS$
DECLARE v text;
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
END
$RLS$;

CREATE OR REPLACE FUNCTION seedtest.is_admin()
RETURNS boolean LANGUAGE sql STABLE AS $RLS$
  SELECT current_user IN ('seedtest_admin');
$RLS$;

-- 1) 누락 컬럼 보강 (존재하면 무시)
ALTER TABLE IF EXISTS attempts   ADD COLUMN IF NOT EXISTS org_id int;
ALTER TABLE IF EXISTS responses  ADD COLUMN IF NOT EXISTS org_id int;
ALTER TABLE IF EXISTS item_bank  ADD COLUMN IF NOT EXISTS owner_org_id int;

-- 1-1) responses.org_id 백필 (attempts가 있을 때만)
DO $RLS$
BEGIN
  IF to_regclass('public.responses') IS NOT NULL
     AND to_regclass('public.attempts') IS NOT NULL THEN
    EXECUTE $Q$
      UPDATE responses r
         SET org_id = a.org_id
        FROM attempts a
       WHERE r.attempt_id = a.id
         AND (r.org_id IS NULL OR r.org_id <> a.org_id)
    $Q$;
  END IF;
END
$RLS$;

-- 2) 인덱스 (존재하면 무시)
DO $RLS$
BEGIN
  IF to_regclass('public.attempts') IS NOT NULL THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_attempts_org_id  ON attempts(org_id)';
  END IF;
  IF to_regclass('public.responses') IS NOT NULL THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_responses_org_id ON responses(org_id)';
  END IF;
  IF to_regclass('public.item_bank') IS NOT NULL THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_item_bank_owner ON item_bank(owner_org_id)';
  END IF;
END
$RLS$;

-- 3) RLS ENABLE + 정책 (테이블이 있을 때만)
-- attempts
DO $RLS$
BEGIN
  IF to_regclass('public.attempts') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE attempts ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS attempts_policy_read   ON attempts';
    EXECUTE 'DROP POLICY IF EXISTS attempts_policy_insert ON attempts';
    EXECUTE 'DROP POLICY IF EXISTS attempts_policy_update ON attempts';
    EXECUTE $P$
      CREATE POLICY attempts_policy_read ON attempts
        FOR SELECT USING (
          seedtest.is_admin()
          OR org_id = seedtest.current_org_id()
          OR org_id IS NULL
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY attempts_policy_insert ON attempts
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY attempts_policy_update ON attempts
        FOR UPDATE
        USING (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
  END IF;
END
$RLS$;

-- responses
DO $RLS$
BEGIN
  IF to_regclass('public.responses') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE responses ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS responses_policy_read   ON responses';
    EXECUTE 'DROP POLICY IF EXISTS responses_policy_insert ON responses';
    EXECUTE 'DROP POLICY IF EXISTS responses_policy_update ON responses';
    EXECUTE $P$
      CREATE POLICY responses_policy_read ON responses
        FOR SELECT USING (
          seedtest.is_admin()
          OR org_id = seedtest.current_org_id()
          OR org_id IS NULL
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY responses_policy_insert ON responses
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY responses_policy_update ON responses
        FOR UPDATE
        USING (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
  END IF;
END
$RLS$;

-- item_bank (owner_org_id 기준)
DO $RLS$
BEGIN
  IF to_regclass('public.item_bank') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE item_bank ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS item_bank_policy_read   ON item_bank';
    EXECUTE 'DROP POLICY IF EXISTS item_bank_policy_insert ON item_bank';
    EXECUTE 'DROP POLICY IF EXISTS item_bank_policy_update ON item_bank';
    EXECUTE $P$
      CREATE POLICY item_bank_policy_read ON item_bank
        FOR SELECT USING (
          seedtest.is_admin()
          OR owner_org_id = seedtest.current_org_id()
          OR owner_org_id IS NULL
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY item_bank_policy_insert ON item_bank
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY item_bank_policy_update ON item_bank
        FOR UPDATE
        USING (
          seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
        )
        WITH CHECK (
          seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
        )
    $P$;
  END IF;
END
$RLS$;
-- 안전 가드
SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path TO public, seedtest;

-- 0) 스키마/헬퍼
CREATE SCHEMA IF NOT EXISTS seedtest;

CREATE OR REPLACE FUNCTION seedtest.current_org_id()
RETURNS int LANGUAGE plpgsql STABLE AS $RLS$
DECLARE v text;
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
END
$RLS$;

CREATE OR REPLACE FUNCTION seedtest.is_admin()
RETURNS boolean LANGUAGE sql STABLE AS $RLS$
  SELECT current_user IN ('seedtest_admin');
$RLS$;

-- 1) 누락 컬럼 보강 (존재하면 무시)
ALTER TABLE IF EXISTS attempts   ADD COLUMN IF NOT EXISTS org_id int;
ALTER TABLE IF EXISTS responses  ADD COLUMN IF NOT EXISTS org_id int;
ALTER TABLE IF EXISTS item_bank  ADD COLUMN IF NOT EXISTS owner_org_id int;

-- 1-1) responses.org_id 백필 (attempts가 있을 때만)
DO $RLS$
BEGIN
  IF to_regclass('public.responses') IS NOT NULL
     AND to_regclass('public.attempts') IS NOT NULL THEN
    EXECUTE $Q$
      UPDATE responses r
         SET org_id = a.org_id
        FROM attempts a
       WHERE r.attempt_id = a.id
         AND (r.org_id IS NULL OR r.org_id <> a.org_id)
    $Q$;
  END IF;
END
$RLS$;

-- 2) 인덱스 (존재하면 무시)
DO $RLS$
BEGIN
  IF to_regclass('public.attempts') IS NOT NULL THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_attempts_org_id  ON attempts(org_id)';
  END IF;
  IF to_regclass('public.responses') IS NOT NULL THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_responses_org_id ON responses(org_id)';
  END IF;
  IF to_regclass('public.item_bank') IS NOT NULL THEN
    EXECUTE 'CREATE INDEX IF NOT EXISTS idx_item_bank_owner ON item_bank(owner_org_id)';
  END IF;
END
$RLS$;

-- 3) RLS ENABLE + 정책 (테이블이 있을 때만)
-- attempts
DO $RLS$
BEGIN
  IF to_regclass('public.attempts') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE attempts ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS attempts_policy_read   ON attempts';
    EXECUTE 'DROP POLICY IF EXISTS attempts_policy_insert ON attempts';
    EXECUTE 'DROP POLICY IF EXISTS attempts_policy_update ON attempts';
    EXECUTE $P$
      CREATE POLICY attempts_policy_read ON attempts
        FOR SELECT USING (
          seedtest.is_admin()
          OR org_id = seedtest.current_org_id()
          OR org_id IS NULL
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY attempts_policy_insert ON attempts
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY attempts_policy_update ON attempts
        FOR UPDATE
        USING (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
  END IF;
END
$RLS$;

-- responses
DO $RLS$
BEGIN
  IF to_regclass('public.responses') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE responses ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS responses_policy_read   ON responses';
    EXECUTE 'DROP POLICY IF EXISTS responses_policy_insert ON responses';
    EXECUTE 'DROP POLICY IF EXISTS responses_policy_update ON responses';
    EXECUTE $P$
      CREATE POLICY responses_policy_read ON responses
        FOR SELECT USING (
          seedtest.is_admin()
          OR org_id = seedtest.current_org_id()
          OR org_id IS NULL
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY responses_policy_insert ON responses
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY responses_policy_update ON responses
        FOR UPDATE
        USING (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
        WITH CHECK (
          seedtest.is_admin() OR org_id = seedtest.current_org_id()
        )
    $P$;
  END IF;
END
$RLS$;

-- item_bank (owner_org_id 기준)
DO $RLS$
BEGIN
  IF to_regclass('public.item_bank') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE item_bank ENABLE ROW LEVEL SECURITY';
    EXECUTE 'DROP POLICY IF EXISTS item_bank_policy_read   ON item_bank';
    EXECUTE 'DROP POLICY IF EXISTS item_bank_policy_insert ON item_bank';
    EXECUTE 'DROP POLICY IF EXISTS item_bank_policy_update ON item_bank';
    EXECUTE $P$
      CREATE POLICY item_bank_policy_read ON item_bank
        FOR SELECT USING (
          seedtest.is_admin()
          OR owner_org_id = seedtest.current_org_id()
          OR owner_org_id IS NULL
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY item_bank_policy_insert ON item_bank
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
        )
    $P$;
    EXECUTE $P$
      CREATE POLICY item_bank_policy_update ON item_bank
        FOR UPDATE
        USING (
          seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
        )
        WITH CHECK (
          seedtest.is_admin() OR owner_org_id = seedtest.current_org_id()
        )
    $P$;
  END IF;
END
$RLS$;

