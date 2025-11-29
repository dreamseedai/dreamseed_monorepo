# 🗨️ DreamSeed AI - 실시간 메신저 시스템 설계

> **MegaCity Phase 2-3 핵심 기능**  
> **작성일**: 2025-11-25  
> **우선순위**: 🔴 P0 - Phase 2 Blocker

---

## 📊 Executive Summary

### 왜 메신저가 중요한가?

**교육 플랫폼의 핵심 = 소통**
- 학생이 막혔을 때 → **즉시 선생님에게 질문**
- 부모가 궁금할 때 → **즉시 선생님과 상담**
- 선생님이 알릴 때 → **즉시 학생/부모에게 공지**

**실제 사용 시나리오:**
```
17:30 - 학생: "선생님, 이 문제 어떻게 푸나요?" (즉시 답변 필요)
18:00 - 부모: "우리 아이 성적이 떨어졌는데 상담 가능한가요?"
19:00 - 선생님: "내일 시험 범위 변경되었습니다" (전체 공지)
```

**메신저 없으면 → 이메일/전화 → 응답 지연 → 사용자 이탈**

---

## 📐 규모 추정

### 코드 라인 수 예상

| 컴포넌트 | 예상 라인 수 | 근거 |
|---------|-------------|------|
| **Backend (FastAPI + Socket.IO)** | 15,000~20,000 | WebSocket 서버, 메시지 라우팅, DB 저장 |
| **Frontend (React + Socket.IO)** | 10,000~15,000 | 채팅 UI, 실시간 업데이트, 알림 |
| **Database Schema** | 500~1,000 | messages, conversations, participants, read_receipts |
| **Redis (Pub/Sub)** | 1,000~2,000 | 실시간 브로드캐스트, 온라인 상태 |
| **파일 업로드 (S3)** | 2,000~3,000 | 이미지/PDF 첨부 |
| **알림 시스템** | 3,000~5,000 | Push/Email/SMS 알림 |
| **테스트** | 5,000~8,000 | 메시지 중복/유실, 재연결 테스트 |
| **문서화** | 1,000~2,000 | API 문서, 아키텍처 다이어그램 |
| **TOTAL** | **37,500~56,000 라인** | **약 40,000~50,000 라인** |

**결론: 메신저는 단독으로 4~5만 라인 규모의 중형 프로젝트!**

---

## 🎯 핵심 기능 요구사항

### 1. 1:1 채팅 (Direct Message)
- 학생 ↔ 선생님
- 부모 ↔ 선생님
- 튜터 ↔ 학생

### 2. 그룹 채팅 (Group Chat)
- 학급별 채팅방 (1반, 2반 등)
- 과목별 채팅방 (수학반, 영어반)
- 학부모 모임

### 3. 공지 채널 (Announcement)
- 선생님 → 전체 학생
- 원장 → 전체 선생님
- Read-only (답장 불가)

### 4. 파일 공유
- 이미지 (PNG, JPG)
- 문서 (PDF, DOCX)
- 최대 10MB
- 바이러스 스캔

### 5. 실시간 기능
- 타이핑 중 표시 ("...이 입력 중")
- 온라인/오프라인 상태
- 읽음/안읽음 표시
- 실시간 알림

### 6. 검색 & 히스토리
- 메시지 내용 검색
- 날짜별 필터링
- 무한 스크롤
- 30일 이후 자동 아카이브

---

## 🏗️ 아키텍처 설계

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Client (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Chat Window  │  │ Message List │  │ Notification │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└──────────────┬──────────────────────────────────────────┘
               │ Socket.IO (WebSocket)
               ▼
┌─────────────────────────────────────────────────────────┐
│              FastAPI + Socket.IO Server                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ Auth Handler │  │ Msg Router   │  │ File Handler │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└──────┬──────────────┬────────────────┬─────────────────┘
       │              │                │
       ▼              ▼                ▼
┌──────────┐   ┌────────────┐   ┌──────────┐
│PostgreSQL│   │   Redis    │   │ S3 (B2)  │
│ Messages │   │  Pub/Sub   │   │  Files   │
└──────────┘   └────────────┘   └──────────┘
```

### Database Schema

```sql
-- 대화방 (1:1, 그룹, 공지)
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    type VARCHAR(20), -- 'direct', 'group', 'announcement'
    title VARCHAR(255),
    zone_id UUID, -- MegaCity Zone
    org_id UUID,  -- 조직 (학원)
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 참가자
CREATE TABLE conversation_participants (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(20), -- 'admin', 'member', 'observer'
    joined_at TIMESTAMP,
    last_read_at TIMESTAMP,
    UNIQUE(conversation_id, user_id)
);

-- 메시지
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    sender_id UUID REFERENCES users(id),
    content TEXT,
    message_type VARCHAR(20), -- 'text', 'image', 'file', 'system'
    file_url TEXT,
    file_size INTEGER,
    file_name VARCHAR(255),
    created_at TIMESTAMP,
    edited_at TIMESTAMP,
    deleted_at TIMESTAMP -- soft delete
);

-- 읽음 상태
CREATE TABLE read_receipts (
    id UUID PRIMARY KEY,
    message_id UUID REFERENCES messages(id),
    user_id UUID REFERENCES users(id),
    read_at TIMESTAMP,
    UNIQUE(message_id, user_id)
);

-- 알림 설정
CREATE TABLE notification_settings (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    conversation_id UUID REFERENCES conversations(id),
    muted BOOLEAN DEFAULT false,
    push_enabled BOOLEAN DEFAULT true,
    email_enabled BOOLEAN DEFAULT true,
    UNIQUE(user_id, conversation_id)
);

-- 인덱스 (성능 최적화)
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_participants_user ON conversation_participants(user_id);
CREATE INDEX idx_read_receipts_message ON read_receipts(message_id);
```

### API Endpoints

#### REST API (초기 로딩)
```
GET    /api/v1/conversations              - 내 대화방 목록
POST   /api/v1/conversations              - 대화방 생성
GET    /api/v1/conversations/{id}         - 대화방 상세
DELETE /api/v1/conversations/{id}         - 대화방 나가기

GET    /api/v1/conversations/{id}/messages - 메시지 히스토리 (페이징)
POST   /api/v1/conversations/{id}/messages - 메시지 전송 (폴백)
DELETE /api/v1/messages/{id}               - 메시지 삭제

POST   /api/v1/conversations/{id}/participants - 참가자 추가
DELETE /api/v1/conversations/{id}/participants/{user_id} - 참가자 제거

POST   /api/v1/files/upload                - 파일 업로드
GET    /api/v1/files/{id}                  - 파일 다운로드
```

#### WebSocket Events (실시간)
```javascript
// Client → Server
emit('message.send', {
  conversation_id: 'uuid',
  content: 'Hello',
  message_type: 'text'
})

emit('message.typing', {
  conversation_id: 'uuid',
  typing: true
})

emit('message.read', {
  message_id: 'uuid'
})

// Server → Client
on('message.new', (data) => {
  // 새 메시지 수신
})

on('message.typing', (data) => {
  // 타이핑 중 표시
})

on('message.read', (data) => {
  // 읽음 상태 업데이트
})

on('user.online', (data) => {
  // 사용자 온라인
})

on('user.offline', (data) => {
  // 사용자 오프라인
})
```

---

## 🚀 구현 계획 (Phase별)

### Phase 2.1 - MVP (4주, ~15,000 LOC)

**목표**: 1:1 채팅 + 텍스트 메시지만

**Week 1 - Backend 기초**
- [ ] Socket.IO 서버 설정
- [ ] DB Schema 생성
- [ ] JWT 인증 연동
- [ ] 기본 REST API (대화방 CRUD)

**Week 2 - WebSocket 핸들러**
- [ ] message.send 이벤트
- [ ] message.new 브로드캐스트
- [ ] Redis Pub/Sub 연동
- [ ] 메시지 DB 저장

**Week 3 - Frontend UI**
- [ ] 채팅 목록 컴포넌트
- [ ] 메시지 입력창
- [ ] 메시지 리스트 (무한 스크롤)
- [ ] 실시간 업데이트

**Week 4 - 테스트 & 배포**
- [ ] 통합 테스트 (메시지 중복/유실)
- [ ] 재연결 테스트
- [ ] 성능 테스트 (100명 동시 접속)
- [ ] 스테이징 배포

### Phase 2.2 - 고급 기능 (4주, ~20,000 LOC)

**Week 5-6 - 그룹 채팅 & 파일**
- [ ] 그룹 대화방 생성/초대
- [ ] 파일 업로드 (S3/B2)
- [ ] 이미지 썸네일 생성
- [ ] 파일 바이러스 스캔

**Week 7 - 실시간 기능**
- [ ] 타이핑 중 표시
- [ ] 온라인/오프라인 상태
- [ ] 읽음/안읽음 표시
- [ ] Read receipts

**Week 8 - 알림 시스템**
- [ ] Push 알림 (Firebase)
- [ ] Email 알림 (SendGrid)
- [ ] 알림 설정 UI
- [ ] 뮤트 기능

### Phase 2.3 - 최적화 (2주, ~10,000 LOC)

**Week 9 - 성능 최적화**
- [ ] 메시지 페이징 최적화
- [ ] Redis 캐싱 (최근 대화방)
- [ ] DB 인덱스 튜닝
- [ ] WebSocket 연결 풀링

**Week 10 - 운영 준비**
- [ ] 모니터링 (메시지 전송률, 에러율)
- [ ] 로깅 (메시지 이력)
- [ ] 백업/복구 절차
- [ ] 장애 대응 매뉴얼

**총 10주 = 2.5개월 = Phase 2 중반~후반**

---

## 📊 리소스 요구사항

### 인프라

| 리소스 | Phase 2.1 (MVP) | Phase 2.2 (Full) | Phase 3 (10K 유저) |
|--------|-----------------|------------------|-------------------|
| WebSocket 서버 | 1대 (2 vCPU) | 2대 (Load Balance) | 5대 (Auto Scale) |
| Redis | 1 instance | 3-node cluster | 10-node cluster |
| PostgreSQL | 기존 사용 | 기존 + 1 replica | 기존 + 3 replicas |
| S3/B2 Storage | 10GB | 100GB | 1TB |
| 월 비용 | +$50 | +$150 | +$500 |

### 팀

- Backend 개발자 1명 (FastAPI + Socket.IO)
- Frontend 개발자 1명 (React + Socket.IO)
- QA 엔지니어 0.5명 (테스트)
- DevOps 0.5명 (배포/모니터링)

---

## 🔒 보안 & 규정 준수

### 보안 요구사항

1. **인증**: JWT 토큰 검증 (WebSocket 연결 시)
2. **권한**: Zone/Org별 접근 제어 (RLS)
3. **암호화**: TLS/SSL (WebSocket wss://)
4. **필터링**: 욕설/부적절한 내용 차단
5. **Rate Limit**: 1초당 10 메시지 (스팸 방지)

### 규정 준수 (GDPR/PIPA)

- 메시지 30일 후 자동 아카이브
- 사용자 탈퇴 시 메시지 삭제 (Right to be forgotten)
- 메시지 내용 검색 시 개인정보 마스킹
- Audit Log (누가 언제 무엇을 읽었는지)

---

## 📈 성공 지표 (KPIs)

### 기술 지표

- **메시지 전송 성공률**: > 99.9%
- **메시지 전송 지연**: < 500ms (p95)
- **WebSocket 재연결 시간**: < 2초
- **동시 접속자 수**: 1,000명 (Phase 2), 10,000명 (Phase 3)
- **장애 복구 시간 (MTTR)**: < 10분

### 비즈니스 지표

- **일일 활성 메시지 수**: 10,000+ (Phase 2)
- **메신저 사용률**: 80%+ (가입자 중)
- **평균 응답 시간**: < 5분 (선생님 → 학생)
- **사용자 만족도**: 4.5+ / 5.0

---

## 🚨 위험 요소 & 대응

### 위험 1: 메시지 유실
**대응**: Redis Pub/Sub + PostgreSQL 이중 저장, ACK 메커니즘

### 위험 2: 서버 과부하 (많은 동시 접속)
**대응**: Load Balancer + Auto Scaling, Redis Cluster

### 위험 3: 스팸/악용
**대응**: Rate Limiting, 신고 기능, AI 기반 욕설 필터

### 위험 4: 개인정보 유출
**대응**: TLS 암호화, RLS 정책, Audit Log

### 위험 5: 개발 지연
**대응**: MVP 먼저 출시 (1:1 텍스트만), 고급 기능은 Phase 2.2

---

## 📚 참고 자료

### 오픈소스 참고

- [Rocket.Chat](https://github.com/RocketChat/Rocket.Chat) - 오픈소스 채팅 플랫폼
- [Matrix](https://matrix.org/) - 분산 메시징 프로토콜
- [Mattermost](https://github.com/mattermost/mattermost-server) - Slack 대체

### 기술 스택

- **Backend**: FastAPI + python-socketio
- **Frontend**: React + socket.io-client
- **Database**: PostgreSQL + Redis
- **Storage**: Backblaze B2 (S3 호환)
- **Monitoring**: Prometheus + Grafana

### 학습 자료

- [Socket.IO 공식 문서](https://socket.io/docs/v4/)
- [Real-time Chat App Tutorial](https://testdriven.io/blog/real-time-chat-with-fastapi-and-socketio/)
- [Scaling WebSocket](https://blog.cloudflare.com/how-to-scale-websockets/)

---

## 📝 다음 단계 (Action Items)

### 즉시 (이번 주)

1. **기술 스택 확정**
   - [ ] Socket.IO vs WebSocket 네이티브 비교
   - [ ] Redis vs RabbitMQ 선택

2. **DB Schema 리뷰**
   - [ ] DBA와 Schema 검토
   - [ ] 인덱스 전략 확정

3. **POC (Proof of Concept)**
   - [ ] 간단한 1:1 채팅 프로토타입 (1일)
   - [ ] 100명 동시 접속 부하 테스트 (1일)

### 단기 (1개월)

4. **Phase 2.1 킥오프**
   - [ ] 팀 구성 (Backend/Frontend/QA)
   - [ ] Sprint 계획 (4주)
   - [ ] MEGACITY_EXECUTION_CHECKLIST.md 업데이트

5. **문서 작성**
   - [ ] API 스펙 (OpenAPI)
   - [ ] Frontend 디자인 (Figma)
   - [ ] 테스트 계획서

### 중기 (3개월)

6. **Phase 2.2-2.3 완료**
   - [ ] 그룹 채팅 출시
   - [ ] 파일 공유 출시
   - [ ] 10,000명 동시 접속 달성

---

**작성자**: DreamSeed AI Team  
**리뷰어**: Architecture & Product Team  
**승인**: CTO / CPO  
**다음 리뷰**: 2025-12-02 (Phase 2 킥오프 전)
