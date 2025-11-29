-- =============================================================================
-- DreamSeed CAT System - Policy, Approval & Audit Schema
-- =============================================================================
-- 이 스키마는 정책/승인/감사 레이어를 포함합니다:
-- - AuditLog: 모든 중요한 행위/정책 적용 기록
-- - Approval: 재시험, 상위 시험 접근, AI 콘텐츠 승인 등
-- - ParentApproval: 학부모-자녀 관계 승인
-- - StudentPolicy: 학생별 AI 사용 정책
-- - TutorLog: AI 튜터 Q&A 로그
-- - StudentConsent: 동의/철회 기록 (GDPR/COPPA)
-- - DeletionRequest: GDPR "잊힐 권리" 데이터 삭제 요청
-- =============================================================================

-- 1. AuditLog (감사 로그)
-- 모든 중요한 이벤트를 추적하여 감사 추적 제공
CREATE TABLE IF NOT EXISTS audit_logs (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    user_id         INTEGER REFERENCES users(id),
    org_id          INTEGER REFERENCES organizations(id),
    event_type      VARCHAR(100) NOT NULL,      -- 'approval_processed', 'data_access', 'policy_violation'
    resource_type   VARCHAR(50),                -- 'student', 'exam_session', 'item', etc.
    resource_id     BIGINT,
    action          VARCHAR(50),                -- 'read', 'create', 'update', 'delete', 'approve', 'reject'
    description     TEXT,
    details_json    JSONB,
    ip_address      VARCHAR(64),
    user_agent      TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_org_id       ON audit_logs(org_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id      ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_event_type   ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource     ON audit_logs(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_timestamp    ON audit_logs(timestamp);

COMMENT ON TABLE audit_logs IS 'Audit trail for all important system events';
COMMENT ON COLUMN audit_logs.event_type IS 'Type of event: approval_processed, data_access, policy_violation, etc.';
COMMENT ON COLUMN audit_logs.resource_type IS 'Type of resource affected: student, exam_session, item, etc.';
COMMENT ON COLUMN audit_logs.action IS 'Action performed: read, create, update, delete, approve, reject';

-- 2. Approval (공통 승인 요청)
-- 재시험, 특별 접근, AI 콘텐츠 승인 등 모든 승인 요청 처리
CREATE TABLE IF NOT EXISTS approvals (
    id              BIGSERIAL PRIMARY KEY,
    request_type    VARCHAR(50) NOT NULL,   -- 'content', 'retest', 'special_access', 'plan_upgrade'
    requester_id    INTEGER NOT NULL REFERENCES users(id),
    approver_role   VARCHAR(50) NOT NULL,   -- 'teacher', 'admin'
    resource_type   VARCHAR(50),            -- 'exam', 'item', 'student', 'plan'
    resource_id     BIGINT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'approved', 'rejected', 'expired'
    request_data    JSONB,                  -- reason, exam_name, additional context
    approved_by     INTEGER REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    rejection_reason TEXT,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_approvals_status        ON approvals(status);
CREATE INDEX IF NOT EXISTS idx_approvals_requester     ON approvals(requester_id);
CREATE INDEX IF NOT EXISTS idx_approvals_resource      ON approvals(resource_type, resource_id);
CREATE INDEX IF NOT EXISTS idx_approvals_created_at    ON approvals(created_at);

COMMENT ON TABLE approvals IS 'Common approval requests for retest, special access, content approval, etc.';
COMMENT ON COLUMN approvals.request_type IS 'Type of approval: content, retest, special_access, plan_upgrade';
COMMENT ON COLUMN approvals.status IS 'Status: pending, approved, rejected, expired';
COMMENT ON COLUMN approvals.approver_role IS 'Role required for approval: teacher, admin';

-- 3. ParentApproval (학부모 ↔ 자녀 승인)
-- 학부모와 자녀 간 계정 연결 승인 관리
CREATE TABLE IF NOT EXISTS parent_approvals (
    id              BIGSERIAL PRIMARY KEY,
    parent_user_id  INTEGER NOT NULL REFERENCES users(id),
    student_id      INTEGER NOT NULL REFERENCES students(id),
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',  -- 'pending', 'approved', 'rejected'
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_at     TIMESTAMPTZ,
    approved_by     INTEGER REFERENCES users(id),
    rejection_reason TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_parent_student ON parent_approvals(parent_user_id, student_id);
CREATE INDEX IF NOT EXISTS idx_parent_approvals_status ON parent_approvals(status);

COMMENT ON TABLE parent_approvals IS 'Parent-to-student relationship approval for account linking';
COMMENT ON COLUMN parent_approvals.status IS 'Approval status: pending, approved, rejected';

-- 4. StudentPolicy (학생별 AI 사용 정책)
-- 학생별 AI 튜터 사용 제한 및 정책 설정
CREATE TABLE IF NOT EXISTS student_policies (
    id                  BIGSERIAL PRIMARY KEY,
    student_id          INTEGER NOT NULL UNIQUE REFERENCES students(id) ON DELETE CASCADE,
    ai_tutor_enabled    BOOLEAN NOT NULL DEFAULT TRUE,
    daily_question_limit INTEGER,           -- NULL이면 무제한
    restricted_during_exam BOOLEAN NOT NULL DEFAULT TRUE,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by          INTEGER REFERENCES users(id),
    meta                JSONB
);

CREATE INDEX IF NOT EXISTS idx_student_policies_student_id ON student_policies(student_id);

COMMENT ON TABLE student_policies IS 'Per-student AI tutor usage policies and restrictions';
COMMENT ON COLUMN student_policies.ai_tutor_enabled IS 'Whether AI tutor is enabled for this student';
COMMENT ON COLUMN student_policies.daily_question_limit IS 'Daily question limit (NULL = unlimited)';
COMMENT ON COLUMN student_policies.restricted_during_exam IS 'Block AI tutor access during active exams';

-- 5. TutorLog (AI 튜터 대화 로그)
-- AI 튜터와의 모든 대화 기록 (품질 모니터링 및 감사용)
CREATE TABLE IF NOT EXISTS tutor_logs (
    id              BIGSERIAL PRIMARY KEY,
    student_id      INTEGER REFERENCES students(id),
    session_id      BIGINT,                     -- 튜터 세션 ID (별도 테이블 참조 가능)
    question        TEXT NOT NULL,
    answer          TEXT,
    model_used      VARCHAR(50),               -- 'gpt-4', 'local-llama-13b', etc.
    context_json    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tutor_logs_student_id ON tutor_logs(student_id);
CREATE INDEX IF NOT EXISTS idx_tutor_logs_session_id ON tutor_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_tutor_logs_created_at ON tutor_logs(created_at);

COMMENT ON TABLE tutor_logs IS 'AI tutor conversation logs for quality monitoring and audit';
COMMENT ON COLUMN tutor_logs.model_used IS 'AI model used: gpt-4, local-llama-13b, etc.';
COMMENT ON COLUMN tutor_logs.context_json IS 'Additional context: topic, difficulty, related items';

-- 6. StudentConsent (동의/철회 이력)
-- GDPR/COPPA/개인정보보호법 준수를 위한 동의 관리
CREATE TABLE IF NOT EXISTS student_consents (
    id              BIGSERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    parent_user_id  INTEGER REFERENCES users(id),
    consent_type    VARCHAR(50) NOT NULL,       -- 'data_processing', 'ai_usage', 'analytics'
    status          VARCHAR(20) NOT NULL,       -- 'granted', 'revoked'
    granted_at      TIMESTAMPTZ,
    revoked_at      TIMESTAMPTZ,
    meta            JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_student_consents_student_id ON student_consents(student_id);
CREATE INDEX IF NOT EXISTS idx_student_consents_status ON student_consents(consent_type, status);

COMMENT ON TABLE student_consents IS 'Student consent history for GDPR/COPPA/privacy law compliance';
COMMENT ON COLUMN student_consents.consent_type IS 'Type of consent: data_processing, ai_usage, analytics';
COMMENT ON COLUMN student_consents.status IS 'Consent status: granted, revoked';

-- 7. DeletionRequest (GDPR 삭제 요청)
-- GDPR "잊힐 권리" 구현을 위한 데이터 삭제 요청 추적
CREATE TABLE IF NOT EXISTS deletion_requests (
    id              BIGSERIAL PRIMARY KEY,
    student_id      INTEGER NOT NULL REFERENCES students(id),
    requested_by    INTEGER NOT NULL REFERENCES users(id),
    reason          TEXT,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'approved', 'rejected', 'done'
    requested_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    approved_by     INTEGER REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    processed_at    TIMESTAMPTZ,
    meta            JSONB
);

CREATE INDEX IF NOT EXISTS idx_deletion_requests_student_id ON deletion_requests(student_id);
CREATE INDEX IF NOT EXISTS idx_deletion_requests_status      ON deletion_requests(status);
CREATE INDEX IF NOT EXISTS idx_deletion_requests_requested_at ON deletion_requests(requested_at);

COMMENT ON TABLE deletion_requests IS 'GDPR "right to be forgotten" data deletion requests';
COMMENT ON COLUMN deletion_requests.status IS 'Request status: pending, approved, rejected, done';
COMMENT ON COLUMN deletion_requests.processed_at IS 'Timestamp when data was actually deleted';

-- =============================================================================
-- Views for common queries
-- =============================================================================

-- View: Pending approvals summary
CREATE OR REPLACE VIEW v_pending_approvals AS
SELECT 
    a.id,
    a.request_type,
    a.requester_id,
    u.email as requester_email,
    a.approver_role,
    a.resource_type,
    a.resource_id,
    a.created_at,
    a.expires_at,
    EXTRACT(EPOCH FROM (NOW() - a.created_at)) / 3600 as hours_pending
FROM approvals a
JOIN users u ON a.requester_id = u.id
WHERE a.status = 'pending'
ORDER BY a.created_at ASC;

COMMENT ON VIEW v_pending_approvals IS 'Summary of all pending approval requests';

-- View: Recent audit events
CREATE OR REPLACE VIEW v_recent_audit_events AS
SELECT 
    al.id,
    al.timestamp,
    al.event_type,
    al.action,
    al.resource_type,
    al.resource_id,
    u.email as user_email,
    o.name as org_name,
    al.description
FROM audit_logs al
LEFT JOIN users u ON al.user_id = u.id
LEFT JOIN organizations o ON al.org_id = o.id
ORDER BY al.timestamp DESC
LIMIT 100;

COMMENT ON VIEW v_recent_audit_events IS 'Most recent 100 audit events';

-- View: Student policy summary
CREATE OR REPLACE VIEW v_student_policy_summary AS
SELECT 
    s.id as student_id,
    u.email as student_email,
    sp.ai_tutor_enabled,
    sp.daily_question_limit,
    sp.restricted_during_exam,
    sp.updated_at,
    u2.email as updated_by_email
FROM students s
LEFT JOIN student_policies sp ON s.id = sp.student_id
LEFT JOIN users u ON s.user_id = u.id
LEFT JOIN users u2 ON sp.updated_by = u2.id;

COMMENT ON VIEW v_student_policy_summary IS 'Summary of AI tutor policies for all students';
