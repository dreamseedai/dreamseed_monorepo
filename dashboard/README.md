# 교사용 클래스 모니터링 대시보드

## ⚠️ 중요 안내

**프로덕션 준비 버전은 `/portal_front/dashboard/` 디렉토리에 있습니다.**

이 디렉토리(`/dashboard/`)는 초기 프로토타입이며, 현재는 아카이브되었습니다.

---

## 🎯 프로덕션 버전 사용하기

### 위치
```
/home/won/projects/dreamseed_monorepo/portal_front/dashboard/
```

### 주요 파일
- **`app_teacher.R`**: 메인 Shiny 대시보드 (v2.0, 998줄)
- **`config/assignment_templates.yaml`**: 과제 템플릿 및 권한 설정
- **`QUICKSTART_v2.md`**: 5분 빠른 시작 가이드 ⭐
- **`ENHANCEMENTS_v2.md`**: 상세 기술 문서
- **`README_teacher.md`**: 사용자 가이드

### 빠른 시작

```bash
# 1. 프로덕션 디렉토리로 이동
cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard

# 2. 퀵스타트 가이드 읽기 (5분)
cat QUICKSTART_v2.md

# 3. 대시보드 실행
DEV_USER=teacher01 DEV_ORG_ID=org_001 DEV_ROLES=teacher \
Rscript -e 'shiny::runApp("app_teacher.R", host="0.0.0.0", port=8081)'

# 4. 브라우저 접속
# http://localhost:8081
```

---

## 🆕 v2.0 주요 기능 (2025-11-06)

### 1️⃣ 개별 학생 즉시 과제 배정
- 학생 테이블에서 "과제 배정" 버튼 클릭
- θ 수준에 맞는 과제 자동 선택
- 성공/실패 알림 즉시 표시

### 2️⃣ 출석 요일별 분산 분석
- `abs_variance`: 요일별 결석률 분산
- `worst_day`: 결석이 가장 많은 요일
- 특정 요일 결석 패턴 파악 (예: 매주 금요일 40% 결석)

### 3️⃣ 문항 반응 이상 모달 (빠른 접근)
- Pure Guessing, Strategic Omit, Rapid-Fire, 복합 패턴
- 버튼 클릭 → 해당 패턴 학생 목록 모달
- 정렬 가능, 즉시 개입 가능

### 4️⃣ YAML 핫리로드 (재시작 불필요)
- 30초마다 설정 파일 변경 자동 감지
- 제로 다운타임 설정 업데이트
- 템플릿/권한 즉시 반영

---

## 📚 상세 문서

### 필수 읽기 (우선순위 순)

1. **[QUICKSTART_v2.md](../portal_front/dashboard/QUICKSTART_v2.md)** ⭐
   - 5분 안에 v2.0 기능 파악
   - 즉시 테스트 방법 포함

2. **[ENHANCEMENTS_v2.md](../portal_front/dashboard/ENHANCEMENTS_v2.md)**
   - 4가지 신규 기능 상세 구현
   - 코드 예시, 알고리즘, 트러블슈팅

3. **[README_teacher.md](../portal_front/dashboard/README_teacher.md)**
   - 교사용 사용 가이드
   - 워크플로우 및 활용 예시

4. **[INTEGRATION_GUIDE.md](../portal_front/dashboard/INTEGRATION_GUIDE.md)**
   - YAML 설정 통합 가이드
   - IdP/프록시 헤더 매핑

---

## 🔧 환경 설정

### 필수 R 패키지

```r
install.packages(c(
  "shiny",
  "shinydashboard",
  "DT",
  "arrow",
  "dplyr",
  "plotly",
  "lubridate",
  "stringr",
  "tidyr",
  "tibble",
  "httr",
  "yaml"
))
```

### 환경 변수

```bash
# 개발 모드 (프록시 없이)
export DEV_USER=teacher01
export DEV_ORG_ID=org_001
export DEV_ROLES=teacher

# 리스크 임계값 (선택)
export RISK_THETA_DELTA=0.02      # 주간 성장률 임계
export RISK_ATTENDANCE=0.25       # 출석 불규칙 임계
export RISK_GUESS=0.15            # 추측 패턴 임계
export RISK_OMIT=0.12             # 무응답 임계

# 과제 배정 API
export ASSIGNMENT_API_URL=http://localhost:8000/api/assignments
export ASSIGNMENT_API_BEARER="Bearer <token>"  # 선택
```

---

## 📊 기능 비교

| 기능 | v1.0 (프로토타입) | v2.0 (프로덕션) |
|------|------------------|----------------|
| 클래스 스냅샷 | ✅ | ✅ |
| 리스크 알림 | ✅ | ✅ |
| θ 히스토그램 | ✅ | ✅ |
| 학생 드릴다운 | ✅ | ✅ |
| 버킷별 CTA | ❌ | ✅ |
| 개별 학생 배정 | ❌ | ✅ |
| 요일별 분산 분석 | ❌ | ✅ |
| 이상 패턴 모달 | ❌ | ✅ |
| YAML 핫리로드 | ❌ | ✅ |
| IdP 통합 | ❌ | ✅ |
| 역할 정규화 | ❌ | ✅ |
| 권한 관리 | ❌ | ✅ |

---

## 🗂️ 아카이브

v1.0 프로토타입 파일은 `_archive_v1_prototype/` 디렉토리에 보관되어 있습니다:

```
dashboard/_archive_v1_prototype/
├── app_teacher.R (614줄, 기본 기능만)
├── bootstrap_data.R (샘플 데이터 생성)
├── run_teacher_dashboard.sh (실행 스크립트)
└── README_v1.md (프로토타입 문서)
```

---

## 🚀 다음 단계

1. **프로덕션 버전 실행**
   ```bash
   cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard
   cat QUICKSTART_v2.md  # 5분 가이드
   ```

2. **설정 커스터마이징**
   ```bash
   vim config/assignment_templates.yaml
   # 템플릿, 권한, IdP 매핑 수정
   ```

3. **실제 데이터 연동**
   - `DATASET_ROOT` 환경변수로 실제 데이터 경로 지정
   - Arrow Parquet 파티션 구조 확인

4. **프로덕션 배포**
   - systemd 서비스 설정
   - 역프록시 헤더 매핑
   - 모니터링 및 로깅 설정

---

## 📞 문의

- **기술 지원**: DreamSeed AI 팀
- **문서 위치**: `/portal_front/dashboard/`
- **버전**: v2.0 (2025-11-06)

---

**⚡ 프로덕션 준비 완료 | 제로 다운타임 | 1분 의사결정**
