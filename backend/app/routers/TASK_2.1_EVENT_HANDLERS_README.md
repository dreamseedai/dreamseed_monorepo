# Task 2.1: WebSocket Event Handlers - 완료 ✅

## 개요

WebSocket을 통한 실시간 메시지 이벤트 처리 핸들러 구현 완료

### 구현된 이벤트 핸들러 (5개)

1. **`message.send`** - 메시지 전송
2. **`message.edit`** - 메시지 수정
3. **`message.delete`** - 메시지 삭제 (soft delete)
4. **`typing.start` / `typing.stop`** - 타이핑 상태
5. **`message.read`** - 읽음 확인 (read receipt)

---

## 생성된 파일

### 1. Event Handler Functions
**`backend/app/routers/messenger.py`** (+330 LOC)

4개의 async 핸들러 함수:
- `handle_message_send()` - DB에 메시지 생성 + Redis 브로드캐스트
- `handle_message_edit()` - 메시지 수정 + 브로드캐스트
- `handle_message_delete()` - Soft delete + 브로드캐스트  
- `handle_read_receipt()` - 읽음 확인 생성 + last_read_at 업데이트

### 2. Updated WebSocket Endpoint
**`backend/app/routers/messenger.py`** (통합)

WebSocket 메시지 루프에서 이벤트 핸들러 호출:
```python
elif message_type == "message.send" and conversation_id:
    await handle_message_send(websocket, user_id, uuid.UUID(conversation_id), message)
```

### 3. Enhanced Demo Client
**`backend/tests/websocket_client_demo.html`** (+150 LOC 업데이트)

새로운 UI 요소:
- **Test Message** 입력 필드 - 메시지 텍스트 입력
- **Send Message** 버튼 - `message.send` 이벤트
- **Typing Start/Stop** 버튼 - 타이핑 인디케이터
- **Message ID** 입력 필드 - 수정/삭제/읽음용
- **Edit/Delete/Mark Read** 버튼 - 메시지 조작

### 4. Event Handler Tests
**`backend/tests/test_messenger_event_handlers.py`** (280 LOC)

7가지 테스트 시나리오:
- `test_message_send_event()` - 메시지 전송
- `test_typing_indicators()` - 타이핑 시작/중지
- `test_message_edit_event()` - 메시지 수정
- `test_message_delete_event()` - 메시지 삭제
- `test_read_receipt_event()` - 읽음 확인
- `test_full_message_lifecycle()` - 전체 라이프사이클
- `test_invalid_event_handling()` - 에러 처리

---

## 이벤트 상세

### 1. message.send

**Client → Server:**
```json
{
  "type": "message.send",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Hello!",
  "message_type": "text"
}
```

**Server → Client (Success):**
```json
{
  "type": "message.sent",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "content": "Hello!",
    "sender_id": 1,
    "created_at": "2025-11-26T10:30:00Z",
    ...
  }
}
```

**Server → All Participants (Broadcast):**
```json
{
  "type": "message.new",
  "data": { ... }
}
```

**처리 과정:**
1. 사용자가 conversation 참가자인지 확인
2. DB에 `Message` 레코드 생성
3. Redis Pub/Sub로 conversation 채널에 브로드캐스트
4. 발신자에게 `message.sent` 응답

---

### 2. message.edit

**Client → Server:**
```json
{
  "type": "message.edit",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "content": "Updated message!"
}
```

**Server → Client:**
```json
{
  "type": "message.edited",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "data": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "content": "Updated message!",
    "edited_at": "2025-11-26T10:31:00Z",
    ...
  }
}
```

**권한:**
- 메시지 발신자만 수정 가능
- `edited_at` 타임스탬프 자동 설정

---

### 3. message.delete

**Client → Server:**
```json
{
  "type": "message.delete",
  "message_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Server → All Participants:**
```json
{
  "type": "message.deleted",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**권한:**
- 메시지 발신자 또는 conversation admin
- Soft delete (`deleted_at` 설정)

---

### 4. typing.start / typing.stop

**Client → Server:**
```json
{
  "type": "typing.start",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Server → All Participants:**
```json
{
  "type": "typing.start",
  "user_id": 1,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**특징:**
- DB 저장 없음 (ephemeral)
- Redis Pub/Sub로만 브로드캐스트
- 프론트엔드에서 타임아웃 처리 (보통 3초)

---

### 5. message.read

**Client → Server:**
```json
{
  "type": "message.read",
  "message_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Server → Client:**
```json
{
  "type": "read.confirmed",
  "message_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Server → All Participants (Optional):**
```json
{
  "type": "message.read",
  "message_id": "123e4567-e89b-12d3-a456-426614174000",
  "user_id": 2,
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**DB 작업:**
1. `read_receipts` 테이블에 레코드 생성 (중복 방지)
2. `conversation_participants.last_read_at` 업데이트
3. 읽지 않은 메시지 수 계산에 사용

---

## 에러 처리

### 인증 실패
```json
{
  "type": "error",
  "message": "Not a participant of this conversation"
}
```

### 권한 부족
```json
{
  "type": "error",
  "message": "Only sender can edit message"
}
```

### 리소스 없음
```json
{
  "type": "error",
  "message": "Message not found"
}
```

### 내부 오류
```json
{
  "type": "error",
  "message": "Failed to send message: <error details>"
}
```

---

## 사용 방법

### 1. 서버 실행

```bash
cd /home/won/projects/dreamseed_monorepo/backend
source ../.venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 데모 클라이언트 테스트

브라우저에서:
```
file:///home/won/projects/dreamseed_monorepo/backend/tests/websocket_client_demo.html
```

**테스트 시나리오:**

1. **연결**
   - User ID: 1 입력
   - "Connect" 버튼 클릭
   - 상태: "Connected (User 1)" 확인

2. **메시지 전송**
   - Conversation ID 입력 (UUID)
   - Test Message: "Hello World!" 입력
   - "Send Message" 버튼 클릭
   - Message ID가 자동으로 입력됨 확인

3. **메시지 수정**
   - Test Message: "Updated!" 입력
   - "Edit Message" 버튼 클릭

4. **타이핑 인디케이터**
   - "Typing Start" 버튼 클릭
   - (3초 후) "Typing Stop" 버튼 클릭

5. **읽음 확인**
   - Message ID 확인
   - "Mark Read" 버튼 클릭

6. **메시지 삭제**
   - "Delete Message" 버튼 클릭

### 3. PyTest 실행

```bash
cd /home/won/projects/dreamseed_monorepo/backend

# 이벤트 핸들러 테스트
pytest tests/test_messenger_event_handlers.py -v

# 또는 직접 실행
python tests/test_messenger_event_handlers.py
```

---

## 아키텍처

### 이벤트 처리 Flow

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ WebSocket
       │ message.send
       ▼
┌──────────────────────────────────────┐
│   FastAPI WebSocket Endpoint         │
│   /api/v1/messenger/ws/{user_id}     │
└──────┬───────────────────────────────┘
       │ Call handler
       ▼
┌──────────────────────────────────────┐
│   handle_message_send()              │
│   1. Verify participant              │
│   2. Create Message in DB            │
│   3. Publish to Redis Pub/Sub        │
│   4. Send ACK to sender              │
└──────┬───────────────────────────────┘
       │ Redis
       │ Pub/Sub
       ▼
┌──────────────────────────────────────┐
│   Redis Channel                       │
│   conversation:{uuid}                 │
└──────┬───────────────────────────────┘
       │ Subscribe
       ▼
┌──────────────────────────────────────┐
│   All Participant WebSockets         │
│   (Broadcaster forwards messages)    │
└──────────────────────────────────────┘
```

### Database Session Management

각 이벤트 핸들러는 독립적인 DB 세션 사용:

```python
from app.core.database import AsyncSessionLocal

async with AsyncSessionLocal() as db:
    # DB operations
    await db.commit()
```

**이유:**
- WebSocket 연결은 장시간 유지
- DB 세션은 짧게 유지 (connection pool 효율)
- 각 이벤트는 독립적인 트랜잭션

---

## LOC 통계

| 파일 | 추가 LOC | 설명 |
|------|----------|------|
| `messenger.py` (handlers) | +330 | 4개 핸들러 함수 |
| `messenger.py` (endpoint) | +50 | 이벤트 라우팅 업데이트 |
| `websocket_client_demo.html` | +150 | UI 요소 추가 |
| `test_messenger_event_handlers.py` | 280 | PyTest 테스트 |
| **Total** | **810** | **Task 2.1** |

---

## 누적 완료 현황

| Task | 상태 | LOC | 설명 |
|------|------|-----|------|
| 1.2 | ✅ | 500 | DB Schema (5 tables + RLS) |
| 1.3 | ✅ | 1,000 | REST API (11 endpoints) |
| 1.4 | ✅ | 960 | Redis Pub/Sub (3 modules) |
| 1.1 | ✅ | 780 | WebSocket Server |
| **2.1** | **✅** | **810** | **WebSocket Event Handlers** |
| **Total** | **✅** | **4,050** | **실시간 메시징 시스템** |

---

## 다음 단계

### Task 2.2: Presence System (온라인/오프라인 상태)

구현 예정:
1. **Online Users Tracking**
   - 실시간 온라인 사용자 목록
   - Last seen 타임스탬프

2. **Status Broadcasting**
   - Zone/org별 온라인 상태 브로드캐스트
   - 효율적인 상태 업데이트 (debouncing)

3. **User Activity**
   - 마지막 활동 시간 추적
   - "Away" 상태 자동 설정

### Task 2.3: File Uploads

구현 예정:
1. **File Upload Endpoint**
   - REST API for file uploads
   - S3/Cloud Storage 통합

2. **File Messages**
   - `message_type: 'file'`
   - Thumbnail 생성 (이미지)

3. **Progress Tracking**
   - WebSocket으로 업로드 진행률 전송

---

## 문제 해결

### WebSocket 연결 끊김

```python
# 자동 재연결 로직 (프론트엔드)
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function reconnect() {
    if (reconnectAttempts < maxReconnectAttempts) {
        setTimeout(() => {
            reconnectAttempts++;
            connect();
        }, Math.min(1000 * (2 ** reconnectAttempts), 30000));
    }
}
```

### 메시지 전송 실패

```python
# 클라이언트 사이드 큐잉
const messageQueue = [];

function sendMessage(message) {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(message));
    } else {
        messageQueue.push(message);
        reconnect();
    }
}
```

### DB 세션 타임아웃

```python
# AsyncSessionLocal 설정
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
```

---

## 참고 문서

- `MESSENGER_SYSTEM_PLAN.md` - 전체 시스템 아키텍처
- `MESSENGER_IMPLEMENTATION_TASKS.md` - 구현 태스크
- `MESSENGER_WEBSOCKET_README.md` - WebSocket 서버 문서

---

**Task 2.1 완료** - 2025-11-26

모든 핵심 이벤트 핸들러 구현 완료! 🎉
