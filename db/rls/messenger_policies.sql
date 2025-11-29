-- Row-Level Security policies for messenger tables
-- Ensures only participants can access conversation data within their zone/org
-- Prerequisites: Requires seedtest.current_org_id() and seedtest.is_admin() functions from rls_policies.sql

-- Safety guards
SET lock_timeout = '5s';
SET statement_timeout = '60s';
SET search_path TO public, seedtest;

-- Helper function to get current user ID from JWT claims
CREATE OR REPLACE FUNCTION seedtest.current_user_id()
RETURNS int LANGUAGE plpgsql STABLE AS $$
DECLARE v text;
BEGIN
  BEGIN
    v := current_setting('request.jwt.claims.user_id', true);
  EXCEPTION WHEN others THEN
    RETURN NULL;
  END;
  IF v IS NULL OR v = '' THEN
    RETURN NULL;
  END IF;
  RETURN v::int;
END
$$;

-- Helper function to get current zone ID from JWT claims
CREATE OR REPLACE FUNCTION seedtest.current_zone_id()
RETURNS int LANGUAGE plpgsql STABLE AS $$
DECLARE v text;
BEGIN
  BEGIN
    v := current_setting('request.jwt.claims.zone_id', true);
  EXCEPTION WHEN others THEN
    RETURN NULL;
  END;
  IF v IS NULL OR v = '' THEN
    RETURN NULL;
  END IF;
  RETURN v::int;
END
$$;

-- =============================================================================
-- 1. CONVERSATIONS TABLE
-- =============================================================================
-- Users can only see conversations where they are participants and within their zone/org

DO $$
BEGIN
  IF to_regclass('public.conversations') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE conversations ENABLE ROW LEVEL SECURITY';
    
    -- Drop existing policies if any
    EXECUTE 'DROP POLICY IF EXISTS conversations_select_policy ON conversations';
    EXECUTE 'DROP POLICY IF EXISTS conversations_insert_policy ON conversations';
    EXECUTE 'DROP POLICY IF EXISTS conversations_update_policy ON conversations';
    
    -- SELECT: Allow participants within same zone/org, or admins
    EXECUTE $P$
      CREATE POLICY conversations_select_policy ON conversations
        FOR SELECT
        USING (
          seedtest.is_admin()
          OR (
            (zone_id = seedtest.current_zone_id() OR zone_id IS NULL)
            AND (org_id = seedtest.current_org_id() OR org_id IS NULL)
            AND id IN (
              SELECT cp.conversation_id
              FROM conversation_participants AS cp
              WHERE cp.user_id = seedtest.current_user_id()
            )
          )
        )
    $P$;
    
    -- INSERT: Allow users to create conversations in their zone/org
    EXECUTE $P$
      CREATE POLICY conversations_insert_policy ON conversations
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin()
          OR (
            org_id = seedtest.current_org_id()
            AND (zone_id = seedtest.current_zone_id() OR zone_id IS NULL)
          )
        )
    $P$;
    
    -- UPDATE: Allow conversation admins or system admins
    EXECUTE $P$
      CREATE POLICY conversations_update_policy ON conversations
        FOR UPDATE
        USING (
          seedtest.is_admin()
          OR id IN (
            SELECT cp.conversation_id
            FROM conversation_participants AS cp
            WHERE cp.user_id = seedtest.current_user_id()
              AND cp.role = 'admin'
          )
        )
        WITH CHECK (
          seedtest.is_admin()
          OR id IN (
            SELECT cp.conversation_id
            FROM conversation_participants AS cp
            WHERE cp.user_id = seedtest.current_user_id()
              AND cp.role = 'admin'
          )
        )
    $P$;
  END IF;
END
$$;

-- =============================================================================
-- 2. CONVERSATION_PARTICIPANTS TABLE
-- =============================================================================
-- Participants can see other members of conversations they belong to

DO $$
BEGIN
  IF to_regclass('public.conversation_participants') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE conversation_participants ENABLE ROW LEVEL SECURITY';
    
    -- Drop existing policies if any
    EXECUTE 'DROP POLICY IF EXISTS participants_select_policy ON conversation_participants';
    EXECUTE 'DROP POLICY IF EXISTS participants_insert_policy ON conversation_participants';
    EXECUTE 'DROP POLICY IF EXISTS participants_update_policy ON conversation_participants';
    EXECUTE 'DROP POLICY IF EXISTS participants_delete_policy ON conversation_participants';
    
    -- SELECT: See members of conversations you're part of
    EXECUTE $P$
      CREATE POLICY participants_select_policy ON conversation_participants
        FOR SELECT
        USING (
          seedtest.is_admin()
          OR conversation_id IN (
            SELECT cp2.conversation_id
            FROM conversation_participants AS cp2
            WHERE cp2.user_id = seedtest.current_user_id()
          )
        )
    $P$;
    
    -- INSERT: Conversation admins can add participants
    EXECUTE $P$
      CREATE POLICY participants_insert_policy ON conversation_participants
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin()
          OR conversation_id IN (
            SELECT cp.conversation_id
            FROM conversation_participants AS cp
            WHERE cp.user_id = seedtest.current_user_id()
              AND cp.role = 'admin'
          )
        )
    $P$;
    
    -- UPDATE: Users can update their own participant record (e.g., last_read_at)
    EXECUTE $P$
      CREATE POLICY participants_update_policy ON conversation_participants
        FOR UPDATE
        USING (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
        WITH CHECK (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
    $P$;
    
    -- DELETE: Conversation admins can remove participants
    EXECUTE $P$
      CREATE POLICY participants_delete_policy ON conversation_participants
        FOR DELETE
        USING (
          seedtest.is_admin()
          OR conversation_id IN (
            SELECT cp.conversation_id
            FROM conversation_participants AS cp
            WHERE cp.user_id = seedtest.current_user_id()
              AND cp.role = 'admin'
          )
        )
    $P$;
  END IF;
END
$$;

-- =============================================================================
-- 3. MESSAGES TABLE
-- =============================================================================
-- Participants can only see messages in conversations they belong to

DO $$
BEGIN
  IF to_regclass('public.messages') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE messages ENABLE ROW LEVEL SECURITY';
    
    -- Drop existing policies if any
    EXECUTE 'DROP POLICY IF EXISTS messages_select_policy ON messages';
    EXECUTE 'DROP POLICY IF EXISTS messages_insert_policy ON messages';
    EXECUTE 'DROP POLICY IF EXISTS messages_update_policy ON messages';
    EXECUTE 'DROP POLICY IF EXISTS messages_delete_policy ON messages';
    
    -- SELECT: See messages in conversations you're part of (exclude soft-deleted)
    EXECUTE $P$
      CREATE POLICY messages_select_policy ON messages
        FOR SELECT
        USING (
          (deleted_at IS NULL OR seedtest.is_admin())
          AND (
            seedtest.is_admin()
            OR conversation_id IN (
              SELECT cp.conversation_id
              FROM conversation_participants AS cp
              WHERE cp.user_id = seedtest.current_user_id()
            )
          )
        )
    $P$;
    
    -- INSERT: Members can send messages to conversations they're part of
    EXECUTE $P$
      CREATE POLICY messages_insert_policy ON messages
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin()
          OR (
            sender_id = seedtest.current_user_id()
            AND conversation_id IN (
              SELECT cp.conversation_id
              FROM conversation_participants AS cp
              WHERE cp.user_id = seedtest.current_user_id()
            )
          )
        )
    $P$;
    
    -- UPDATE: Only sender can edit their own messages
    EXECUTE $P$
      CREATE POLICY messages_update_policy ON messages
        FOR UPDATE
        USING (
          seedtest.is_admin()
          OR sender_id = seedtest.current_user_id()
        )
        WITH CHECK (
          seedtest.is_admin()
          OR sender_id = seedtest.current_user_id()
        )
    $P$;
    
    -- DELETE: Sender or conversation admin can delete (soft delete)
    EXECUTE $P$
      CREATE POLICY messages_delete_policy ON messages
        FOR DELETE
        USING (
          seedtest.is_admin()
          OR sender_id = seedtest.current_user_id()
          OR conversation_id IN (
            SELECT cp.conversation_id
            FROM conversation_participants AS cp
            WHERE cp.user_id = seedtest.current_user_id()
              AND cp.role = 'admin'
          )
        )
    $P$;
  END IF;
END
$$;

-- =============================================================================
-- 4. READ_RECEIPTS TABLE
-- =============================================================================
-- Participants can see read receipts for messages in their conversations

DO $$
BEGIN
  IF to_regclass('public.read_receipts') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE read_receipts ENABLE ROW LEVEL SECURITY';
    
    -- Drop existing policies if any
    EXECUTE 'DROP POLICY IF EXISTS readreceipts_select_policy ON read_receipts';
    EXECUTE 'DROP POLICY IF EXISTS readreceipts_insert_policy ON read_receipts';
    EXECUTE 'DROP POLICY IF EXISTS readreceipts_delete_policy ON read_receipts';
    
    -- SELECT: See read receipts for messages in your conversations
    EXECUTE $P$
      CREATE POLICY readreceipts_select_policy ON read_receipts
        FOR SELECT
        USING (
          seedtest.is_admin()
          OR message_id IN (
            SELECT m.id
            FROM messages AS m
            JOIN conversation_participants AS cp ON m.conversation_id = cp.conversation_id
            WHERE cp.user_id = seedtest.current_user_id()
          )
        )
    $P$;
    
    -- INSERT: Users can mark messages as read
    EXECUTE $P$
      CREATE POLICY readreceipts_insert_policy ON read_receipts
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin()
          OR (
            user_id = seedtest.current_user_id()
            AND message_id IN (
              SELECT m.id
              FROM messages AS m
              JOIN conversation_participants AS cp ON m.conversation_id = cp.conversation_id
              WHERE cp.user_id = seedtest.current_user_id()
            )
          )
        )
    $P$;
    
    -- DELETE: Users can delete their own read receipts
    EXECUTE $P$
      CREATE POLICY readreceipts_delete_policy ON read_receipts
        FOR DELETE
        USING (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
    $P$;
  END IF;
END
$$;

-- =============================================================================
-- 5. NOTIFICATION_SETTINGS TABLE
-- =============================================================================
-- Users can only see and modify their own notification settings

DO $$
BEGIN
  IF to_regclass('public.notification_settings') IS NOT NULL THEN
    EXECUTE 'ALTER TABLE notification_settings ENABLE ROW LEVEL SECURITY';
    
    -- Drop existing policies if any
    EXECUTE 'DROP POLICY IF EXISTS notif_select_policy ON notification_settings';
    EXECUTE 'DROP POLICY IF EXISTS notif_insert_policy ON notification_settings';
    EXECUTE 'DROP POLICY IF EXISTS notif_update_policy ON notification_settings';
    EXECUTE 'DROP POLICY IF EXISTS notif_delete_policy ON notification_settings';
    
    -- SELECT: Users see only their own settings
    EXECUTE $P$
      CREATE POLICY notif_select_policy ON notification_settings
        FOR SELECT
        USING (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
    $P$;
    
    -- INSERT: Users can create their own settings
    EXECUTE $P$
      CREATE POLICY notif_insert_policy ON notification_settings
        FOR INSERT
        WITH CHECK (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
    $P$;
    
    -- UPDATE: Users can update their own settings
    EXECUTE $P$
      CREATE POLICY notif_update_policy ON notification_settings
        FOR UPDATE
        USING (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
        WITH CHECK (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
    $P$;
    
    -- DELETE: Users can delete their own settings
    EXECUTE $P$
      CREATE POLICY notif_delete_policy ON notification_settings
        FOR DELETE
        USING (
          seedtest.is_admin()
          OR user_id = seedtest.current_user_id()
        )
    $P$;
  END IF;
END
$$;

-- =============================================================================
-- VERIFICATION QUERIES (for testing)
-- =============================================================================
-- Uncomment to test after applying policies:

/*
-- Set test context (replace with actual values)
SET request.jwt.claims.user_id = '1';
SET request.jwt.claims.zone_id = '550e8400-e29b-41d4-a716-446655440000';
SET seedtest.org_id = '1';

-- Test queries
SELECT COUNT(*) FROM conversations;
SELECT COUNT(*) FROM conversation_participants;
SELECT COUNT(*) FROM messages WHERE deleted_at IS NULL;
SELECT COUNT(*) FROM read_receipts;
SELECT COUNT(*) FROM notification_settings;

-- Reset context
RESET request.jwt.claims.user_id;
RESET request.jwt.claims.zone_id;
RESET seedtest.org_id;
*/
