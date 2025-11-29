-- =============================================================================
-- DreamSeed CAT System - Tutor Domain Schema
-- =============================================================================
-- 튜터(가정교사) 도메인을 위한 스키마:
-- - Tutors: 튜터 프로필 및 정보
-- - TutorSessions: 튜터링 세션 기록
-- - TutorNotes: 세션별 피드백/과제/메시지
-- - TutorSessionTasks: 세션 내 TODO 항목 (기존)
-- 
-- Teacher vs Tutor:
-- - Teacher: 학교/학원 소속, 반(class) 관리
-- - Tutor: 개인/플랫폼 소속, 1:1 또는 소그룹 지도
-- =============================================================================

-- 1. Tutors (튜터 프로필)
-- users 테이블과 1:1 관계, role='tutor'
CREATE TABLE IF NOT EXISTS tutors (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    org_id          INTEGER REFERENCES organizations(id),  -- 소속 기관 (NULL이면 개인)
    subjects        TEXT[],                 -- 전문 과목 ['math', 'physics', 'english']
    bio             TEXT,                   -- 자기소개
    hourly_rate     NUMERIC(10, 2),         -- 시간당 수업료 (NULL이면 미공개)
    years_experience INTEGER,               -- 경력 (년)
    education       TEXT,                   -- 학력
    certifications  TEXT[],                 -- 자격증
    available_hours JSONB,                  -- 가능 시간대 {mon: ['09:00-12:00'], ...}
    rating_avg      NUMERIC(3, 2) DEFAULT 0.0,  -- 평균 평점 (0.0-5.0)
    rating_count    INTEGER DEFAULT 0,      -- 평가 개수
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    meta            JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tutors_user_id ON tutors(user_id);
CREATE INDEX IF NOT EXISTS idx_tutors_org_id ON tutors(org_id);
CREATE INDEX IF NOT EXISTS idx_tutors_is_active ON tutors(is_active);
CREATE INDEX IF NOT EXISTS idx_tutors_subjects ON tutors USING GIN(subjects);

COMMENT ON TABLE tutors IS 'Tutor profiles for 1:1 or small group tutoring';
COMMENT ON COLUMN tutors.subjects IS 'Array of subject specializations';
COMMENT ON COLUMN tutors.hourly_rate IS 'Hourly rate in currency (NULL if not disclosed)';
COMMENT ON COLUMN tutors.available_hours IS 'Available hours per weekday in JSON format';

-- 2. TutorSessions (튜터링 세션) - 기존 테이블 확장
-- 기존 tutor_sessions 테이블이 있으므로 ALTER로 추가
ALTER TABLE tutor_sessions 
    ADD COLUMN IF NOT EXISTS mode VARCHAR(20),             -- 'online', 'offline', 'video', 'chat'
    ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ,       -- 실제 시작 시각
    ADD COLUMN IF NOT EXISTS ended_at TIMESTAMPTZ,         -- 실제 종료 시각
    ADD COLUMN IF NOT EXISTS session_rating INTEGER,       -- 세션 평점 (1-5)
    ADD COLUMN IF NOT EXISTS session_feedback TEXT,        -- 학생/학부모 피드백
    ADD COLUMN IF NOT EXISTS meta JSONB;                   -- 추가 메타데이터

CREATE INDEX IF NOT EXISTS idx_tutor_sessions_tutor_id ON tutor_sessions(tutor_id);
CREATE INDEX IF NOT EXISTS idx_tutor_sessions_student_id ON tutor_sessions(student_id);
CREATE INDEX IF NOT EXISTS idx_tutor_sessions_date ON tutor_sessions(date);
CREATE INDEX IF NOT EXISTS idx_tutor_sessions_status ON tutor_sessions(status);

COMMENT ON TABLE tutor_sessions IS 'Tutoring session records (1:1 or small group)';
COMMENT ON COLUMN tutor_sessions.mode IS 'Session mode: online, offline, video, chat';
COMMENT ON COLUMN tutor_sessions.status IS 'Session status: upcoming, in_progress, completed, cancelled';

-- 3. TutorNotes (세션 피드백 및 노트)
-- 튜터가 세션 후 작성하는 다양한 노트
CREATE TABLE IF NOT EXISTS tutor_notes (
    id              BIGSERIAL PRIMARY KEY,
    tutor_session_id BIGINT NOT NULL REFERENCES tutor_sessions(id) ON DELETE CASCADE,
    author_id       INTEGER NOT NULL REFERENCES users(id),  -- 작성자 (주로 튜터)
    note_type       VARCHAR(50) NOT NULL,       -- 'summary', 'homework', 'parent_message', 'progress', 'concern'
    title           VARCHAR(255),
    content         TEXT NOT NULL,
    is_visible_to_student BOOLEAN NOT NULL DEFAULT TRUE,
    is_visible_to_parent BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta            JSONB
);

CREATE INDEX IF NOT EXISTS idx_tutor_notes_session_id ON tutor_notes(tutor_session_id);
CREATE INDEX IF NOT EXISTS idx_tutor_notes_author_id ON tutor_notes(author_id);
CREATE INDEX IF NOT EXISTS idx_tutor_notes_note_type ON tutor_notes(note_type);

COMMENT ON TABLE tutor_notes IS 'Session notes, feedback, homework, and parent messages';
COMMENT ON COLUMN tutor_notes.note_type IS 'Type: summary, homework, parent_message, progress, concern';
COMMENT ON COLUMN tutor_notes.is_visible_to_student IS 'Whether student can see this note';
COMMENT ON COLUMN tutor_notes.is_visible_to_parent IS 'Whether parent can see this note';

-- 4. TutorStudentRelations (튜터-학생 관계)
-- 튜터가 담당하는 학생 목록 (계약/매칭 관리)
CREATE TABLE IF NOT EXISTS tutor_student_relations (
    id              BIGSERIAL PRIMARY KEY,
    tutor_id        INTEGER NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'active', 'paused', 'ended'
    started_at      TIMESTAMPTZ,
    ended_at        TIMESTAMPTZ,
    subjects        TEXT[],                     -- 담당 과목
    weekly_hours    NUMERIC(4, 1),              -- 주당 수업 시간
    contract_type   VARCHAR(50),                -- 'monthly', 'per_session', 'package'
    rate_per_hour   NUMERIC(10, 2),
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta            JSONB
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_tutor_student_active 
    ON tutor_student_relations(tutor_id, student_id) 
    WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_tutor_student_relations_tutor_id ON tutor_student_relations(tutor_id);
CREATE INDEX IF NOT EXISTS idx_tutor_student_relations_student_id ON tutor_student_relations(student_id);
CREATE INDEX IF NOT EXISTS idx_tutor_student_relations_status ON tutor_student_relations(status);

COMMENT ON TABLE tutor_student_relations IS 'Tutor-student relationships and contracts';
COMMENT ON COLUMN tutor_student_relations.status IS 'Relationship status: pending, active, paused, ended';
COMMENT ON COLUMN tutor_student_relations.contract_type IS 'Contract type: monthly, per_session, package';

-- 5. TutorAvailability (튜터 가용 시간)
-- 튜터의 주간 스케줄 관리
CREATE TABLE IF NOT EXISTS tutor_availability (
    id              BIGSERIAL PRIMARY KEY,
    tutor_id        INTEGER NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    day_of_week     INTEGER NOT NULL,           -- 0=Monday, 6=Sunday
    start_time      TIME NOT NULL,
    end_time        TIME NOT NULL,
    is_available    BOOLEAN NOT NULL DEFAULT TRUE,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tutor_availability_tutor_id ON tutor_availability(tutor_id);
CREATE INDEX IF NOT EXISTS idx_tutor_availability_day ON tutor_availability(day_of_week);

COMMENT ON TABLE tutor_availability IS 'Tutor weekly schedule and availability';
COMMENT ON COLUMN tutor_availability.day_of_week IS 'Day of week: 0=Monday, 6=Sunday';

-- 6. TutorRatings (튜터 평가)
-- 학생/학부모가 남기는 튜터 평가
CREATE TABLE IF NOT EXISTS tutor_ratings (
    id              BIGSERIAL PRIMARY KEY,
    tutor_id        INTEGER NOT NULL REFERENCES tutors(id) ON DELETE CASCADE,
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_id      BIGINT REFERENCES tutor_sessions(id) ON DELETE SET NULL,
    rating          INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment         TEXT,
    created_by      INTEGER NOT NULL REFERENCES users(id),  -- 평가자 (학생 또는 학부모)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    meta            JSONB
);

CREATE INDEX IF NOT EXISTS idx_tutor_ratings_tutor_id ON tutor_ratings(tutor_id);
CREATE INDEX IF NOT EXISTS idx_tutor_ratings_student_id ON tutor_ratings(student_id);
CREATE INDEX IF NOT EXISTS idx_tutor_ratings_session_id ON tutor_ratings(session_id);

COMMENT ON TABLE tutor_ratings IS 'Student/parent ratings and reviews for tutors';
COMMENT ON COLUMN tutor_ratings.rating IS 'Rating from 1 to 5 stars';
COMMENT ON COLUMN tutor_ratings.created_by IS 'User who created the rating (student or parent)';

-- =============================================================================
-- Triggers for automatic updates
-- =============================================================================

-- Update tutor rating average
CREATE OR REPLACE FUNCTION update_tutor_rating_avg()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE tutors
    SET 
        rating_avg = (
            SELECT AVG(rating)::NUMERIC(3,2)
            FROM tutor_ratings
            WHERE tutor_id = NEW.tutor_id
        ),
        rating_count = (
            SELECT COUNT(*)
            FROM tutor_ratings
            WHERE tutor_id = NEW.tutor_id
        )
    WHERE id = NEW.tutor_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tutor_rating_avg
AFTER INSERT OR UPDATE ON tutor_ratings
FOR EACH ROW
EXECUTE FUNCTION update_tutor_rating_avg();

-- Update tutor updated_at timestamp
CREATE OR REPLACE FUNCTION update_tutor_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_tutor_updated_at
BEFORE UPDATE ON tutors
FOR EACH ROW
EXECUTE FUNCTION update_tutor_updated_at();

-- =============================================================================
-- Views for common queries
-- =============================================================================

-- View: Active tutor profiles with statistics
CREATE OR REPLACE VIEW v_active_tutors AS
SELECT 
    t.id,
    t.user_id,
    u.email,
    u.full_name,
    t.subjects,
    t.hourly_rate,
    t.years_experience,
    t.rating_avg,
    t.rating_count,
    COUNT(DISTINCT tsr.student_id) as active_students,
    COUNT(DISTINCT ts.id) as total_sessions
FROM tutors t
JOIN users u ON t.user_id = u.id
LEFT JOIN tutor_student_relations tsr ON t.id = tsr.tutor_id AND tsr.status = 'active'
LEFT JOIN tutor_sessions ts ON t.user_id = ts.tutor_id
WHERE t.is_active = TRUE
GROUP BY t.id, u.email, u.full_name
ORDER BY t.rating_avg DESC, t.rating_count DESC;

COMMENT ON VIEW v_active_tutors IS 'Active tutors with statistics';

-- View: Tutor session summary
CREATE OR REPLACE VIEW v_tutor_session_summary AS
SELECT 
    ts.id,
    ts.date,
    ts.subject,
    ts.topic,
    ts.status,
    ts.duration_minutes,
    ts.mode,
    t.id as tutor_id,
    u_tutor.full_name as tutor_name,
    s.id as student_id,
    u_student.full_name as student_name,
    COUNT(tn.id) as note_count,
    ts.session_rating
FROM tutor_sessions ts
JOIN users u_tutor ON ts.tutor_id = u_tutor.id
JOIN students s ON ts.student_id = s.id
JOIN users u_student ON s.user_id = u_student.id
LEFT JOIN tutors t ON u_tutor.id = t.user_id
LEFT JOIN tutor_notes tn ON ts.id = tn.tutor_session_id
GROUP BY ts.id, t.id, u_tutor.full_name, s.id, u_student.full_name
ORDER BY ts.date DESC;

COMMENT ON VIEW v_tutor_session_summary IS 'Summary of tutor sessions with participant info';

-- View: Upcoming sessions
CREATE OR REPLACE VIEW v_upcoming_tutor_sessions AS
SELECT 
    ts.id,
    ts.date,
    ts.subject,
    ts.duration_minutes,
    u_tutor.full_name as tutor_name,
    u_student.full_name as student_name,
    ts.notes
FROM tutor_sessions ts
JOIN users u_tutor ON ts.tutor_id = u_tutor.id
JOIN students s ON ts.student_id = s.id
JOIN users u_student ON s.user_id = u_student.id
WHERE ts.status = 'upcoming' OR ts.status = 'Upcoming'
  AND ts.date >= CURRENT_DATE
ORDER BY ts.date ASC, ts.created_at ASC;

COMMENT ON VIEW v_upcoming_tutor_sessions IS 'Upcoming tutor sessions';
