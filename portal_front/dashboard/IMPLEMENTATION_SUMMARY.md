# Teacher Dashboard - Complete Implementation Summary

## ✅ 완료된 기능 (1~4번 모두 구현)

### 1. 버킷별 CTA → 과제 배정 API 연동 ✅
**파일**: `portal_front/dashboard/app_teacher.R`
- 5개 버킷 CTA 버튼 (매우낮음/낮음/중간/높음/매우높음)
- 클릭 시 자동 필터링 + 과제 배정 API 호출
- 활성 필터 시각적 표시 (파란색 강조)
- "필터 초기화" 버튼 추가

**API 파일**: `portal_api/assignment_api.py`
- FastAPI 엔드포인트: `POST /api/assignments`
- 5가지 과제 템플릿 매핑
- JWT 헤더 검증 (X-User, X-Org-Id)
- 배정 로그 및 응답 반환

**실행**:
```bash
# API 서버 (터미널 1)
cd portal_api
uvicorn assignment_api:app --host 0.0.0.0 --port 8000 --reload

# Shiny 대시보드 (터미널 2)
export ASSIGNMENT_API_URL=http://localhost:8000/api/assignments
Rscript portal_front/dashboard/app_teacher.R
```

---

### 2. 학생 필터링 구현 ✅
**파일**: `portal_front/dashboard/app_teacher.R`
- `bucket_filter` reactive state 추가
- `students_tbl()` 에서 필터 조건 동적 적용
- 버킷별 θ 범위 자동 필터:
  - very_low: θ <= -1.5
  - low: -1.5 < θ <= -0.5
  - mid: -0.5 < θ <= 0.5
  - high: 0.5 < θ <= 1.5
  - very_high: θ > 1.5
- DT 테이블 자동 갱신

---

### 3. 문항 이상 패턴 세부 분석 ✅
**파일**: `portal_front/dashboard/app_teacher.R`

#### A. 4개 패턴 value box 추가:
- **Pure Guessing**: guess_rate > 15% & omit < 5%
- **Strategic Omit**: omit_rate > 12% & guess < 5%
- **Rapid-Fire**: rapid_fire_rate > 10% & avg_time < 20초
- **복합 이상 패턴**: 3가지 모두 충족

#### B. 문항별 이상치 히트맵:
- `item_response_patterns` 데이터셋 추가
- 이상률 상위 20개 문항 자동 선택
- Plotly 히트맵 (X=문항ID, Y=패턴, Z=이상률)
- Collapsible 섹션으로 UI 정리

#### C. 데이터 부트스트랩:
- `response_stats`에 `rapid_fire_rate`, `avg_response_time` 추가
- `item_response_patterns` 신규 생성 (문항×학생 레벨)

---

### 4. 실시간 데이터 ETL 파이프라인 ✅
**파일**: `portal_front/dashboard/etl_realtime.R`

#### 기능:
- **학사 출결 시스템** → attendance 동기화
- **평가 시스템** → response_stats 동기화
- 증분 업데이트 (since 파라미터)
- 중복 제거 및 Parquet 파티션 유지
- 5분마다 자동 폴링 (설정 가능)

#### 실행:
```bash
# 로컬 테스트
export DATASET_ROOT=data/datasets
export ATTENDANCE_API=http://localhost:8000/api/attendance
export RESPONSE_API=http://localhost:8000/api/response_stats
export ETL_INTERVAL=300
Rscript portal_front/dashboard/etl_realtime.R
```

#### Systemd 서비스:
- `/etc/systemd/system/dashboard-etl.service` 설정 예시 제공
- 프로덕션 환경 자동 시작/재시작

---

## 파일 구조

```
portal_front/dashboard/
├── app_teacher.R                # 교사용 대시보드 (메인)
├── etl_realtime.R               # 실시간 ETL 파이프라인
└── README_teacher.md            # 통합 문서 (업데이트됨)

portal_api/
└── assignment_api.py            # 과제 배정 FastAPI 서버

data/datasets/                   # Parquet 데이터셋
├── classes/
├── students/
├── student_theta/
├── attendance/
├── skill_weakness/
├── response_stats/              # ← rapid_fire_rate, avg_response_time 추가
└── item_response_patterns/      # ← 신규 추가
```

---

## 실행 순서

### 1. 과제 배정 API 시작
```bash
cd portal_api
pip install fastapi uvicorn pydantic
uvicorn assignment_api:app --host 0.0.0.0 --port 8000 --reload
```

### 2. ETL 파이프라인 시작 (선택)
```bash
export DATASET_ROOT=data/datasets
export ATTENDANCE_API=http://localhost:8000/api/attendance
export RESPONSE_API=http://localhost:8000/api/response_stats
Rscript portal_front/dashboard/etl_realtime.R &
```

### 3. 교사용 대시보드 시작
```bash
export DEV_USER=teacher01
export DEV_ORG_ID=org_001
export DEV_ROLES=teacher
export ASSIGNMENT_API_URL=http://localhost:8000/api/assignments
Rscript -e 'shiny::runApp("portal_front/dashboard/app_teacher.R", host="0.0.0.0", port=8081)'
```

### 4. 브라우저 접속
```
http://localhost:8081
```

---

## 테스트 시나리오

1. **클래스 선택**: 드롭다운에서 클래스 선택
2. **KPI 확인**: 6개 value box (평균 θ, 중앙값, 범위, 성장률, 출석, 리스크)
3. **히스토그램 확인**: 5색 구간별 학생 분포
4. **버킷 CTA 클릭**:
   - "매우낮음 15명 → 보정 과제" 클릭
   - 학생 테이블이 θ <= -1.5 필터링됨
   - API 호출 성공 알림 표시
   - 버튼이 파란색으로 강조
5. **필터 초기화**: "필터 초기화" 클릭 → 전체 학생 복구
6. **문항 이상 패턴**: Collapsible 섹션 확장
   - 4개 패턴 카드 확인
   - 히트맵으로 문항별 이상률 시각화
7. **학생 드릴다운**: 테이블 행 클릭 → 모달 팝업
   - 4주 θ 스파크라인
   - 출석 타임라인
   - 취약 스킬태그

---

## 프로덕션 배포

### Nginx 리버스 프록시
```nginx
location /dashboard/teacher/ {
    proxy_pass http://localhost:8081/;
    proxy_set_header X-User $jwt_claim_sub;
    proxy_set_header X-Org-Id $jwt_claim_org_id;
    proxy_set_header X-Roles $jwt_claim_roles;
}

location /api/assignments {
    proxy_pass http://localhost:8000/api/assignments;
    proxy_set_header X-User $jwt_claim_sub;
    proxy_set_header X-Org-Id $jwt_claim_org_id;
}
```

### Systemd 서비스
```bash
# Shiny 대시보드
sudo systemctl enable shiny-teacher-dashboard
sudo systemctl start shiny-teacher-dashboard

# ETL 파이프라인
sudo systemctl enable dashboard-etl
sudo systemctl start dashboard-etl

# Assignment API
sudo systemctl enable assignment-api
sudo systemctl start assignment-api
```

---

## 다음 확장 가능

- [ ] 버킷별 과제 배정 이력 조회
- [ ] 학생 진도율 실시간 모니터링
- [ ] 교사 알림 시스템 (리스크 학생 자동 알림)
- [ ] 학부모 연계 (학생 리포트 자동 전송)
- [ ] 대시보드 다국어 지원 (i18n)
