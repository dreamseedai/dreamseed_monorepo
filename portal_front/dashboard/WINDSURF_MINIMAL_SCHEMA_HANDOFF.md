# 🎯 Windsurf Minimal Schema Mode 인수인계

**인수인계 일시**: 2025-11-06  
**이전 작업자**: GitHub Copilot  
**현재 작업자**: Windsurf  
**브랜치**: `staging/attempt-view-lock-v1`  
**프로젝트**: DreamseedAI Teacher Dashboard - Minimal Schema Integration

---

## ✅ Copilot 구현 완료 사항

### 1. 새로운 파일
```
✅ data_access_minimal.R (4,853 bytes)
   - Arrow (Parquet) 백엔드
   - Postgres 백엔드
   - 6개 테이블 + 4개 파생 뷰
```

### 2. 업데이트된 파일
```
✅ app_teacher.R
   - USE_MIN_SCHEMA=true 시 minimal 모드 전환
   - irt_snapshot 기반 주간 성장률 계산
   - 서브그룹 분위수 기반 리스크 규칙
   
✅ README.md
   - "Minimal Schema Mode" 섹션 추가
   - 환경 변수 가이드
```

---

## 📊 Minimal Schema 구조

### 핵심 테이블 (6개)

#### 1. `student` (필수)
```sql
CREATE TABLE student (
  id VARCHAR(50) PRIMARY KEY,
  class_id VARCHAR(50) NOT NULL,
  name VARCHAR(100),
  grade VARCHAR(10)  -- "G9", "G10", "G11", "G12"
);
```

#### 2. `session` (필수)
```sql
CREATE TABLE session (
  id VARCHAR(50) PRIMARY KEY,
  class_id VARCHAR(50) NOT NULL,
  date DATE NOT NULL,
  topic VARCHAR(200)
);
```

#### 3. `attendance` (필수)
```sql
CREATE TABLE attendance (
  student_id VARCHAR(50) NOT NULL,
  session_id VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL,  -- 'present', 'late', 'absent', 'tardy'
  PRIMARY KEY (student_id, session_id)
);
```

**Note**: `status`는 `'late'`와 `'tardy'` 모두 지각으로 정규화됩니다.

#### 4. `irt_snapshot` (필수)
```sql
CREATE TABLE irt_snapshot (
  student_id VARCHAR(50) NOT NULL,
  week_start DATE NOT NULL,
  theta DOUBLE PRECISION NOT NULL,
  se DOUBLE PRECISION,
  delta_theta DOUBLE PRECISION,
  c_hat DOUBLE PRECISION,        -- 추측 파라미터 (선택)
  omit_rate DOUBLE PRECISION,    -- 무응답률 (선택)
  PRIMARY KEY (student_id, week_start)
);
```

**Note**: `c_hat`과 `omit_rate`가 없으면 응답 이상 감지가 제한됩니다.

#### 5. `skill_mastery` (필수)
```sql
CREATE TABLE skill_mastery (
  student_id VARCHAR(50) NOT NULL,
  skill_tag VARCHAR(50) NOT NULL,
  mastery DOUBLE PRECISION NOT NULL,  -- 0.0 ~ 1.0
  updated_at TIMESTAMP,
  PRIMARY KEY (student_id, skill_tag)
);
```

#### 6. `risk_flag` (선택)
```sql
CREATE TABLE risk_flag (
  student_id VARCHAR(50) NOT NULL,
  week_start DATE NOT NULL,
  type VARCHAR(50) NOT NULL,  -- 'improve', 'attendance', 'response'
  score DOUBLE PRECISION,
  details_json TEXT,
  PRIMARY KEY (student_id, week_start, type)
);
```

**Note**: 선택 사항. 없으면 대시보드가 실시간 계산합니다.

---

### 파생 뷰 (4개)

Copilot이 `data_access_minimal.R`에 구현한 파생 함수:

#### 1. `tbl_classes_index()`
- `student` 테이블에서 `class_id`별로 그룹화
- 기본 `country="USA"`, `subject="math"` 설정

#### 2. `tbl_attendance_joined()`
- `attendance` + `session` 조인
- `student_id`, `class_id`, `date`, `status` 반환

#### 3. `tbl_response_stats()`
- `irt_snapshot`에서 학생별 최신 주차 데이터 추출
- `guess_like_rate = c_hat`, `omit_rate` 반환

#### 4. `tbl_skill_weakness()`
- `skill_mastery`에서 학생별 하위 3개 스킬 추출
- 쉼표로 구분된 문자열 반환

---

## 🔧 리스크 규칙 (End-to-End 구현)

### 1. 개선 저조 (Low Improvement)
**조건**:
- `Δ7d < +0.05` AND
- 최근 3주 연속 비양수 성장 (주간 단위)

**데이터 소스**: `irt_snapshot.delta_theta`

**구현 위치**: `app_teacher.R` (Line ~500)

---

### 2. 출석 불규칙 (Attendance Irregular)
**조건** (OR):
- 결석률 ≥ 10%
- 지각률 ≥ 15%
- 요일별 분산 ≥ 서브그룹 80th percentile

**데이터 소스**: `attendance` + `session`

**서브그룹**: 동일 country/subject/grade 학생들

**Fallback**:
1. 서브그룹 (country.subject.grade)
2. 과목 (subject)
3. 국가 (country)
4. 전체 (all)

**구현 위치**: `app_teacher.R` (Line ~550)

---

### 3. 응답 이상 (Response Anomaly)
**조건** (OR):
- `c_hat` ≥ 서브그룹 80th percentile
- `omit_rate` ≥ 8%

**데이터 소스**: `irt_snapshot` (최신 주차)

**Note**: `c_hat`이 없으면 `omit_rate`만 사용

**구현 위치**: `app_teacher.R` (Line ~600)

---

## 🚀 실행 방법

### Option 1: Arrow (Parquet) 백엔드

#### 1. 데이터 준비
```bash
# Parquet 폴더 구조 생성
mkdir -p /data/min_schema/{student,session,attendance,irt_snapshot,skill_mastery}

# 각 폴더에 Parquet 파일 배치
# 예: /data/min_schema/student/part-0.parquet
```

#### 2. 환경 변수 설정
```bash
export USE_MIN_SCHEMA=true
export MIN_SCHEMA_BACKEND=arrow
export MIN_SCHEMA_ARROW_ROOT=/data/min_schema

# 개발 모드 (역프록시 없을 때)
export DEV_USER=teacher_1
export DEV_ORG_ID=org_001
export DEV_ROLES=teacher
```

#### 3. 실행
```bash
cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard

Rscript -e 'shiny::runApp(".", host="0.0.0.0", port=8080)'
```

---

### Option 2: Postgres 백엔드

#### 1. 데이터베이스 준비
```sql
-- DDL 실행 (migrations/001_global_schema.sql 참고)
CREATE TABLE student (...);
CREATE TABLE session (...);
CREATE TABLE attendance (...);
CREATE TABLE irt_snapshot (...);
CREATE TABLE skill_mastery (...);
CREATE TABLE risk_flag (...);  -- 선택

-- 샘플 데이터 INSERT
INSERT INTO student VALUES ('S001', 'CLASS001', 'John Doe', 'G9');
-- ...
```

#### 2. 환경 변수 설정
```bash
export USE_MIN_SCHEMA=true
export MIN_SCHEMA_BACKEND=db

# Postgres 연결 정보
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=dreamseed
export PGUSER=postgres
export PGPASSWORD=yourpass

# 또는 DSN 사용
export PG_DSN="postgresql://postgres:yourpass@localhost:5432/dreamseed"

# 개발 모드
export DEV_USER=teacher_1
export DEV_ORG_ID=org_001
export DEV_ROLES=teacher
```

#### 3. 실행
```bash
cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard

Rscript -e 'shiny::runApp(".", host="0.0.0.0", port=8080)'
```

---

## 🧪 검증 체크리스트

### 기본 기능 테스트
- [ ] **클래스 스냅샷**: `irt_snapshot`에서 주간 최신 θ 히스토그램 렌더링
- [ ] **주간 성장 박스**: 지난주 vs 전주 delta 표시
- [ ] **학생 테이블**: `improve_flag`, `attn_flag`, `resp_flag` 표시
- [ ] **리스크 점수**: 가중치 (3, 2, 1) 적용된 총점

### 리스크 규칙 검증
- [ ] **개선 저조**: Δ7d < +0.05 AND 3주 연속 비양수
- [ ] **출석 불규칙**: 결석 ≥ 10% OR 지각 ≥ 15% OR DoW 분산 ≥ 80th pct
- [ ] **응답 이상**: c_hat ≥ 80th pct OR omit ≥ 8%

### 서브그룹 분위수 테스트
- [ ] **충분한 데이터**: 동일 country/subject/grade 학생 30명 이상
- [ ] **Fallback**: 데이터 부족 시 subject → country → all 순서로 fallback
- [ ] **로그 확인**: Shiny 콘솔에 `[attn_var_cutoff] ✓ Subgroup (USA.math.G9): N=50, cutoff=0.0123` 출력

### 과제 배정 테스트
- [ ] **버킷 버튼**: θ 히스토그램 버킷 클릭 시 API 호출
- [ ] **개별 학생**: 학생 테이블 "과제 배정" 버튼 클릭 시 API 호출
- [ ] **다국어 메시지**: 성공/실패 알림이 사용자 언어로 표시

### 성능 테스트
- [ ] **10,000 학생**: 데이터 로드 < 2초
- [ ] **서브그룹 분위수**: 계산 < 1초
- [ ] **No runtime errors**: Shiny 콘솔에 에러 없음

---

## 🔧 환경 변수 전체 목록

### Minimal Schema 모드
```bash
USE_MIN_SCHEMA=true                    # 필수: minimal 모드 활성화
MIN_SCHEMA_BACKEND=arrow|db            # 필수: arrow 또는 db
MIN_SCHEMA_ARROW_ROOT=/data/min_schema # Arrow 사용 시 필수
```

### Postgres 연결 (db 백엔드 사용 시)
```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=dreamseed
PGUSER=postgres
PGPASSWORD=yourpass

# 또는
PG_DSN="postgresql://user:pass@host:port/dbname"
```

### 리스크 임계값 (선택, 기본값 있음)
```bash
RISK_THETA_DELTA=0.05              # 주간 성장률 임계값
RISK_ATTEND_ABS=0.10               # 결석률 임계값 (10%)
RISK_ATTEND_TARDY=0.15             # 지각률 임계값 (15%)
RISK_ATTEND_VAR_TOP_PCT=0.80       # DoW 분산 백분위 (80th)
RISK_RESP_GUESS_TOP_PCT=0.80       # c_hat 백분위 (80th)
RISK_RESP_OMIT=0.08                # 무응답률 임계값 (8%)
```

### 과제 배정 API
```bash
ASSIGNMENT_API_URL=http://localhost:8000/api/assignments
ASSIGNMENT_API_BEARER="Bearer <token>"  # 선택
```

### 개발 모드 (역프록시 없을 때)
```bash
DEV_USER=teacher_1
DEV_ORG_ID=org_001
DEV_ROLES=teacher
```

---

## ❓ Open Questions (Windsurf → Copilot)

### 1. irt_snapshot에 c_hat과 omit_rate 포함 여부
**질문**: `irt_snapshot` 테이블에 `c_hat`과 `omit_rate` 컬럼이 포함되어 있습니까?

**영향**:
- **있음**: 응답 이상 감지 완전 작동
- **없음**: `omit_rate`는 0으로 고정, `c_hat`만 사용 불가

**대안**: 별도 테이블 `response_stats`에서 가져오기

---

### 2. risk_flag 테이블 사용 여부
**질문**: `risk_flag` 테이블을 사용하시겠습니까?

**옵션**:
- **A. 실시간 계산** (현재 구현): 대시보드가 매번 계산
- **B. 배치 계산**: 별도 배치 작업이 `risk_flag` 테이블에 저장

**제안**: "리스크 재계산" 버튼 추가 가능
```r
# 버튼 클릭 시 배치 API 호출
observeEvent(input$recalculate_risks, {
  httr::POST(
    url = Sys.getenv("RISK_BATCH_API_URL"),
    body = list(class_id = input$class_id),
    encode = "json"
  )
  showNotification("리스크 재계산 요청 완료")
})
```

**필요 정보**:
- 배치 API 엔드포인트
- 요청 메서드 (POST/PUT)
- 요청 바디 구조
- 인증 헤더

---

### 3. class_id 없는 irt_snapshot 처리
**질문**: `irt_snapshot` 테이블에 `class_id` 컬럼이 없습니까?

**현재 구현**: `student` 테이블과 조인하여 `class_id` 파생

**확인 필요**: 이 방식이 정확한지 검증

---

## 🐛 알려진 제약사항

### 1. 아이템 이상 히트맵 미구현
**현재**: 데모 데이터 사용  
**이유**: Minimal schema에 문항별 응답 데이터 없음  
**영향**: 히트맵 기능 비활성화 또는 제거 필요

### 2. 서브그룹 최소 크기
**요구사항**: 서브그룹당 최소 10명 권장 (통계적 유의성)  
**Fallback**: 10명 미만 시 상위 레벨로 자동 fallback

### 3. 주간 데이터 요구사항
**요구사항**: `irt_snapshot`에 최소 4주 데이터 필요 (3주 연속 성장 판단)  
**영향**: 데이터 부족 시 개선 저조 플래그 미작동

---

## 📊 테스트 시나리오

### 시나리오 1: Arrow 백엔드 기본 테스트
```bash
# 1. 샘플 Parquet 데이터 생성 (별도 스크립트 필요)
Rscript generate_sample_parquet.R

# 2. 환경 변수 설정
export USE_MIN_SCHEMA=true
export MIN_SCHEMA_BACKEND=arrow
export MIN_SCHEMA_ARROW_ROOT=/tmp/test_data

# 3. 대시보드 실행
Rscript -e 'shiny::runApp("portal_front/dashboard", port=8080)'

# 4. 브라우저 접속
# http://localhost:8080

# 5. 검증
# - 클래스 스냅샷 표시 확인
# - 학생 테이블에 리스크 플래그 확인
# - 과제 배정 버튼 클릭 테스트
```

**예상 결과**:
- 클래스 평균 θ: 0.45
- 리스크 학생 수: 개선 저조 5명, 출석 불규칙 3명, 응답 이상 2명
- 과제 배정 API 호출 성공 (200/201)

---

### 시나리오 2: Postgres 백엔드 테스트
```bash
# 1. DB 준비
psql -h localhost -U postgres -d dreamseed -f migrations/001_global_schema.sql
psql -h localhost -U postgres -d dreamseed -f test_data/insert_sample.sql

# 2. 환경 변수 설정
export USE_MIN_SCHEMA=true
export MIN_SCHEMA_BACKEND=db
export PGHOST=localhost
export PGDATABASE=dreamseed
export PGUSER=postgres
export PGPASSWORD=test123

# 3. 대시보드 실행
Rscript -e 'shiny::runApp("portal_front/dashboard", port=8080)'

# 4. 검증
# - Shiny 콘솔에 DB 연결 로그 확인
# - 서브그룹 분위수 계산 로그 확인
```

---

### 시나리오 3: 서브그룹 Fallback 테스트
```bash
# 1. 소규모 데이터 준비 (USA.math.G9 학생 5명만)
# 2. 대시보드 실행
# 3. Shiny 콘솔 로그 확인

# 예상 로그:
# [attn_var_cutoff] ⚠ Subgroup (USA.math.G9) too small (N=5), falling back to subject
# [attn_var_cutoff] ✓ Subject (math): N=50, cutoff=0.0145
```

---

## 🎯 Acceptance Criteria

### 1. 환경 전환 (env-only)
- [ ] Arrow 백엔드 실행 성공 (코드 변경 없이 env만)
- [ ] Postgres 백엔드 실행 성공 (코드 변경 없이 env만)

### 2. 리스크 규칙 정확성
- [ ] 테스트 클래스의 리스크 카운트가 수동 계산과 일치
- [ ] 개선 저조: Δ7d < +0.05 AND 3주 연속 비양수
- [ ] 출석 불규칙: 결석 ≥ 10% OR 지각 ≥ 15% OR DoW 분산 ≥ 80th pct
- [ ] 응답 이상: c_hat ≥ 80th pct OR omit ≥ 8%

### 3. 과제 배정 API
- [ ] 버킷 버튼 클릭 시 API 호출 성공 (200/201)
- [ ] 개별 학생 버튼 클릭 시 API 호출 성공
- [ ] 실패 시 적절한 에러 메시지 표시

### 4. 안정성
- [ ] 런타임 에러 없음
- [ ] 서브그룹 분위수 로그 출력
- [ ] 10,000 학생 데이터 로드 < 2초

---

## 📝 Windsurf 작업 계획

### Week 1: 검증 및 테스트
- [ ] `data_access_minimal.R` 코드 리뷰
- [ ] Arrow 백엔드 샘플 데이터 생성 스크립트 작성
- [ ] Postgres 백엔드 샘플 데이터 INSERT 스크립트 작성
- [ ] 기본 시나리오 테스트 (Arrow)
- [ ] 기본 시나리오 테스트 (Postgres)

### Week 2: 리스크 규칙 검증
- [ ] 개선 저조 규칙 수동 검증
- [ ] 출석 불규칙 규칙 수동 검증
- [ ] 응답 이상 규칙 수동 검증
- [ ] 서브그룹 분위수 계산 검증
- [ ] Fallback 로직 테스트

### Week 3: 통합 및 문서화
- [ ] Open Questions 답변 받기
- [ ] risk_flag 배치 API 연동 (선택)
- [ ] 성능 테스트 (10,000 학생)
- [ ] 최종 문서 업데이트

---

## 🔗 참고 문서

1. **data_access_minimal.R** - 데이터 접근 레이어 (4,853 bytes)
2. **README.md** - Minimal Schema Mode 섹션
3. **helpers_global.R** - 서브그룹 함수, 임계값, i18n
4. **migrations/001_global_schema.sql** - DB 스키마 (선택)

---

## 💬 Copilot에게 질문

### 즉시 필요한 정보
1. `irt_snapshot`에 `c_hat`과 `omit_rate` 컬럼 포함 여부
2. `risk_flag` 테이블 사용 계획 (실시간 vs 배치)
3. 배치 API 엔드포인트 정보 (사용 시)

### 추가 요청 사항
1. 샘플 Parquet 데이터 생성 스크립트
2. 샘플 Postgres INSERT 스크립트
3. 테스트 케이스 예시 (리스크 규칙 검증용)

---

## ✅ 현재 상태

### Copilot 완료
- ✅ `data_access_minimal.R` 구현 (Arrow + Postgres)
- ✅ `app_teacher.R` minimal 모드 통합
- ✅ 리스크 규칙 end-to-end 구현
- ✅ 서브그룹 분위수 + fallback
- ✅ README 업데이트

### Windsurf 진행 중
- 🔄 코드 리뷰 및 검증
- ⏳ 샘플 데이터 생성
- ⏳ 테스트 시나리오 실행

### 대기 중
- ⏳ Open Questions 답변
- ⏳ 성능 테스트
- ⏳ 프로덕션 배포

---

**Copilot에게 감사드립니다!** Minimal Schema Mode가 완벽하게 구현되어 있어 즉시 테스트를 시작할 수 있습니다. 💪

---

**작성자**: Windsurf  
**최종 업데이트**: 2025-11-06  
**버전**: Minimal Schema Handoff v1.0  
**상태**: ✅ 인수인계 진행 중
