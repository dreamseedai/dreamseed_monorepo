-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- DreamSeed Item Tables (IRT/CAT Support)
-- Migration: 20251120_item_tables_irt_cat.sql
-- 
-- Purpose: Add item management tables with IRT parameters
-- Tables: items, item_choices, item_pools, item_pool_membership
-- 
-- These tables support:
-- - 3PL IRT model (a, b, c parameters)
-- - Multiple choice questions
-- - Item pooling and organization
-- - Integration with AdaptiveEngine
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ─────────────────────────────────────────
-- 1. items (Core question/item table)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS items (
    id              BIGSERIAL PRIMARY KEY,
    topic           VARCHAR(255),                 -- Subject area: 'algebra', 'geometry', etc.
    question_text   TEXT NOT NULL,                -- The actual question
    correct_answer  TEXT,                         -- Expected answer (for auto-grading)
    explanation     TEXT,                         -- Solution explanation
    
    -- IRT Parameters (3PL Model)
    a               NUMERIC(6,3) NOT NULL,        -- Discrimination parameter (0.5-2.5)
    b               NUMERIC(6,3) NOT NULL,        -- Difficulty parameter (-3 to +3)
    c               NUMERIC(6,3) NOT NULL,        -- Guessing parameter (0-0.3)
    
    meta            JSONB,                        -- Question type, tags, standards, etc.
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_items_topic ON items(topic);
CREATE INDEX IF NOT EXISTS idx_items_difficulty ON items(b);  -- For filtering by difficulty

COMMENT ON TABLE items IS 'Question items with IRT parameters for adaptive testing';
COMMENT ON COLUMN items.a IS 'IRT discrimination parameter: how well item distinguishes ability levels';
COMMENT ON COLUMN items.b IS 'IRT difficulty parameter: ability level at which P(correct)=0.5';
COMMENT ON COLUMN items.c IS 'IRT guessing parameter: probability of guessing correctly';
COMMENT ON COLUMN items.topic IS 'Subject/topic area for content filtering';

-- ─────────────────────────────────────────
-- 2. item_choices (Multiple choice options)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS item_choices (
    id              BIGSERIAL PRIMARY KEY,
    item_id         BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    choice_num      INTEGER NOT NULL,             -- 1, 2, 3, 4, 5
    choice_text     TEXT NOT NULL,                -- The choice text
    is_correct      INTEGER NOT NULL DEFAULT 0,   -- 0 or 1 (SQLite compatibility)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_item_choices_item_id ON item_choices(item_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_item_choices_unique ON item_choices(item_id, choice_num);

COMMENT ON TABLE item_choices IS 'Multiple choice options for items';
COMMENT ON COLUMN item_choices.choice_num IS 'Choice number (1-based index)';
COMMENT ON COLUMN item_choices.is_correct IS 'Whether this is the correct answer (0 or 1)';

-- ─────────────────────────────────────────
-- 3. item_pools (Named collections of items)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS item_pools (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE,
    description     TEXT,
    subject         VARCHAR(100),
    grade_level     VARCHAR(20),
    meta            JSONB,                        -- Pool configuration, constraints
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_item_pools_subject ON item_pools(subject);
CREATE INDEX IF NOT EXISTS idx_item_pools_grade ON item_pools(grade_level);

COMMENT ON TABLE item_pools IS 'Named collections of items for organizing questions';
COMMENT ON COLUMN item_pools.name IS 'Pool name (e.g., "Grade 8 Math Placement Test")';
COMMENT ON COLUMN item_pools.meta IS 'Pool configuration: max_items, time_limit, etc.';

-- ─────────────────────────────────────────
-- 4. item_pool_membership (Items <-> Pools)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS item_pool_membership (
    item_id         BIGINT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    pool_id         INTEGER NOT NULL REFERENCES item_pools(id) ON DELETE CASCADE,
    sequence        INTEGER,                      -- Optional ordering within pool
    weight          NUMERIC(5,2) DEFAULT 1.0,     -- Optional item weight/importance
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (item_id, pool_id)
);

CREATE INDEX IF NOT EXISTS idx_item_pool_membership_pool_id ON item_pool_membership(pool_id);
CREATE INDEX IF NOT EXISTS idx_item_pool_membership_sequence ON item_pool_membership(pool_id, sequence);

COMMENT ON TABLE item_pool_membership IS 'Many-to-many relationship between items and pools';
COMMENT ON COLUMN item_pool_membership.sequence IS 'Optional ordering for fixed-sequence tests';
COMMENT ON COLUMN item_pool_membership.weight IS 'Item weight for selection probability';

-- ─────────────────────────────────────────
-- 5. Update attempts table to link to items
-- ─────────────────────────────────────────
-- Note: This assumes attempts.item_id already exists but may not have FK constraint
-- If it doesn't exist, this will fail - check your schema first

DO $$ 
BEGIN
    -- Add foreign key if column exists but constraint doesn't
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'attempts' AND column_name = 'item_id'
    ) THEN
        -- Try to add constraint (will fail if already exists, which is fine)
        BEGIN
            ALTER TABLE attempts
            ADD CONSTRAINT fk_attempts_item_id 
            FOREIGN KEY (item_id) REFERENCES items(id) ON DELETE SET NULL;
        EXCEPTION WHEN duplicate_object THEN
            NULL; -- Constraint already exists, ignore
        END;
    END IF;
END $$;

-- ─────────────────────────────────────────
-- 6. Sample Data (Optional)
-- ─────────────────────────────────────────
-- Uncomment to insert sample items for testing

/*
-- Easy algebra item
INSERT INTO items (topic, question_text, correct_answer, explanation, a, b, c, meta)
VALUES (
    'algebra',
    'Solve for x: 2x + 5 = 13',
    '4',
    'Subtract 5 from both sides: 2x = 8. Divide by 2: x = 4',
    1.2,   -- Good discrimination
    -0.5,  -- Easy (negative b)
    0.2,   -- Low guessing
    '{"difficulty_label": "easy", "grade_level": 7}'::jsonb
);

-- Medium geometry item
INSERT INTO items (topic, question_text, correct_answer, explanation, a, b, c, meta)
VALUES (
    'geometry',
    'What is the area of a circle with radius 5?',
    '78.54',
    'Use formula A = πr². A = π × 5² = π × 25 ≈ 78.54',
    1.5,   -- High discrimination
    0.0,   -- Medium difficulty
    0.2,   -- Low guessing
    '{"difficulty_label": "medium", "grade_level": 8}'::jsonb
);

-- Hard calculus item
INSERT INTO items (topic, question_text, correct_answer, explanation, a, b, c, meta)
VALUES (
    'calculus',
    'Find the derivative of f(x) = x³ + 2x² - 5x + 7',
    '3x² + 4x - 5',
    'Apply power rule: f''(x) = 3x² + 4x - 5',
    1.8,   -- Very high discrimination
    1.5,   -- Hard (positive b)
    0.1,   -- Very low guessing
    '{"difficulty_label": "hard", "grade_level": 12}'::jsonb
);

-- Create sample pool
INSERT INTO item_pools (name, description, subject, grade_level)
VALUES (
    'Grade 8 Math Diagnostic',
    'Placement test for incoming 8th grade students',
    'math',
    '8'
);

-- Add items to pool
INSERT INTO item_pool_membership (item_id, pool_id, sequence)
VALUES 
    (1, 1, 1),
    (2, 1, 2);
*/

-- ─────────────────────────────────────────
-- Migration metadata
-- ─────────────────────────────────────────
INSERT INTO schema_migrations (migration_name) 
VALUES ('20251120_item_tables_irt_cat')
ON CONFLICT (migration_name) DO NOTHING;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- End of migration
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
