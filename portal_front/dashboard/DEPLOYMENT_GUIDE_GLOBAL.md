# DreamseedAI 글로벌 Teacher Dashboard 배포 가이드

**버전**: 2.0 (글로벌 확장)  
**작성일**: 2025-11-06  
**대상**: 운영팀, DevOps, SRE  
**목적**: 다국가/다과목/다학년 지원 Teacher Dashboard 프로덕션 배포

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [데이터베이스 마이그레이션](#데이터베이스-마이그레이션)
3. [YAML 설정 파일 배포](#yaml-설정-파일-배포)
4. [환경 변수 설정](#환경-변수-설정)
5. [R 헬퍼 함수 배포](#r-헬퍼-함수-배포)
6. [애플리케이션 배포](#애플리케이션-배포)
7. [검증 및 테스트](#검증-및-테스트)
8. [모니터링 및 알람](#모니터링-및-알람)
9. [트러블슈팅](#트러블슈팅)
10. [롤백 절차](#롤백-절차)

---

## 사전 요구사항

### 소프트웨어 버전
- **PostgreSQL**: 14+ (JSONB, Array 지원 필요)
- **R**: 4.2+ (arrow, dplyr, shiny 최신 버전)
- **Shiny Server**: 1.5.20+
- **Apache Arrow**: 12.0+

### 필수 R 패키지
```r
install.packages(c(
  "shiny", "shinydashboard", "DT", 
  "arrow", "dplyr", "plotly", 
  "lubridate", "stringr", "tidyr", 
  "tibble", "httr", "yaml"
))
```

### 파일 권한
```bash
# 작업 디렉토리
sudo mkdir -p /srv/shiny-server/teacher_dashboard_global
sudo chown -R shiny:shiny /srv/shiny-server/teacher_dashboard_global

# 로그 디렉토리
sudo mkdir -p /var/log/shiny-server/teacher_dashboard
sudo chown -R shiny:shiny /var/log/shiny-server/teacher_dashboard
```

### 데이터베이스 접속 권한
- READ 권한: `students`, `classes`, `student_theta`, `attendance`, `skill_weakness`, `response_stats`, `item_response_patterns`
- WRITE 권한: `schema_migrations` (마이그레이션 기록용)
- CREATE TABLE 권한: `subjects_master`, `organizations` (신규 테이블)

---

## 데이터베이스 마이그레이션

### 1단계: 백업

```bash
# 프로덕션 DB 백업 (필수!)
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME -F c -b -v \
  -f backup_before_global_migration_$(date +%Y%m%d_%H%M%S).dump
  
# 백업 파일 검증
ls -lh backup_before_global_migration_*.dump
```

### 2단계: 마이그레이션 실행

```bash
# 마이그레이션 스크립트 실행
psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -f migrations/001_global_schema.sql \
  -v ON_ERROR_STOP=1 \
  --echo-all \
  --set=sslmode=require

# 결과 확인
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c \
  "SELECT version, description, applied_at FROM schema_migrations ORDER BY applied_at DESC LIMIT 5;"
```

**예상 출력**:
```
 version |                 description                  |       applied_at        
---------+----------------------------------------------+-------------------------
 001     | Global expansion schema: countries, subjects | 2025-11-06 10:30:45.123
```

### 3단계: 데이터 검증

```sql
-- 새 테이블 생성 확인
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('subjects_master', 'organizations');

-- 새 컬럼 추가 확인
SELECT column_name, data_type, column_default
FROM information_schema.columns
WHERE table_name = 'students'
  AND column_name IN ('country', 'grade', 'education_type', 'language');

-- 초기 데이터 확인
SELECT subject_code, subject_name_en, category, min_grade, max_grade
FROM subjects_master
WHERE is_active = TRUE
ORDER BY category, subject_code;

-- 결과: 20개 과목 (Math 6개, Physics 4개, Chemistry 3개, Biology 4개 등)
```

### 4단계: 기존 데이터 마이그레이션 (필요시)

```sql
-- 기존 students 테이블에 기본값 설정
UPDATE students 
SET country = 'USA',
    grade = 'G9',
    grade_system = 'US',
    language = 'en-US',
    timezone = 'America/Los_Angeles',
    education_type = 'tutoring',
    group_size = 1,
    is_active = TRUE
WHERE country IS NULL;

-- 기존 classes 테이블에 기본값 설정
UPDATE classes 
SET subject = 'math',
    subject_code = 'MATH-ALG2',
    country = 'USA',
    grade = 'G9',
    curriculum = 'US-Common-Core',
    education_type = 'tutoring',
    is_active = TRUE
WHERE country IS NULL;

-- 영향 받은 행 수 확인
SELECT 
  (SELECT COUNT(*) FROM students WHERE country = 'USA') AS students_migrated,
  (SELECT COUNT(*) FROM classes WHERE country = 'USA') AS classes_migrated;
```

---

## YAML 설정 파일 배포

### 1단계: 설정 파일 복사

```bash
# YAML 파일을 서버로 복사
scp config/assignment_templates_global.yaml \
    $SERVER_USER@$SERVER_HOST:/srv/shiny-server/teacher_dashboard_global/config/

# 파일 권한 설정
ssh $SERVER_USER@$SERVER_HOST "sudo chown shiny:shiny /srv/shiny-server/teacher_dashboard_global/config/assignment_templates_global.yaml"
ssh $SERVER_USER@$SERVER_HOST "sudo chmod 644 /srv/shiny-server/teacher_dashboard_global/config/assignment_templates_global.yaml"
```

### 2단계: YAML 유효성 검증

```bash
# R에서 YAML 로드 테스트
ssh $SERVER_USER@$SERVER_HOST "Rscript -e \"
library(yaml)
config <- yaml.load_file('/srv/shiny-server/teacher_dashboard_global/config/assignment_templates_global.yaml')
cat('✓ YAML loaded successfully\\\\n')
cat('Supported countries:', paste(names(config\\$templates), collapse=', '), '\\\\n')
cat('Total subjects (USA):', length(config\\$templates\\$USA), '\\\\n')
\""
```

**예상 출력**:
```
✓ YAML loaded successfully
Supported countries: USA, CAN
Total subjects (USA): 4
```

### 3단계: 핫 리로드 설정 확인

```bash
# 30초마다 YAML 변경 감지하는지 확인
tail -f /var/log/shiny-server/teacher_dashboard/app.log | grep "config_reload"
```

---

## 환경 변수 설정

### 1단계: 환경 변수 파일 생성

```bash
# /etc/shiny-server/teacher_dashboard_global.env 파일 생성
sudo tee /etc/shiny-server/teacher_dashboard_global.env > /dev/null <<EOF
# Database connection
DB_HOST=your-prod-db-host.rds.amazonaws.com
DB_PORT=5432
DB_NAME=dreamseed_prod
DB_USER=shiny_app_user
DB_PASSWORD=REDACTED

# Arrow dataset path
ARROW_BASE_PATH=/mnt/data/arrow_datasets

# Assignment API
ASSIGNMENT_API_URL=https://api.dreamseedai.com/v1/assignments

# Risk thresholds (can override YAML defaults)
RISK_THETA_DELTA=0.05
RISK_ATTEND_ABS=0.10
RISK_ATTEND_TARDY=0.15
RISK_ATTEND_VAR_TOP_PCT=0.80
RISK_RESP_GUESS_TOP_PCT=0.80
RISK_RESP_OMIT=0.08

# Performance tuning
ARROW_USE_THREADS=TRUE
SHINY_MAX_UPLOADS=10485760
SHINY_SANITIZE_ERRORS=FALSE

# CDN / Data server (multi-region)
DATA_SERVER_USA=https://us-data.dreamseedai.com
DATA_SERVER_CAN=https://ca-data.dreamseedai.com
DATA_SERVER_KOR=https://kr-data.dreamseedai.com
EOF

# 파일 권한 설정 (보안)
sudo chmod 600 /etc/shiny-server/teacher_dashboard_global.env
sudo chown root:root /etc/shiny-server/teacher_dashboard_global.env
```

### 2단계: Shiny Server 설정 업데이트

```bash
# /etc/shiny-server/shiny-server.conf 수정
sudo tee -a /etc/shiny-server/shiny-server.conf > /dev/null <<EOF

# Teacher Dashboard (Global Edition)
location /teacher_dashboard_global {
  app_dir /srv/shiny-server/teacher_dashboard_global;
  log_dir /var/log/shiny-server/teacher_dashboard;
  
  # Environment variables
  env_file /etc/shiny-server/teacher_dashboard_global.env;
  
  # Performance settings
  app_idle_timeout 600;
  app_init_timeout 120;
  
  # Access control (integrate with nginx reverse proxy)
  required_user teacher;
  required_group dreamseed_users;
}
EOF
```

### 3단계: Shiny Server 재시작

```bash
# 설정 검증
sudo shiny-server --config /etc/shiny-server/shiny-server.conf --test

# 서비스 재시작
sudo systemctl restart shiny-server

# 상태 확인
sudo systemctl status shiny-server
```

---

## R 헬퍼 함수 배포

### 1단계: 파일 복사

```bash
# helpers_global.R 복사
scp helpers_global.R \
    $SERVER_USER@$SERVER_HOST:/srv/shiny-server/teacher_dashboard_global/

# 권한 설정
ssh $SERVER_USER@$SERVER_HOST "sudo chown shiny:shiny /srv/shiny-server/teacher_dashboard_global/helpers_global.R"
ssh $SERVER_USER@$SERVER_HOST "sudo chmod 644 /srv/shiny-server/teacher_dashboard_global/helpers_global.R"
```

### 2단계: 함수 유효성 검증

```bash
# R에서 로드 테스트
ssh $SERVER_USER@$SERVER_HOST "Rscript -e \"
source('/srv/shiny-server/teacher_dashboard_global/helpers_global.R')
cat('✓ helpers_global.R loaded successfully\\\\n')

# Test get_template function
library(yaml)
config <- yaml.load_file('/srv/shiny-server/teacher_dashboard_global/config/assignment_templates_global.yaml')
template <- get_template(config, 'USA', 'math', 'G9', 'algebra2', 'very_low')
cat('Template ID:', template\\$template_id, '\\\\n')
cat('Catalog IDs:', paste(template\\$catalog_ids, collapse=', '), '\\\\n')
\""
```

**예상 출력**:
```
✓ helpers_global.R loaded successfully
[get_template] ✓ Found: USA.math.G9.algebra2.very_low
Template ID: US-MATH-ALG2-G9-REMEDIAL
Catalog IDs: MATH-ALG2-BASICS-001, MATH-ALG2-BASICS-002, MATH-ALG2-REVIEW-001
```

---

## 애플리케이션 배포

### 1단계: 앱 파일 복사

```bash
# app_teacher.R 복사
scp app_teacher.R \
    $SERVER_USER@$SERVER_HOST:/srv/shiny-server/teacher_dashboard_global/

# 권한 설정
ssh $SERVER_USER@$SERVER_HOST "sudo chown -R shiny:shiny /srv/shiny-server/teacher_dashboard_global/"
```

### 2단계: 의존성 확인

```bash
# R 패키지 버전 확인
ssh $SERVER_USER@$SERVER_HOST "Rscript -e \"
installed_pkgs <- installed.packages()[, c('Package', 'Version')]
required_pkgs <- c('shiny', 'shinydashboard', 'DT', 'arrow', 'dplyr', 'plotly', 'lubridate', 'yaml')
for (pkg in required_pkgs) {
  version <- installed_pkgs[installed_pkgs[,'Package'] == pkg, 'Version']
  cat(sprintf('%-20s %s\\\\n', pkg, ifelse(length(version) > 0, version, '❌ NOT INSTALLED')))
}
\""
```

### 3단계: 앱 시작

```bash
# Shiny Server 재시작
ssh $SERVER_USER@$SERVER_HOST "sudo systemctl restart shiny-server"

# 로그 확인 (에러 없는지)
ssh $SERVER_USER@$SERVER_HOST "tail -n 50 /var/log/shiny-server/teacher_dashboard/app.log"
```

### 4단계: 브라우저 접속 테스트

```bash
# 로컬에서 curl 테스트
curl -I https://your-domain.com/teacher_dashboard_global/

# 예상 응답: HTTP/2 200
```

---

## 검증 및 테스트

### 기능 테스트 체크리스트

#### 1. YAML 설정 로드
- [ ] USA/CAN 템플릿 정상 로드
- [ ] 다국어 메시지 (en-US, ko-KR) 정상 로드
- [ ] 국가별 기본 설정 정상 로드
- [ ] 핫 리로드 (30초마다) 작동

#### 2. 서브그룹 분위수 계산
- [ ] country/subject/grade 필터링 정상
- [ ] 데이터 부족 시 fallback 정상 (subject → country → all)
- [ ] 분위수 컷오프 계산 정상 (80th percentile)
- [ ] 로그에 서브그룹 정보 출력

**검증 쿼리**:
```sql
-- 서브그룹 데이터 확인
SELECT country, subject, grade, COUNT(*) AS student_count
FROM students
WHERE is_active = TRUE
GROUP BY country, subject, grade
ORDER BY country, subject, grade;

-- 결과 예시:
-- USA | math | G9 | 150
-- USA | math | G10 | 130
-- USA | physics | G10 | 80
-- CAN | math | G9 | 45
```

#### 3. 개별 학생 배정
- [ ] 학생 메타 조회 (country, grade) 정상
- [ ] 클래스 메타 조회 (subject, subject_level) 정상
- [ ] `get_template()` 계층적 검색 정상
- [ ] 다국어 성공/실패 메시지 정상
- [ ] API 호출 성공 (201 응답)

**수동 테스트**:
1. 대시보드 접속 → 클래스 선택
2. 학생 테이블에서 "배정" 버튼 클릭
3. 로그 확인:
   ```
   [get_template] ✓ Found: USA.math.G9.algebra2.very_low
   [assignment API] success: 1 students, template=US-MATH-ALG2-G9-REMEDIAL
   ```

#### 4. 프라이버시 필터
- [ ] GDPR 국가 (GBR) → 이름 익명화
- [ ] COPPA (USA, 13세 미만) → 필터링
- [ ] FERPA (공교육 교사) → 외부 기록 제한
- [ ] PIPA (KOR) → ID 마스킹

**검증 스크립트** (R):
```r
# helpers_global.R 테스트
source("helpers_global.R")
config <- yaml::yaml.load_file("config/assignment_templates_global.yaml")

# 테스트 데이터
test_data <- data.frame(
  student_id = c("STU-12345", "STU-67890"),
  student_name = c("John Doe", "Jane Smith"),
  country = c("GBR", "USA"),
  date_of_birth = as.Date(c("2010-01-01", "2015-05-15")),
  parental_consent = c(TRUE, FALSE)
)

# GDPR 테스트 (영국)
filtered_gdpr <- privacy_filter(test_data[1,], "GBR", "academy", "teacher", config)
print(filtered_gdpr$student_name)  # 예상: "J***"

# COPPA 테스트 (미국 13세 미만)
filtered_coppa <- privacy_filter(test_data[2,], "USA", "tutoring", "teacher", config)
print(nrow(filtered_coppa))  # 예상: 0 (필터링됨)
```

#### 5. 성능 테스트
- [ ] 10,000 학생 × 28일 데이터 로드 < 2초
- [ ] 서브그룹 분위수 계산 < 1초
- [ ] 메모리 사용량 < 2GB (per session)
- [ ] 동시 접속 50명 처리 가능

**부하 테스트** (Apache Bench):
```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 -H "Cookie: shiny-session-id=..." \
   https://your-domain.com/teacher_dashboard_global/
```

---

## 모니터링 및 알람

### 1. 로그 모니터링

```bash
# 실시간 로그 확인
tail -f /var/log/shiny-server/teacher_dashboard/app.log | grep -E "ERROR|WARNING|✓|✗"

# 주요 로그 패턴:
# - [load_config] Successfully loaded GLOBAL config from: ...
# - [attn_var_cutoff] ✓ Subgroup (USA.math.G9): N=150, cutoff=0.0234
# - [get_template] ✓ Found: USA.math.G9.algebra2.very_low
# - [assignment API] success: 5 students, template=...
```

### 2. CloudWatch 메트릭 (AWS 환경)

```yaml
# cloudwatch-agent-config.json
{
  "metrics": {
    "namespace": "DreamseedAI/TeacherDashboard",
    "metrics_collected": {
      "statsd": {
        "service_address": ":8125",
        "metrics_collection_interval": 60,
        "metrics_aggregation_interval": 60
      }
    },
    "dimensions": {
      "environment": ["production"],
      "country": ["USA", "CAN", "KOR"]
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/shiny-server/teacher_dashboard/app.log",
            "log_group_name": "/aws/ec2/shiny-server/teacher_dashboard",
            "log_stream_name": "{instance_id}/app.log",
            "retention_in_days": 30
          }
        ]
      }
    }
  }
}
```

### 3. 알람 설정

**CloudWatch Alarms** (참고용):
```yaml
alarms:
  - name: TeacherDashboard_HighErrorRate
    metric: Errors
    threshold: 10  # 1분당 10개 이상
    evaluation_periods: 2
    action: SNS:alert-ops-team
  
  - name: TeacherDashboard_SlowResponse
    metric: ResponseTime
    threshold: 5000  # 5초 이상
    evaluation_periods: 3
    action: SNS:alert-ops-team
  
  - name: TeacherDashboard_MemoryUsage
    metric: MemoryUtilization
    threshold: 85  # 85% 이상
    evaluation_periods: 2
    action: SNS:alert-ops-team
```

---

## 트러블슈팅

### 문제 1: YAML 로드 실패

**증상**:
```
[load_config] Failed to load YAML: could not find function "yaml.load_file"
```

**원인**: yaml 패키지 미설치

**해결**:
```bash
ssh $SERVER_USER@$SERVER_HOST "sudo Rscript -e \"install.packages('yaml', repos='https://cran.rstudio.com/')\""
```

---

### 문제 2: 서브그룹 데이터 부족

**증상**:
```
[collect_subgroup] ⚠ Insufficient data even after fallback
```

**원인**: 특정 국가/과목/학년 조합의 학생 수 < 10명

**해결**:
1. 최소 요구사항 확인:
   ```sql
   SELECT country, subject, grade, COUNT(*) 
   FROM students 
   WHERE is_active = TRUE 
   GROUP BY country, subject, grade 
   HAVING COUNT(*) < 10;
   ```

2. fallback 레벨 조정:
   ```r
   # helpers_global.R 수정
   collect_subgroup_data(..., min_rows = 5)  # 10 → 5로 낮춤
   ```

---

### 문제 3: 템플릿 검색 실패

**증상**:
```
[get_template] ✗ No template found. Using hardcoded default.
```

**원인**: YAML에 해당 country.subject.grade.level.bucket 조합 없음

**디버깅**:
```bash
# YAML 구조 확인
Rscript -e "
library(yaml)
config <- yaml.load_file('config/assignment_templates_global.yaml')
cat('USA subjects:', paste(names(config\$templates\$USA), collapse=', '), '\n')
cat('USA.math grades:', paste(names(config\$templates\$USA\$math), collapse=', '), '\n')
cat('USA.math.G9 levels:', paste(names(config\$templates\$USA\$math\$G9), collapse=', '), '\n')
"
```

**해결**:
1. YAML에 누락된 템플릿 추가
2. 또는 fallback 템플릿 확인 (USA.math.G9.mid는 반드시 존재해야 함)

---

### 문제 4: 데이터베이스 연결 타임아웃

**증상**:
```
Error in open_dataset(): could not connect to server: Connection timed out
```

**원인**: 
- DB 방화벽 차단
- 네트워크 지연
- DB 접속 정보 오류

**해결**:
```bash
# 1. 네트워크 테스트
telnet $DB_HOST $DB_PORT

# 2. 환경 변수 확인
cat /etc/shiny-server/teacher_dashboard_global.env | grep DB_

# 3. psql 직접 연결 테스트
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c "SELECT 1;"
```

---

## 롤백 절차

### 긴급 롤백 (< 5분)

```bash
# 1. 이전 버전으로 앱 교체
ssh $SERVER_USER@$SERVER_HOST "
  cd /srv/shiny-server/
  sudo rm -rf teacher_dashboard_global
  sudo cp -r teacher_dashboard_global_backup_20251106 teacher_dashboard_global
  sudo chown -R shiny:shiny teacher_dashboard_global
  sudo systemctl restart shiny-server
"

# 2. 상태 확인
curl -I https://your-domain.com/teacher_dashboard_global/
```

### 데이터베이스 롤백 (복구)

```bash
# 백업 파일에서 복구
pg_restore -h $DB_HOST -U $DB_USER -d $DB_NAME \
  --clean --if-exists \
  -v backup_before_global_migration_20251106_100000.dump
  
# 마이그레이션 기록 삭제
psql -h $DB_HOST -U $DB_USER -d $DB_NAME -c \
  "DELETE FROM schema_migrations WHERE version = '001';"
```

---

## 운영 체크리스트

### 일일 점검 (매일 오전 9시)
- [ ] 로그 확인 (ERROR/WARNING 없는지)
- [ ] 메모리 사용량 < 70%
- [ ] 디스크 사용량 < 80%
- [ ] 응답 시간 < 2초 (평균)

### 주간 점검 (매주 월요일)
- [ ] YAML 설정 백업
- [ ] DB 백업 확인 (자동 백업 성공 여부)
- [ ] 로그 로테이션 확인
- [ ] 패키지 업데이트 확인 (`update.packages()`)

### 월간 점검 (매월 1일)
- [ ] 전체 시스템 성능 분석
- [ ] 데이터 증가 추이 확인 (students, classes 테이블)
- [ ] 템플릿 사용 통계 분석
- [ ] 보안 패치 확인

---

## 부록

### A. 환경별 설정 예시

**개발 환경**:
```bash
DB_HOST=localhost
DB_NAME=dreamseed_dev
ARROW_BASE_PATH=/tmp/arrow_test
RISK_THETA_DELTA=0.10  # 개발에서는 더 관대하게
```

**스테이징 환경**:
```bash
DB_HOST=staging-db.internal.com
DB_NAME=dreamseed_staging
ARROW_BASE_PATH=/mnt/staging_data/arrow
RISK_THETA_DELTA=0.05
```

**프로덕션 환경**:
```bash
DB_HOST=prod-db.rds.amazonaws.com
DB_NAME=dreamseed_prod
ARROW_BASE_PATH=/mnt/prod_data/arrow
RISK_THETA_DELTA=0.05
SHINY_SANITIZE_ERRORS=TRUE  # 보안 강화
```

### B. 참고 자료

- [Shiny Server Admin Guide](https://docs.rstudio.com/shiny-server/)
- [Apache Arrow R Documentation](https://arrow.apache.org/docs/r/)
- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [GDPR Compliance Checklist](https://gdpr.eu/checklist/)

---

**배포 완료 체크리스트**:
- [ ] DB 마이그레이션 성공
- [ ] YAML 설정 파일 배포
- [ ] 환경 변수 설정
- [ ] R 헬퍼 함수 배포
- [ ] 앱 배포 및 시작
- [ ] 기능 테스트 통과
- [ ] 모니터링 설정
- [ ] 운영 팀 인수인계

**배포 승인**: _______________  
**배포 일시**: 2025-11-06 ___:___  
**배포 담당자**: _______________
