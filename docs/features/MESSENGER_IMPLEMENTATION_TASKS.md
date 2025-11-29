# 🤖 GPT 작업 지시서: DreamSeed AI 메신저 시스템 구현

> **대상**: GPT-4, Claude 3.5, 또는 개발 AI 어시스턴트  
> **기간**: 10주 (Phase 2.1~2.3)  
> **규모**: 40,000~50,000 라인  
> **우선순위**: 🔴 P0 - MegaCity Phase 2 Blocker

---

## 📋 Overview

이 문서는 **GPT에게 단계별로 작업을 지시**하여 DreamSeed AI 메신저 시스템을 구현하는 **실행 가능한 태스크 리스트**입니다.

### 전제 조건
- [MESSENGER_SYSTEM_PLAN.md](./MESSENGER_SYSTEM_PLAN.md) 숙지
- 현재 코드베이스: `/home/won/projects/dreamseed_monorepo`
- Backend: FastAPI + PostgreSQL + Redis
- Frontend: Next.js 14 + React + TypeScript

---

## 🎯 Phase 2.1 - MVP (4주, ~15,000 LOC)

### Week 1 - Backend 기초 구조

#### Task 1.1: Socket.IO 서버 설정

**GPT에게 지시:**
```
DreamSeed AI 프로젝트의 메신저 시스템을 구현하려고 합니다.

**요구사항:**
1. FastAPI + python-socketio 서버 생성
2. 포트 8001 사용 (기존 8000은 REST API)
3. JWT 토큰 기반 인증
4. 다음 파일 구조 생성:

backend/
├── messenger/
│   ├── __init__.py
│   ├── app.py           # Socket.IO 앱
│   ├── events.py        # 이벤트 핸들러
│   ├── middleware.py    # 인증 미들웨어
│   └── handlers/
│       ├── __init__.py
│       ├── message.py   # 메시지 핸들
│       ├── typing.py    # 타이핑 핸들러
│       └── presence.py  # 온라인/오프라인

**제약 조건:**
- Python 3.11+
- python-socketio >= 5.10.0
- aioredis >= 2.0.0 (Pub/Sub용)
- 기존 backend/app/core/auth.py의 JWT 검증 로직 재사용

**출력 형식:**
- 전체 코드 (복사 가능)
- 설치 명령어 (requirements.txt 업데이트)
- 실행 방법 (uvicorn 명령어)

파일별로 완전한 코드를 생성해주세요.
```

**예상 출력:**
- `backend/messenger/app.py` (100 LOC)
- `backend/messenger/events.py` (150 LOC)
- `backend/messenger/middleware.py` (80 LOC)
- `requirements.txt` 업데이트

#### Task 1.2: Database Schema 생성

**GPT에게 지시:**
```
메신저 시스템의 PostgreSQL 스키마를 생성해주세요.

**요구사항:**
1. 4개 테이블: conversations, conversation_participants, messages, read_receipts
2. Alembic 마이그레이션 파일 생성
3. 각 테이블에 적절한 인덱스
4. Foreign Key 제약조건
5. Zone/Org별 RLS 정책 (기존 패턴 따름)

**참고 스키마:**
- users: 이미 존재 (backend/app/models/user.py)
- organizations: 이미 존재
- zones: 이미 존재

**출력 형식:**
- Alembic 마이그레이션 파일 (backend/alembic/versions/xxx_messenger_schema.py)
- SQLAlchemy 모델 (backend/app/models/messenger_models.py)
- RLS 정책 SQL (db/rls/messenger_policies.sql)

전체 코드를 생성해주세요.
```

**예상 출력:**
- 마이그레이션 파일 (200 LOC)
- 모델 파일 (300 LOC)
- RLS 정책 (100 LOC)

#### Task 1.3: REST API 엔드포인트 (대화방 CRUD)

**GPT에게 지시:**
```
메신저의 REST API를 구현해주세요.

**엔드포인트:**
1. GET /api/v1/conversations - 내 대화방 목록
2. POST /api/v1/conversations - 대화방 생성
3. GET /api/v1/conversations/{id} - 대화방 상세
4. DELETE /api/v1/conversations/{id} - 대화방 나가기
5. GET /api/v1/conversations/{id}/messages - 메시지 히스토리 (페이징)
6. POST /api/v1/conversations/{id}/messages - 메시지 전송 (폴백용)

**기술 스택:**
- FastAPI Router
- SQLAlchemy 2.0 (async)
- Pydantic v2 스키마
- JWT 인증 (Depends(get_current_user))

**참고 코드:**
- backend/app/api/routers/teacher_class.py (라우터 패턴)
- backend/app/api/schemas/exam_schemas.py (스키마 패턴)

**출력 형식:**
- 라우터 파일 (backend/app/api/routers/messenger.py)
- 스키마 파일 (backend/app/api/schemas/messenger_schemas.py)
- 테스트 파일 (backend/tests/test_messenger_api.py)

전체 코드를 생성해주세요.
```

**예상 출력:**
- 라우터 (400 LOC)
- 스키마 (200 LOC)
- 테스트 (300 LOC)

#### Task 1.4: Redis Pub/Sub 설정

**GPT에게 지시:**
```
메신저의 Redis Pub/Sub을 설정해주세요.

**요구사항:**
1. Redis 클라이언트 초기화 (기존 backend/app/core/redis.py 확장)
2. Pub/Sub 채널 관리
3. 메시지 브로드캐스트 로직

**채널 네이밍:**
- conversation:{conversation_id} - 대화방별 메시지
- user:{user_id} - 사용자별 알림
- zone:{zone_id} - Zone별 공지

**출력 형식:**
- backend/app/core/redis.py 업데이트
- backend/messenger/pubsub.py (Pub/Sub 핸들러)

전체 코드를 생성해주세요.
```

**예상 출력:**
- redis.py 업데이트 (100 LOC)
- pubsub.py (200 LOC)

---

### Week 2 - WebSocket 핸들러

#### Task 2.1: message.send 이벤트 핸들러

**GPT에게 지시:**
```
메시지 전송 이벤트를 처리하는 핸들러를 작성해주세요.

**이벤트:**
- 클라이언트 → 서버: emit('message.send', data)
- data 구조: { conversation_id, content, message_type }

**처리 로직:**
1. JWT 토큰 검증 (세션에서 user_id 추출)
2. conversation_id 권한 확인 (참가자인지)
3. 메시지 DB 저장 (messages 테이블)
4. Redis Pub/Sub으로 브로드캐스트
5. 성공 ACK 응답

**에러 처리:**
- 401: 인증 실패
- 403: 권한 없음
- 400: 잘못된 데이터
- 500: 서버 오류

**출력 형식:**
- backend/messenger/handlers/message.py 업데이트
- 테스트 파일 (backend/tests/test_message_handler.py)

전체 코드를 생성해주세요.
```

**예상 출력:**
- 핸들러 (300 LOC)
- 테스트 (200 LOC)

#### Task 2.2: message.new 브로드캐스트

**GPT에게 지시:**
```
새 메시지를 다른 참가자들에게 브로드캐스트하는 로직을 작성해주세요.

**요구사항:**
1. Redis Pub/Sub 구독
2. conversation_id별로 참가자 조회
3. 각 참가자에게 Socket.IO emit('message.new', data)
4. 오프라인 사용자는 스킵 (나중에 REST API로 조회)

**최적화:**
- 참가자 목록 Redis 캐싱 (TTL 5분)
- 배치 전송 (10개씩 묶어서)

**출력 형식:**
- backend/messenger/pubsub.py 업데이트
- 성능 테스트 (backend/tests/test_broadcast_performance.py)

전체 코드를 생성해주세요.
```

**예상 출력:**
- pubsub.py 업데이트 (200 LOC)
- 성능 테스트 (150 LOC)

#### Task 2.3: 메시지 DB 저장 & 조회

**GPT에게 지시:**
```
메시지 저장 및 히스토리 조회를 구현해주세요.

**DB 저장:**
- 비동기 INSERT (asyncpg 사용)
- 트랜잭션 처리
- 재시도 로직 (max 3회)

**히스토리 조회:**
- 페이징 (limit=50, after_id)
- 내림차순 정렬 (최신 메시지 먼저)
- 읽음/안읽음 상태 포함

**출력 형식:**
- backend/app/services/messenger_service.py (비즈니스 로직)
- backend/tests/test_messenger_service.py (테스트)

전체 코드를 생성해주세요.
```

**예상 출력:**
- 서비스 (350 LOC)
- 테스트 (250 LOC)

---

### Week 3 - Frontend UI

#### Task 3.1: 채팅 목록 컴포넌트

**GPT에게 지시:**
```
채팅 목록 UI를 React + TypeScript로 작성해주세요.

**요구사항:**
1. 대화방 리스트 표시
2. 최근 메시지 미리보기
3. 안읽은 메시지 개수 뱃지
4. 클릭 시 채팅창 열기

**디자인:**
- Tailwind CSS
- shadcn/ui 컴포넌트 사용
- 무한 스크롤 (react-intersection-observer)
- 실시간 업데이트 (Socket.IO)

**파일 구조:**
apps/portal_front/src/components/messenger/
├── ConversationList.tsx
├── ConversationItem.tsx
└── UnreadBadge.tsx

**API:**
- GET /api/v1/conversations (REST)
- Socket.IO on('message.new') (실시간)

전체 코드를 생성해주세요.
```

**예상 출력:**
- ConversationList.tsx (300 LOC)
- ConversationItem.tsx (150 LOC)
- UnreadBadge.tsx (50 LOC)

#### Task 3.2: 메시지 입력창 & 전송

**GPT에게 지시:**
```
메시지 입력창 UI를 작성해주세요.

**요구사항:**
1. 텍스트 입력 (Textarea)
2. Enter 전송, Shift+Enter 줄바꿈
3. 전송 버튼
4. 파일 첨부 버튼 (Phase 2.2)

**UX:**
- 입력 중 타이핑 이벤트 발생 (debounce 1초)
- 전송 후 입력창 초기화
- 로딩 상태 표시
- 에러 처리 (재전송 버튼)

**파일 구조:**
apps/portal_front/src/components/messenger/
├── MessageInput.tsx
└── TypingIndicator.tsx

**API:**
- Socket.IO emit('message.send')
- Socket.IO emit('message.typing')

전체 코드를 생성해주세요.
```

**예상 출력:**
- MessageInput.tsx (250 LOC)
- TypingIndicator.tsx (100 LOC)

#### Task 3.3: 메시지 리스트 (무한 스크롤)

**GPT에게 지시:**
```
메시지 리스트 UI를 작성해주세요.

**요구사항:**
1. 메시지 말풍선 (내 메시지 vs 상대 메시지)
2. 타임스탬프
3. 읽음/안읽음 표시
4. 무한 스크롤 (위로 스크롤 시 과거 메시지 로드)
5. 자동 스크롤 (새 메시지 도착 시)

**최적화:**
- 가상 스크롤 (react-window)
- 이미지 lazy loading
- 메시지 그룹핑 (같은 사용자, 5분 이내)

**파일 구조:**
apps/portal_front/src/components/messenger/
├── MessageList.tsx
├── MessageBubble.tsx
└── MessageGrouper.tsx

**API:**
- GET /api/v1/conversations/{id}/messages?after_id=xxx (REST)
- Socket.IO on('message.new') (실시간)

전체 코드를 생성해주세요.
```

**예상 출력:**
- MessageList.tsx (400 LOC)
- MessageBubble.tsx (200 LOC)
- MessageGrouper.tsx (150 LOC)

#### Task 3.4: Socket.IO 클라이언트 설정

**GPT에게 지시:**
```
Frontend의 Socket.IO 클라이언트를 설정해주세요.

**요구사항:**
1. socket.io-client 초기화
2. JWT 토큰 인증
3. 재연결 로직 (exponential backoff)
4. React Context로 전역 관리
5. Custom Hook (useSocket)

**파일 구조:**
apps/portal_front/src/lib/
├── socket.ts          # 클라이언트 초기화
├── SocketContext.tsx  # React Context
└── hooks/
    └── useSocket.ts   # Custom Hook

**에러 처리:**
- connect_error: 토스트 메시지
- disconnect: 재연결 중 표시
- reconnect: 성공 메시지

전체 코드를 생성해주세요.
```

**예상 출력:**
- socket.ts (200 LOC)
- SocketContext.tsx (150 LOC)
- useSocket.ts (100 LOC)

---

### Week 4 - 테스트 & 배포

#### Task 4.1: 통합 테스트 (메시지 중복/유실)

**GPT에게 지시:**
```
메신저의 통합 테스트를 작성해주세요.

**테스트 시나리오:**
1. 메시지 중복 방지 (같은 메시지 2번 전송 시)
2. 메시지 유실 방지 (네트워크 끊김 시)
3. 순서 보장 (A → B → C 순서 유지)
4. 동시 전송 (100명이 동시에 메시지 전송)

**도구:**
- pytest
- pytest-asyncio
- socket.io client (for testing)

**파일 구조:**
backend/tests/integration/
├── test_message_delivery.py
├── test_message_ordering.py
└── test_concurrent_send.py

전체 테스트 코드를 생성해주세요.
```

**예상 출력:**
- test_message_delivery.py (300 LOC)
- test_message_ordering.py (200 LOC)
- test_concurrent_send.py (250 LOC)

#### Task 4.2: 재연결 테스트

**GPT에게 지시:**
```
네트워크 재연결 시나리오 테스트를 작성해주세요.

**시나리오:**
1. 연결 중 메시지 전송 → 저장 확인
2. 연결 끊김 → 재연결 → 미전송 메시지 재전송
3. 오프라인 중 메시지 도착 → 재연결 후 수신
4. 재연결 시 메시지 히스토리 동기화

**도구:**
- pytest
- playwright (Frontend 테스트)

**파일 구조:**
backend/tests/integration/test_reconnection.py
apps/portal_front/tests/e2e/messenger_reconnect.spec.ts

전체 테스트 코드를 생성해주세요.
```

**예상 출력:**
- test_reconnection.py (250 LOC)
- messenger_reconnect.spec.ts (200 LOC)

#### Task 4.3: 성능 테스트 (100명 동시 접속)

**GPT에게 지시:**
```
메신저의 성능 테스트를 작성해주세요.

**목표:**
- 100명 동시 접속
- 초당 1,000 메시지 전송
- 메시지 전송 지연 < 500ms (p95)
- 메모리 사용량 < 2GB

**도구:**
- locust (부하 테스트)
- prometheus_client (메트릭 수집)

**파일 구조:**
backend/tests/load/
├── locustfile_messenger.py
└── prometheus_exporter.py

**출력:**
- 부하 테스트 스크립트
- Grafana 대시보드 JSON
- 성능 리포트 템플릿

전체 코드를 생성해주세요.
```

**예상 출력:**
- locustfile_messenger.py (300 LOC)
- prometheus_exporter.py (150 LOC)
- grafana_dashboard.json (200 LOC)

#### Task 4.4: Docker Compose & 배포 스크립트

**GPT에게 지시:**
```
메신저 서버의 Docker Compose 설정을 작성해주세요.

**서비스:**
1. messenger_server (FastAPI + Socket.IO)
2. redis (Pub/Sub)
3. nginx (Reverse Proxy)

**요구사항:**
- docker-compose.messenger.yml
- Health Check 설정
- 환경 변수 (.env.example)
- Nginx WebSocket 프록시 설정

**파일 구조:**
docker-compose.messenger.yml
.env.messenger.example
nginx/messenger.conf

전체 설정 파일을 생성해주세요.
```

**예상 출력:**
- docker-compose.messenger.yml (150 LOC)
- .env.messenger.example (30 LOC)
- nginx/messenger.conf (100 LOC)

---

## 🎯 Phase 2.2 - 고급 기능 (4주, ~20,000 LOC)

### Week 5-6 - 그룹 채팅 & 파일

#### Task 5.1: 그룹 대화방 생성/초대

**GPT에게 지시:**
```
그룹 채팅 기능을 구현해주세요.

**요구사항:**
1. 대화방 타입 'group' 추가
2. 참가자 초대 API
3. 참가자 제거 API (관리자만)
4. 그룹 이름 변경

**DB 변경:**
- conversation_participants에 role 컬럼 ('admin', 'member')
- 그룹 관리 이력 (audit_log)

**API:**
- POST /api/v1/conversations/{id}/participants
- DELETE /api/v1/conversations/{id}/participants/{user_id}
- PUT /api/v1/conversations/{id} (이름 변경)

전체 코드를 생성해주세요.
```

**예상 출력:**
- 라우터 업데이트 (300 LOC)
- 스키마 업데이트 (150 LOC)
- 테스트 (250 LOC)

#### Task 5.2: 파일 업로드 (S3/B2)

**GPT에게 지시:**
```
파일 업로드 기능을 구현해주세요.

**요구사항:**
1. 이미지 (PNG, JPG) - 최대 10MB
2. 문서 (PDF, DOCX) - 최대 10MB
3. Backblaze B2 (S3 호환) 사용
4. 썸네일 생성 (이미지만)

**보안:**
- 파일 타입 검증 (MIME type)
- 바이러스 스캔 (ClamAV 또는 VirusTotal API)
- 파일명 난독화 (UUID)

**API:**
- POST /api/v1/files/upload
- GET /api/v1/files/{id}
- DELETE /api/v1/files/{id}

**파일 구조:**
backend/app/services/file_service.py
backend/app/api/routers/files.py

전체 코드를 생성해주세요.
```

**예상 출력:**
- file_service.py (400 LOC)
- files.py (250 LOC)
- 테스트 (200 LOC)

#### Task 5.3: 이미지 썸네일 생성

**GPT에게 지시:**
```
업로드된 이미지의 썸네일을 생성해주세요.

**요구사항:**
1. Pillow 라이브러리 사용
2. 3가지 크기: small (100x100), medium (300x300), large (600x600)
3. 비동기 처리 (Celery 또는 백그라운드 태스크)
4. WebP 포맷으로 압축

**파일 구조:**
backend/app/services/thumbnail_service.py
backend/app/workers/thumbnail_worker.py

전체 코드를 생성해주세요.
```

**예상 출력:**
- thumbnail_service.py (300 LOC)
- thumbnail_worker.py (200 LOC)

#### Task 5.4: 파일 바이러스 스캔

**GPT에게 지시:**
```
업로드된 파일의 바이러스를 스캔해주세요.

**도구:**
- Option 1: ClamAV (오픈소스)
- Option 2: VirusTotal API (클라우드)

**요구사항:**
1. 업로드 직후 스캔
2. 스캔 결과 DB 저장 (file_scans 테이블)
3. 감염 파일 자동 삭제

**파일 구조:**
backend/app/services/virus_scan_service.py

전체 코드를 생성해주세요.
```

**예상 출력:**
- virus_scan_service.py (250 LOC)
- 테스트 (150 LOC)

---

### Week 7 - 실시간 기능

#### Task 7.1: 타이핑 중 표시

**GPT에게 지시:**
```
"...이 입력 중" 표시 기능을 구현해주세요.

**Backend:**
- Socket.IO emit('message.typing', { conversation_id, typing: true/false })
- Redis 캐싱 (TTL 3초)
- 같은 대화방 참가자에게만 브로드캐스트

**Frontend:**
- 1초 debounce
- 3초 후 자동 사라짐
- "홍길동이 입력 중..." 표시

**파일 구조:**
backend/messenger/handlers/typing.py
apps/portal_front/src/components/messenger/TypingIndicator.tsx

전체 코드를 생성해주세요.
```

**예상 출력:**
- typing.py (150 LOC)
- TypingIndicator.tsx (업데이트 100 LOC)

#### Task 7.2: 온라인/오프라인 상태

**GPT에게 지시:**
```
사용자 온라인/오프라인 상태를 구현해주세요.

**Backend:**
- Socket.IO connect → Redis SET user:{id}:online = true (TTL 60초)
- Socket.IO disconnect → Redis DEL user:{id}:online
- 30초마다 heartbeat (클라이언트가 ping)

**Frontend:**
- 프로필 옆에 초록/회색 점 표시
- "5분 전 접속" 같은 상대적 시간 표시

**파일 구조:**
backend/messenger/handlers/presence.py
apps/portal_front/src/components/messenger/OnlineStatus.tsx

전체 코드를 생성해주세요.
```

**예상 출력:**
- presence.py (200 LOC)
- OnlineStatus.tsx (150 LOC)

#### Task 7.3: 읽음/안읽음 표시

**GPT에게 지시:**
```
메시지 읽음/안읽음 표시를 구현해주세요.

**Backend:**
- Socket.IO emit('message.read', { message_id })
- DB INSERT INTO read_receipts
- 메시지 발신자에게 Socket.IO emit('message.read_receipt')

**Frontend:**
- 내 메시지 옆에 "읽음" 표시 (체크 2개)
- 읽지 않음: 체크 1개
- 단체방: "3명이 읽음" 표시

**파일 구조:**
backend/messenger/handlers/read_receipt.py
apps/portal_front/src/components/messenger/ReadReceipt.tsx

전체 코드를 생성해주세요.
```

**예상 출력:**
- read_receipt.py (250 LOC)
- ReadReceipt.tsx (150 LOC)

---

### Week 8 - 알림 시스템

#### Task 8.1: Push 알림 (Firebase)

**GPT에게 지시:**
```
Firebase Cloud Messaging(FCM)을 사용한 Push 알림을 구현해주세요.

**Backend:**
1. Firebase Admin SDK 설정
2. FCM 토큰 저장 (user_devices 테이블)
3. 메시지 전송 시 오프라인 사용자에게 Push

**Frontend:**
1. Firebase SDK 초기화
2. 알림 권한 요청
3. FCM 토큰 서버 전송
4. 알림 클릭 시 채팅방 열기

**파일 구조:**
backend/app/services/push_notification_service.py
apps/portal_front/src/lib/firebase.ts

전체 코드를 생성해주세요.
```

**예상 출력:**
- push_notification_service.py (300 LOC)
- firebase.ts (200 LOC)

#### Task 8.2: Email 알림 (SendGrid)

**GPT에게 지시:**
```
SendGrid를 사용한 Email 알림을 구현해주세요.

**발송 조건:**
- 사용자가 24시간 이상 오프라인
- 안읽은 메시지 5개 이상

**템플릿:**
- 제목: "[DreamSeed] 새로운 메시지가 도착했습니다"
- 본문: 발신자, 메시지 미리보기, 링크

**파일 구조:**
backend/app/services/email_notification_service.py
backend/app/templates/email/new_message.html

전체 코드를 생성해주세요.
```

**예상 출력:**
- email_notification_service.py (250 LOC)
- new_message.html (100 LOC)

#### Task 8.3: 알림 설정 UI

**GPT에게 지시:**
```
사용자별 알림 설정 UI를 구현해주세요.

**설정 항목:**
1. Push 알림 ON/OFF
2. Email 알림 ON/OFF
3. 대화방별 뮤트
4. 키워드 알림 (특정 단어 포함 시만)

**파일 구조:**
apps/portal_front/src/components/messenger/NotificationSettings.tsx
backend/app/api/routers/messenger.py (설정 API 추가)

전체 코드를 생성해주세요.
```

**예상 출력:**
- NotificationSettings.tsx (300 LOC)
- 라우터 업데이트 (150 LOC)

---

## 🎯 Phase 2.3 - 최적화 (2주, ~10,000 LOC)

### Week 9 - 성능 최적화

#### Task 9.1: 메시지 페이징 최적화

**GPT에게 지시:**
```
메시지 히스토리 조회의 성능을 최적화해주세요.

**현재 문제:**
- 1,000개 이상 메시지 조회 시 느림
- DB 쿼리가 비효율적

**최적화 방안:**
1. Cursor-based 페이징 (after_id 사용)
2. DB 인덱스 추가 (conversation_id, created_at)
3. 최근 500개만 DB 조회, 나머지는 아카이브
4. 결과 캐싱 (Redis, TTL 5분)

**파일 구조:**
backend/app/services/messenger_service.py (업데이트)
backend/alembic/versions/xxx_add_message_indexes.py

전체 코드를 생성해주세요.
```

**예상 출력:**
- 서비스 업데이트 (200 LOC)
- 마이그레이션 (50 LOC)
- 벤치마크 스크립트 (150 LOC)

#### Task 9.2: Redis 캐싱 전략

**GPT에게 지시:**
```
메신저의 Redis 캐싱 전략을 구현해주세요.

**캐시 대상:**
1. 최근 대화방 목록 (TTL 5분)
2. 참가자 목록 (TTL 10분)
3. 온라인 사용자 (TTL 1분)
4. 안읽은 메시지 개수 (TTL 30초)

**캐시 무효화:**
- 새 메시지 도착 시
- 참가자 변경 시

**파일 구조:**
backend/app/services/cache_service.py

전체 코드를 생성해주세요.
```

**예상 출력:**
- cache_service.py (350 LOC)
- 테스트 (200 LOC)

#### Task 9.3: DB 인덱스 튜닝

**GPT에게 지시:**
```
메신저 DB의 인덱스를 최적화해주세요.

**분석:**
- 느린 쿼리 로그 분석
- EXPLAIN ANALYZE 결과

**추가할 인덱스:**
1. messages(conversation_id, created_at DESC)
2. conversation_participants(user_id, conversation_id)
3. read_receipts(message_id, user_id)

**파일 구조:**
backend/alembic/versions/xxx_optimize_messenger_indexes.py
docs/performance/messenger_query_analysis.md

전체 코드를 생성해주세요.
```

**예상 출력:**
- 마이그레이션 (100 LOC)
- 분석 문서 (500 LOC)

#### Task 9.4: WebSocket 연결 풀링

**GPT에게 지시:**
```
Socket.IO 서버의 연결 풀을 최적화해주세요.

**문제:**
- 1,000명 동시 접속 시 메모리 부족
- 연결 수가 계속 증가

**해결책:**
1. Sticky Session (Nginx 설정)
2. Redis Adapter (멀티 프로세스)
3. 유휴 연결 자동 해제 (5분 무응답 시)

**파일 구조:**
backend/messenger/app.py (업데이트)
nginx/messenger.conf (업데이트)

전체 코드를 생성해주세요.
```

**예상 출력:**
- app.py 업데이트 (150 LOC)
- nginx.conf 업데이트 (100 LOC)

---

### Week 10 - 운영 준비

#### Task 10.1: Prometheus 메트릭

**GPT에게 지시:**
```
메신저의 Prometheus 메트릭을 추가해주세요.

**메트릭:**
1. messenger_messages_total (카운터)
2. messenger_messages_sent_duration_seconds (히스토그램)
3. messenger_connected_users (게이지)
4. messenger_errors_total (카운터)

**파일 구조:**
backend/messenger/metrics.py
monitoring/grafana/messenger_dashboard.json

전체 코드를 생성해주세요.
```

**예상 출력:**
- metrics.py (200 LOC)
- messenger_dashboard.json (300 LOC)

#### Task 10.2: 로깅 & 디버깅

**GPT에게 지시:**
```
메신저의 로깅 시스템을 구현해주세요.

**로그 레벨:**
- DEBUG: 모든 이벤트
- INFO: 메시지 전송/수신
- WARNING: 재연결, 타임아웃
- ERROR: DB 오류, 네트워크 오류

**로그 포맷:**
- JSON 구조화 (structlog)
- 추적 ID (trace_id)
- 사용자 ID, 대화방 ID 포함

**파일 구조:**
backend/messenger/logging_config.py

전체 코드를 생성해주세요.
```

**예상 출력:**
- logging_config.py (150 LOC)

#### Task 10.3: 백업/복구 절차

**GPT에게 지시:**
```
메신저 데이터의 백업/복구 절차를 작성해주세요.

**백업:**
1. 일일 DB 백업 (messages 테이블)
2. Redis RDB 스냅샷
3. S3/B2 파일 백업

**복구:**
1. 최근 백업에서 복원
2. 메시지 일관성 검증
3. 사용자 알림

**파일 구조:**
scripts/messenger_backup.sh
scripts/messenger_restore.sh
docs/operations/messenger_dr.md

전체 스크립트를 생성해주세요.
```

**예상 출력:**
- messenger_backup.sh (200 LOC)
- messenger_restore.sh (150 LOC)
- messenger_dr.md (400 LOC)

#### Task 10.4: 장애 대응 매뉴얼

**GPT에게 지시:**
```
메신저의 장애 대응 매뉴얼(Runbook)을 작성해주세요.

**장애 시나리오:**
1. Socket.IO 서버 다운
2. Redis 연결 실패
3. DB 쿼리 타임아웃
4. 메시지 전송 지연

**대응 절차:**
- 확인: 어떤 지표를 보는가?
- 조치: 어떻게 복구하는가?
- 알림: 누구에게 알리는가?

**파일 구조:**
docs/operations/messenger_runbook.md

전체 매뉴얼을 생성해주세요.
```

**예상 출력:**
- messenger_runbook.md (600 LOC)

---

## 📊 진행 상황 추적

### GPT 작업 체크리스트

#### Phase 2.1 (Week 1-4)
- [ ] Task 1.1: Socket.IO 서버 설정
- [ ] Task 1.2: Database Schema 생성
- [ ] Task 1.3: REST API 엔드포인트
- [ ] Task 1.4: Redis Pub/Sub 설정
- [ ] Task 2.1: message.send 핸들러
- [ ] Task 2.2: message.new 브로드캐스트
- [ ] Task 2.3: 메시지 DB 저장 & 조회
- [ ] Task 3.1: 채팅 목록 컴포넌트
- [ ] Task 3.2: 메시지 입력창
- [ ] Task 3.3: 메시지 리스트
- [ ] Task 3.4: Socket.IO 클라이언트
- [ ] Task 4.1: 통합 테스트
- [ ] Task 4.2: 재연결 테스트
- [ ] Task 4.3: 성능 테스트
- [ ] Task 4.4: Docker Compose

#### Phase 2.2 (Week 5-8)
- [ ] Task 5.1: 그룹 대화방
- [ ] Task 5.2: 파일 업로드
- [ ] Task 5.3: 썸네일 생성
- [ ] Task 5.4: 바이러스 스캔
- [ ] Task 7.1: 타이핑 중 표시
- [ ] Task 7.2: 온라인/오프라인
- [ ] Task 7.3: 읽음/안읽음
- [ ] Task 8.1: Push 알림
- [ ] Task 8.2: Email 알림
- [ ] Task 8.3: 알림 설정

#### Phase 2.3 (Week 9-10)
- [ ] Task 9.1: 페이징 최적화
- [ ] Task 9.2: Redis 캐싱
- [ ] Task 9.3: DB 인덱스
- [ ] Task 9.4: 연결 풀링
- [ ] Task 10.1: Prometheus 메트릭
- [ ] Task 10.2: 로깅
- [ ] Task 10.3: 백업/복구
- [ ] Task 10.4: 장애 대응

---

## 📝 GPT 사용 팁

### 1. 명확한 컨텍스트 제공
```
"DreamSeed AI 프로젝트의 메신저 시스템을 구현 중입니다.
현재 코드베이스는 FastAPI + PostgreSQL + Redis 구조이며,
기존 인증 시스템(JWT)과 통합해야 합니다."
```

### 2. 참고 파일 명시
```
"backend/app/api/routers/teacher_class.py의 라우터 패턴을 따라
메신저 라우터를 작성해주세요."
```

### 3. 제약 조건 명확히
```
"Python 3.11+, SQLAlchemy 2.0, Pydantic v2를 사용해야 합니다.
기존 코드 스타일(black, isort)을 따라주세요."
```

### 4. 출력 형식 지정
```
"다음 형식으로 출력해주세요:
1. 전체 코드 (복사 가능)
2. 설치 명령어
3. 테스트 방법
4. 예상 문제점 및 해결책"
```

### 5. 반복 작업 자동화
```
"이 패턴을 다른 5개 핸들러에도 적용해주세요:
- typing.py
- presence.py
- read_receipt.py
- file.py
- group.py"
```

---

## 🚀 다음 단계

### 즉시 시작 (오늘)
1. **Task 1.1부터 순차적으로 GPT에게 지시**
2. **생성된 코드를 로컬에 복사**
3. **테스트 실행 → 에러 수정**

### 주간 리뷰 (매주 금요일)
- 완료된 Task 체크
- 다음 주 계획 조정
- 블로커 해결

### Phase 완료 시
- [x] Phase 2.1 완료 → MEGACITY_EXECUTION_CHECKLIST.md 업데이트
- [x] Phase 2.2 완료 → MAINTENANCE_PLAN.md 업데이트
- [x] Phase 2.3 완료 → 프로덕션 배포

---

**작성자**: DreamSeed AI Team  
**GPT 버전**: GPT-4, Claude 3.5 Sonnet  
**예상 완료**: 2026년 3월 (10주)  
**다음 리뷰**: 매주 금요일 17:00
