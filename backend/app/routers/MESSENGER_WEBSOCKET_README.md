# Messenger WebSocket Implementation

## Task 1.1 완료 ✅

WebSocket 실시간 메시징 서버 구현 완료

### 생성된 파일

#### 1. WebSocket 엔드포인트
**`backend/app/routers/messenger.py`** (150+ LOC 추가)
- `/api/v1/messenger/ws/{user_id}` - WebSocket 엔드포인트
- 실시간 양방향 메시지 통신
- Redis Pub/Sub 통합 (수평 확장 지원)
- 자동 온라인/오프라인 상태 관리

#### 2. 테스트 파일
**`backend/tests/test_messenger_websocket.py`** (250 LOC)
- PyTest 기반 WebSocket 테스트
- 연결/해제 테스트
- 구독 및 타이핑 인디케이터 테스트
- 에러 핸들링 테스트
- 멀티 디바이스 지원 테스트

#### 3. 데모 클라이언트
**`backend/tests/websocket_client_demo.html`** (380 LOC)
- 브라우저 기반 WebSocket 테스트 클라이언트
- 실시간 연결 상태 모니터링
- 메시지 송수신 UI
- Conversation 구독/타이핑 인디케이터 테스트

---

## 아키텍처

### WebSocket Flow

```
┌─────────────┐         WebSocket         ┌─────────────┐
│   Client    │ ◄────────────────────────► │   FastAPI   │
│  (Browser)  │                            │   Server    │
└─────────────┘                            └──────┬──────┘
                                                  │
                                                  │ Redis
                                                  │ Pub/Sub
                                                  ▼
                                           ┌──────────────┐
                                           │    Redis     │
                                           │  (Broadcast) │
                                           └──────────────┘
                                                  │
                                                  │
                        ┌─────────────────────────┼─────────────────────────┐
                        ▼                         ▼                         ▼
                 ┌─────────────┐           ┌─────────────┐           ┌─────────────┐
                 │  FastAPI    │           │  FastAPI    │           │  FastAPI    │
                 │ Instance 1  │           │ Instance 2  │           │ Instance 3  │
                 └─────────────┘           └─────────────┘           └─────────────┘
```

### 메시지 타입

#### Client → Server

```json
{
  "type": "subscribe",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

```json
{
  "type": "typing",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

```json
{
  "type": "message.read",
  "message_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Server → Client

```json
{
  "type": "system",
  "event": "connected",
  "message": "Connected to messenger",
  "timestamp": "2025-11-26T10:30:00Z"
}
```

```json
{
  "type": "subscribed",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

```json
{
  "type": "message.new",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "data": {
    "id": "...",
    "content": "Hello!",
    "sender_id": 2,
    "created_at": "2025-11-26T10:31:00Z"
  }
}
```

```json
{
  "type": "user.online",
  "user_id": 2,
  "timestamp": "2025-11-26T10:32:00Z"
}
```

```json
{
  "type": "error",
  "message": "Invalid conversation_id format"
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

### 2. 데모 클라이언트 열기

브라우저에서:
```
file:///home/won/projects/dreamseed_monorepo/backend/tests/websocket_client_demo.html
```

또는 HTTP 서버로:
```bash
cd /home/won/projects/dreamseed_monorepo/backend/tests
python -m http.server 8080
# 브라우저: http://localhost:8080/websocket_client_demo.html
```

### 3. 테스트 실행

```bash
# PyTest로 자동 테스트
cd /home/won/projects/dreamseed_monorepo/backend
pytest tests/test_messenger_websocket.py -v

# 또는 직접 실행
python tests/test_messenger_websocket.py
```

---

## WebSocket 엔드포인트 상세

### URL
```
ws://localhost:8000/api/v1/messenger/ws/{user_id}
```

### 연결 Flow

1. **연결 수락**
   - WebSocket 연결 수락
   - 온라인 상태 Redis 발행 (`online:status` 채널)
   - 환영 메시지 전송

2. **Redis Pub/Sub 리스너 시작**
   - `user:{user_id}` 채널 구독
   - 백그라운드 태스크로 메시지 수신 대기

3. **메시지 수신 루프**
   - 클라이언트 메시지 처리
   - 타입별 핸들링 (subscribe, typing, message.read)

4. **연결 해제**
   - Redis 리스너 취소
   - WebSocket 정리
   - 오프라인 상태 발행

### 에러 핸들링

- **Invalid JSON**: `{"type": "error", "message": "Invalid JSON format"}`
- **Invalid UUID**: `{"type": "error", "message": "Invalid conversation_id format"}`
- **Unknown type**: 로그에만 기록 (클라이언트 에러 없음)
- **Connection error**: 자동 정리 및 오프라인 상태

---

## 멀티 디바이스 지원

동일 사용자가 여러 디바이스에서 동시 접속 가능:

```python
# WebSocketConnectionManager
self.active_connections[user_id] = [websocket1, websocket2, ...]
```

- 첫 연결: 온라인 상태 발행
- 추가 연결: 기존 온라인 유지
- 마지막 연결 해제: 오프라인 상태 발행

---

## 통합 완료 현황

### ✅ 완료된 작업

1. **Task 1.2: Database Schema** (5 tables)
   - conversations, conversation_participants, messages
   - read_receipts, notification_settings
   - RLS policies with seedtest schema

2. **Task 1.3: REST API Endpoints** (11 endpoints)
   - Conversation CRUD
   - Message operations (send, edit, delete)
   - Participant management
   - Notification settings
   - Redis Pub/Sub 통합

3. **Task 1.4: Redis Pub/Sub** (3 modules)
   - `pubsub.py` - Redis Pub/Sub 매니저
   - `websocket.py` - WebSocket 연결 관리자
   - `broadcaster.py` - 메시지 브로드캐스터
   - `main.py` - 라이프사이클 이벤트 통합

4. **Task 1.1: WebSocket Server** (현재)
   - WebSocket 엔드포인트 (`/ws/{user_id}`)
   - Redis Pub/Sub 리스너
   - 실시간 메시지 전달
   - 온라인 상태 관리
   - 테스트 + 데모 클라이언트

### 📊 LOC 통계

| 파일 | LOC | 설명 |
|------|-----|------|
| `messenger.py` (WebSocket 추가) | +150 | WebSocket 엔드포인트 |
| `test_messenger_websocket.py` | 250 | PyTest 테스트 |
| `websocket_client_demo.html` | 380 | 브라우저 데모 |
| **Total (Task 1.1)** | **780** | **WebSocket 구현** |

**누적 LOC (Tasks 1.1-1.4)**: ~2,800 LOC

---

## 다음 단계

### Task 2.1: WebSocket Event Handlers

실시간 이벤트 핸들러 구현:

1. **message.send** - 메시지 전송 처리
2. **message.edit** - 메시지 수정
3. **message.delete** - 메시지 삭제
4. **typing.start / typing.stop** - 타이핑 상태
5. **read.receipt** - 읽음 확인

### Task 2.2: Presence System

온라인/오프라인 상태 추적:

1. 마지막 접속 시간 저장
2. 실시간 온라인 사용자 목록
3. 상태 브로드캐스트 최적화

### Task 3.x: Frontend Integration

React/Next.js 클라이언트 구현:

1. WebSocket 훅 (`useWebSocket`)
2. 메시지 목록 컴포넌트
3. 실시간 알림
4. 타이핑 인디케이터 UI

---

## 테스트 시나리오

### 1. 기본 연결
```
1. 데모 클라이언트 열기
2. User ID 입력 (예: 1)
3. "Connect" 버튼 클릭
4. 상태: "Connected (User 1)" 확인
5. 환영 메시지 수신 확인
```

### 2. Conversation 구독
```
1. Conversation ID 입력 (UUID)
2. "Subscribe" 버튼 클릭
3. "✅ Subscribed to conversation..." 메시지 확인
```

### 3. 타이핑 인디케이터
```
1. Conversation ID 입력
2. "Send Typing" 버튼 클릭
3. "→ Typing indicator sent" 메시지 확인
4. Redis에 타이핑 이벤트 발행됨
```

### 4. 멀티 디바이스
```
1. 첫 번째 브라우저 탭에서 User 1 연결
2. 두 번째 브라우저 탭에서 User 1 연결
3. 두 연결 모두 활성화 유지
4. 첫 번째 탭 닫기 → 온라인 상태 유지
5. 두 번째 탭 닫기 → 오프라인 상태 발행
```

### 5. 에러 핸들링
```
1. Invalid JSON 전송 → 에러 메시지 수신
2. Invalid UUID 구독 → 에러 메시지 수신
3. Unknown message type → 무시 (로그만)
```

---

## Production 고려사항

### 인증

현재는 `user_id`만으로 연결하지만, Production에서는:

```python
# JWT 토큰 검증 추가
async def verify_websocket_token(
    websocket: WebSocket,
    token: str = Query(...)
):
    user = verify_jwt_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        raise HTTPException(status_code=401)
    return user

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    user: User = Depends(verify_websocket_token)
):
    ...
```

### 스케일링

- Redis Pub/Sub로 수평 확장 지원
- 여러 FastAPI 인스턴스 동시 실행 가능
- Load Balancer에서 WebSocket sticky session 설정

### 모니터링

```python
# 연결 통계 엔드포인트
@router.get("/stats")
async def get_websocket_stats():
    stats = manager.get_stats()
    return {
        "online_users": stats["online_users"],
        "total_connections": stats["total_connections"],
        "active_conversations": stats["active_conversations"]
    }
```

---

## 문제 해결

### WebSocket 연결 실패

```bash
# 서버 로그 확인
tail -f /tmp/dreamseed_backend.log

# Redis 연결 확인
redis-cli ping

# 포트 확인
netstat -tuln | grep 8000
```

### Redis Pub/Sub 문제

```python
# Redis 연결 테스트
from app.core.redis import get_redis
redis = get_redis()
await redis.ping()  # Should return True
```

### 메시지 전달 안 됨

1. Redis broadcaster 실행 확인
2. Conversation 구독 확인
3. Redis 채널 확인: `redis-cli PUBSUB CHANNELS "conversation:*"`

---

## 참고 문서

- `MESSENGER_SYSTEM_PLAN.md` - 전체 시스템 설계
- `MESSENGER_IMPLEMENTATION_TASKS.md` - 구현 태스크 목록
- `backend/app/messenger/README.md` - 모듈 상세 문서

---

**Task 1.1 완료** - 2025-11-26
