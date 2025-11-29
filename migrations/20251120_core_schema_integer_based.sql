-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- DreamSeed Core Schema (INTEGER-based)
-- Migration: 20251120_core_schema_integer_based.sql
-- 
-- Purpose: Establishes core entity tables for CAT system
-- Entities: Organizations, Users, Teachers, Students, Classes, 
--           ExamSessions, Attempts, Student-Classroom junction
--
-- ⚠️  WARNING: Review existing schema before applying
-- ⚠️  Some tables may already exist - merge carefully
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- ─────────────────────────────────────────
-- 0. organizations (Multi-tenancy support)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS organizations (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    type            VARCHAR(50),              -- 'school', 'academy', 'tutoring_center'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE organizations IS 'Multi-tenant organization entities (schools, academies)';
COMMENT ON COLUMN organizations.type IS 'Organization type: school, academy, tutoring_center';

-- ─────────────────────────────────────────
-- 1. users (Unified account table)
-- ─────────────────────────────────────────
-- Note: This may conflict with existing users table
-- If users table exists, add missing columns instead of recreating
CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    org_id          INTEGER REFERENCES organizations(id),
    email           VARCHAR(255) NOT NULL UNIQUE,
    username        VARCHAR(255) UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL,     -- 'student','teacher','parent','admin','super_admin'
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_org_id ON users(org_id);
CREATE INDEX IF NOT EXISTS idx_users_role   ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_email  ON users(email);

COMMENT ON TABLE users IS 'Unified user accounts supporting multiple roles';
COMMENT ON COLUMN users.role IS 'User role: student, teacher, parent, admin, super_admin';
COMMENT ON COLUMN users.org_id IS 'Optional organization affiliation for multi-tenancy';

-- ─────────────────────────────────────────
-- 2. teachers (Teacher profile extension)
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teachers (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    org_id      INTEGER REFERENCES organizations(id),
    subject     VARCHAR(100),
    meta        JSONB,                        -- Flexible metadata (certifications, bio, etc.)
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_teachers_org_id  ON teachers(org_id);
CREATE INDEX IF NOT EXISTS idx_teachers_user_id ON teachers(user_id);

COMMENT ON TABLE teachers IS 'Teacher profile data extending users table';
COMMENT ON COLUMN teachers.subject IS 'Primary subject taught (math, english, science, etc.)';
COMMENT ON COLUMN teachers.meta IS 'Flexible JSONB for additional teacher attributes';

-- ─────────────────────────────────────────
-- 3. students (Student profile extension)
-- ─────────────────────────────────────────
-- Note: May conflict with existing students table
-- Merge with existing table if present
CREATE TABLE IF NOT EXISTS students (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    org_id      INTEGER REFERENCES organizations(id),
    grade       VARCHAR(20),                  -- '1', '2', '3', 'K', 'PreK', etc.
    birth_year  INTEGER,
    locale      VARCHAR(20),                  -- 'ko-KR', 'en-US', etc.
    meta        JSONB,                        -- Flexible metadata
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_students_org_id  ON students(org_id);
CREATE INDEX IF NOT EXISTS idx_students_grade   ON students(grade);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);

COMMENT ON TABLE students IS 'Student profile data extending users table';
COMMENT ON COLUMN students.grade IS 'Current grade level (numeric or text: K, PreK, etc.)';
COMMENT ON COLUMN students.locale IS 'Preferred language/locale for UI and content';
COMMENT ON COLUMN students.meta IS 'Flexible JSONB for learning preferences, special needs, etc.';

-- ─────────────────────────────────────────
-- 4. classes (Classroom/Course sections)
-- ─────────────────────────────────────────
-- Note: May conflict with existing classes table
-- Check for table name conflicts
CREATE TABLE IF NOT EXISTS classes (
    id          SERIAL PRIMARY KEY,
    org_id      INTEGER REFERENCES organizations(id),
    teacher_id  INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
    name        VARCHAR(255) NOT NULL,        -- ex) "고2-1반 수학", "Algebra I - Period 3"
    grade       VARCHAR(20),
    subject     VARCHAR(100),
    meta        JSONB,                        -- Schedule, room number, etc.
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_classes_org_id     ON classes(org_id);
CREATE INDEX IF NOT EXISTS idx_classes_teacher_id ON classes(teacher_id);
CREATE INDEX IF NOT EXISTS idx_classes_grade      ON classes(grade);
CREATE INDEX IF NOT EXISTS idx_classes_subject    ON classes(subject);

COMMENT ON TABLE classes IS 'Classroom or course sections taught by teachers';
COMMENT ON COLUMN classes.name IS 'Display name for class (e.g., "고2-1반 수학")';
COMMENT ON COLUMN classes.meta IS 'Flexible JSONB for schedule, room, syllabus, etc.';

-- ─────────────────────────────────────────
-- 5. student_classroom (N:N junction table)
-- ─────────────────────────────────────────
-- Students can be in multiple classes
-- Classes contain multiple students
CREATE TABLE IF NOT EXISTS student_classroom (
    student_id  INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id    INTEGER NOT NULL REFERENCES classes(id) ON DELETE CASCADE,
    enrolled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (student_id, class_id)
);

CREATE INDEX IF NOT EXISTS idx_student_classroom_class_id   ON student_classroom(class_id);
CREATE INDEX IF NOT EXISTS idx_student_classroom_student_id ON student_classroom(student_id);

COMMENT ON TABLE student_classroom IS 'Many-to-many relationship between students and classes';
COMMENT ON COLUMN student_classroom.enrolled_at IS 'Timestamp when student joined the class';

-- ─────────────────────────────────────────
-- 6. exam_sessions (CAT exam instances)
-- ─────────────────────────────────────────
-- Represents a single exam/test session
-- Includes IRT theta estimation results
CREATE TABLE IF NOT EXISTS exam_sessions (
    id              BIGSERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    class_id        INTEGER REFERENCES classes(id) ON DELETE SET NULL,
    exam_type       VARCHAR(50) NOT NULL,     -- 'placement','practice','mock','official','quiz'
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress', -- 'in_progress','completed','abandoned'
    started_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at        TIMESTAMPTZ,
    score           NUMERIC(5,2),             -- Final score (0~100 scale)
    duration_sec    INTEGER,                  -- Total time spent in seconds
    theta           NUMERIC(6,3),             -- IRT ability estimate (typically -3 to +3)
    standard_error  NUMERIC(6,3),             -- Standard error of theta estimate
    meta            JSONB                     -- Algorithm params, stopping rule, etc.
);

CREATE INDEX IF NOT EXISTS idx_exam_sessions_student_id ON exam_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_exam_sessions_class_id   ON exam_sessions(class_id);
CREATE INDEX IF NOT EXISTS idx_exam_sessions_status     ON exam_sessions(status);
CREATE INDEX IF NOT EXISTS idx_exam_sessions_exam_type  ON exam_sessions(exam_type);
CREATE INDEX IF NOT EXISTS idx_exam_sessions_started_at ON exam_sessions(started_at DESC);

COMMENT ON TABLE exam_sessions IS 'Individual CAT exam/test sessions with IRT results';
COMMENT ON COLUMN exam_sessions.exam_type IS 'Type: placement, practice, mock, official, quiz';
COMMENT ON COLUMN exam_sessions.status IS 'Session status: in_progress, completed, abandoned';
COMMENT ON COLUMN exam_sessions.theta IS 'IRT ability estimate (typically -3 to +3)';
COMMENT ON COLUMN exam_sessions.standard_error IS 'Precision of theta estimate (lower = more accurate)';
COMMENT ON COLUMN exam_sessions.meta IS 'Algorithm config, stopping rule criteria, adaptive history';

-- ─────────────────────────────────────────
-- 7. attempts (Item-level responses)
-- ─────────────────────────────────────────
-- Records each question/item response
-- Links to items table (to be defined separately)
CREATE TABLE IF NOT EXISTS attempts (
    id                BIGSERIAL PRIMARY KEY,
    student_id        INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    exam_session_id   BIGINT NOT NULL REFERENCES exam_sessions(id) ON DELETE CASCADE,
    item_id           BIGINT,                   -- FK to items table (define separately)
    correct           BOOLEAN NOT NULL,
    submitted_answer  TEXT,                     -- Open-ended response or essay
    selected_choice   INTEGER,                  -- Multiple-choice option (1-5)
    response_time_ms  INTEGER,                  -- Response time in milliseconds
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta              JSONB                     -- Item difficulty, discrimination, partial credit, etc.
);

CREATE INDEX IF NOT EXISTS idx_attempts_student_id      ON attempts(student_id);
CREATE INDEX IF NOT EXISTS idx_attempts_exam_session_id ON attempts(exam_session_id);
CREATE INDEX IF NOT EXISTS idx_attempts_item_id         ON attempts(item_id);
CREATE INDEX IF NOT EXISTS idx_attempts_created_at      ON attempts(created_at DESC);

COMMENT ON TABLE attempts IS 'Item-level student responses within exam sessions';
COMMENT ON COLUMN attempts.correct IS 'Whether the response was correct';
COMMENT ON COLUMN attempts.submitted_answer IS 'Student answer (text for open-ended)';
COMMENT ON COLUMN attempts.selected_choice IS 'Selected option for multiple-choice (1-based index)';
COMMENT ON COLUMN attempts.response_time_ms IS 'Time taken to answer in milliseconds';
COMMENT ON COLUMN attempts.meta IS 'Item parameters (difficulty, discrimination), partial credit, hints used';

-- ─────────────────────────────────────────
-- Migration metadata
-- ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS schema_migrations (
    id              SERIAL PRIMARY KEY,
    migration_name  VARCHAR(255) NOT NULL UNIQUE,
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO schema_migrations (migration_name) 
VALUES ('20251120_core_schema_integer_based')
ON CONFLICT (migration_name) DO NOTHING;

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- End of migration
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
