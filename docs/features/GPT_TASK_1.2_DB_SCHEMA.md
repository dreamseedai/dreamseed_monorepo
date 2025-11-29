# GPT 작업 지시: Task 1.2 - Database Schema

복사해서 GPT에게 붙여넣으세요:

---

## Task 1.2: Database Schema 생성

DreamSeed AI 메신저 시스템의 PostgreSQL 스키마를 생성해주세요.

### 요구사항

**4개 테이블:**
1. `conversations` - 대화방 (1:1, 그룹, 공지)
2. `conversation_participants` - 참가자
3. `messages` - 메시지
4. `read_receipts` - 읽음 상태

**기존 테이블 참조:**
- `users` (이미 존재)
- `organizations` (이미 존재)
- `zones` (이미 존재)

### 상세 스키마

```sql
-- 대화방 (1:1, 그룹, 공지)
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type VARCHAR(20) NOT NULL CHECK (type IN ('direct', 'group', 'announcement')),
    title VARCHAR(255),
    zone_id UUID REFERENCES zones(id) ON DELETE CASCADE,
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES users(id) ON DELETE SET NULL
);

-- 참가자
CREATE TABLE conversation_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('admin', 'member', 'observer')),
    joined_at TIMESTAMP DEFAULT NOW(),
    last_read_at TIMESTAMP,
    UNIQUE(conversation_id, user_id)
);

-- 메시지
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID REFERENCES users(id) ON DELETE SET NULL,
    content TEXT,
    message_type VARCHAR(20) NOT NULL CHECK (message_type IN ('text', 'image', 'file', 'system')),
    file_url TEXT,
    file_size INTEGER,
    file_name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    edited_at TIMESTAMP,
    deleted_at TIMESTAMP
);

-- 읽음 상태
CREATE TABLE read_receipts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    read_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(message_id, user_id)
);

-- 알림 설정
CREATE TABLE notification_settings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    muted BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    UNIQUE(user_id, conversation_id)
);

-- 인덱스 (성능 최적화)
CREATE INDEX idx_messages_conversation_created ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_deleted ON messages(deleted_at) WHERE deleted_at IS NULL;
CREATE INDEX idx_participants_user ON conversation_participants(user_id);
CREATE INDEX idx_participants_conversation ON conversation_participants(conversation_id);
CREATE INDEX idx_read_receipts_message ON read_receipts(message_id);
CREATE INDEX idx_read_receipts_user ON read_receipts(user_id);
CREATE INDEX idx_conversations_zone_org ON conversations(zone_id, org_id);
```

### 추가 작업

1. **Alembic 마이그레이션 파일 생성**
   - 파일명: `backend/alembic/versions/XXX_add_messenger_schema.py`
   - upgrade() 함수: 위 SQL 실행
   - downgrade() 함수: 테이블 삭제

2. **SQLAlchemy 모델 생성**
   - 파일명: `backend/app/models/messenger_models.py`
   - Conversation, ConversationParticipant, Message, ReadReceipt, NotificationSetting 클래스

3. **RLS 정책 (Row Level Security)**
   - Zone/Org별 접근 제어
   - 사용자는 자신이 참가한 대화방만 조회 가능
   - 파일명: `db/rls/messenger_policies.sql`

### 제약 조건

- PostgreSQL 16+
- SQLAlchemy 2.0+ (async)
- 기존 DreamSeed AI 코드 스타일 따름

### 출력 형식

다음 3개 파일을 생성해주세요:

1. **backend/alembic/versions/XXX_add_messenger_schema.py** (전체 코드)
2. **backend/app/models/messenger_models.py** (전체 코드)
3. **db/rls/messenger_policies.sql** (전체 코드)

각 파일마다:
- 완전한 코드 (복사 가능)
- 주석 포함
- 타입 힌트 포함 (Python)

---

이 지시를 GPT에게 복사해서 붙여넣으면 됩니다!
