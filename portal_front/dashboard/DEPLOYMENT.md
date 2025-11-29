# 교사용 대시보드 배포 가이드

## 🎯 빠른 시작 (개발 환경)

### 1단계: 의존성 설치

```r
# R 콘솔에서 실행
install.packages(c(
  "shiny", "shinydashboard", "DT", "arrow", "dplyr",
  "plotly", "lubridate", "stringr", "tidyr", "tibble",
  "httr", "yaml"
))
```

### 2단계: 대시보드 실행

```bash
cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard

# 실행 스크립트 사용 (권장)
./run_dashboard.sh

# 또는 직접 실행
DEV_USER=teacher01 DEV_ORG_ID=org_001 DEV_ROLES=teacher \
Rscript -e 'shiny::runApp("app_teacher.R", host="0.0.0.0", port=8081)'
```

### 3단계: 브라우저 접속

```
http://localhost:8081
```

---

## 🔧 프로덕션 배포

### systemd 서비스 설정

```bash
# 1. 서비스 파일 생성
sudo vim /etc/systemd/system/teacher-dashboard.service
```

```ini
[Unit]
Description=Teacher Dashboard (Shiny)
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/home/won/projects/dreamseed_monorepo/portal_front/dashboard
Environment="DATASET_ROOT=/data/irt/datasets"
Environment="RISK_THETA_DELTA=0.02"
Environment="RISK_ATTENDANCE=0.25"
Environment="RISK_GUESS=0.15"
Environment="RISK_OMIT=0.12"
Environment="ASSIGNMENT_API_URL=http://localhost:8000/api/assignments"
ExecStart=/usr/bin/Rscript -e "shiny::runApp('app_teacher.R', host='127.0.0.1', port=8081)"
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 2. 서비스 활성화 및 시작
sudo systemctl daemon-reload
sudo systemctl enable teacher-dashboard
sudo systemctl start teacher-dashboard

# 3. 상태 확인
sudo systemctl status teacher-dashboard

# 4. 로그 확인
sudo journalctl -u teacher-dashboard -f
```

### Nginx 역프록시 설정

```nginx
# /etc/nginx/sites-available/teacher-dashboard
server {
    listen 443 ssl http2;
    server_name dashboard.dreamseed.ai;

    ssl_certificate /etc/letsencrypt/live/dashboard.dreamseed.ai/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard.dreamseed.ai/privkey.pem;

    # IdP 인증 헤더 주입 (Keycloak/Auth0 등)
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 인증 헤더 (IdP에서 검증 후 주입)
        proxy_set_header X-User $http_x_auth_request_user;
        proxy_set_header X-Org-Id $http_x_auth_request_org_id;
        proxy_set_header X-Roles $http_x_auth_request_groups;
        proxy_set_header Authorization $http_authorization;

        # WebSocket 지원 (Shiny reactivity)
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
}
```

```bash
# Nginx 설정 활성화
sudo ln -s /etc/nginx/sites-available/teacher-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 🔐 IdP 통합

### Keycloak 예시

```yaml
# config/assignment_templates.yaml
idp_header_mappings:
  keycloak:
    user: "X-Auth-Request-User"
    org: "X-Auth-Request-Org-Id"
    roles: "X-Auth-Request-Groups"

role_mappings:
  admin:
    - "admin"
    - "principal"
  teacher:
    - "teacher"
    - "instructor"
  viewer:
    - "viewer"
    - "analyst"
```

### 환경변수 설정

```bash
# systemd 서비스 파일에 추가
Environment="AUTH_HEADER_USER=X-Auth-Request-User"
Environment="AUTH_HEADER_ORG=X-Auth-Request-Org-Id"
Environment="AUTH_HEADER_ROLES=X-Auth-Request-Groups"
```

---

## 📊 데이터 연동

### Arrow Parquet 데이터 구조

```
/data/irt/datasets/
├── classes.parquet
├── students.parquet
├── student_theta/
│   ├── org_id=org_001/
│   │   ├── class_id=class_01/
│   │   │   └── part-0.parquet
│   │   └── class_id=class_02/
│   │       └── part-0.parquet
│   └── org_id=org_002/
│       └── ...
├── attendance/
│   └── (동일 파티션 구조)
├── skill_weakness.parquet
└── response_stats.parquet
```

### 데이터 생성 (개발/테스트)

```bash
# 샘플 데이터 생성 스크립트 실행
cd /home/won/projects/dreamseed_monorepo/dashboard/_archive_v1_prototype
Rscript bootstrap_data.R

# 생성된 데이터 확인
ls -lh /home/won/projects/dreamseed_monorepo/data/datasets/
```

---

## 🔍 모니터링 및 로깅

### 로그 수집

```bash
# systemd 로그
sudo journalctl -u teacher-dashboard -f --since "1 hour ago"

# 애플리케이션 로그 (파일로 저장)
# systemd 서비스 파일에 추가:
StandardOutput=append:/var/log/teacher-dashboard/app.log
StandardError=append:/var/log/teacher-dashboard/error.log
```

### 성능 모니터링

```bash
# R 프로세스 리소스 사용량
ps aux | grep "app_teacher.R"

# 메모리 사용량
free -h

# Arrow 데이터셋 크기
du -sh /data/irt/datasets/
```

---

## 🔄 설정 업데이트 (핫리로드)

### 실시간 설정 변경

```bash
# 1. 설정 파일 수정
vim /home/won/projects/dreamseed_monorepo/portal_front/dashboard/config/assignment_templates.yaml

# 2. 변경 예시: 템플릿 ID 수정
templates:
  very_low:
    id: "new_remedial_v2"  # 변경

# 3. 저장 후 30초 이내 자동 반영
# 대시보드 재시작 불필요!

# 4. 브라우저에서 알림 확인
# "⚡ 설정 파일이 업데이트되었습니다"
```

### 수동 재시작 (필요시)

```bash
sudo systemctl restart teacher-dashboard
```

---

## 🧪 테스트

### 기능 테스트 체크리스트

```bash
# 1. 개별 학생 과제 배정
# - 학생 테이블에서 "과제 배정" 버튼 클릭
# - 알림 확인: "✓ [학생명] 학생에게 '[template_id]' 과제를 배정했습니다."

# 2. 요일별 분산 분석
# - abs_variance 컬럼 확인 (> 0.05인 학생 찾기)
# - worst_day 확인 (예: "Fri")

# 3. 이상 패턴 모달
# - "Pure Guessing 학생 보기" 버튼 클릭
# - 모달에서 학생 목록 확인
# - guess_rate로 정렬

# 4. 핫리로드
# - config/assignment_templates.yaml 수정
# - 30초 대기
# - 알림 확인: "⚡ 설정 파일이 업데이트되었습니다"
```

### API 연동 테스트

```bash
# 과제 배정 API 모의 서버 (개발용)
# Python Flask 예시
cat > /tmp/mock_assignment_api.py << 'EOF'
from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/api/assignments', methods=['POST'])
def assign():
    data = request.json
    print(f"Received assignment: {data}")
    return jsonify({"status": "success", "assignment_id": "A12345"})

if __name__ == '__main__':
    app.run(port=8000)
EOF

python3 /tmp/mock_assignment_api.py
```

---

## 🐛 트러블슈팅

### 문제: 대시보드가 시작되지 않음

```bash
# 1. R 패키지 확인
Rscript -e 'library(shiny); library(arrow); library(yaml)'

# 2. 포트 충돌 확인
sudo lsof -i :8081

# 3. 로그 확인
sudo journalctl -u teacher-dashboard -n 50
```

### 문제: 데이터가 로드되지 않음

```bash
# 1. 데이터 경로 확인
ls -lh $DATASET_ROOT

# 2. Arrow 데이터셋 읽기 테스트
Rscript -e "
library(arrow)
ds <- open_dataset('$DATASET_ROOT/student_theta')
print(ds %>% head())
"

# 3. 권한 확인
sudo chown -R www-data:www-data $DATASET_ROOT
```

### 문제: 핫리로드가 작동하지 않음

```bash
# 1. 파일 권한 확인
ls -l config/assignment_templates.yaml

# 2. 파일 수정 시간 강제 업데이트
touch config/assignment_templates.yaml

# 3. 로그에서 reload 메시지 확인
sudo journalctl -u teacher-dashboard -f | grep "hot-reload"
```

---

## 📚 추가 문서

- **[QUICKSTART_v2.md](./QUICKSTART_v2.md)**: 5분 빠른 시작
- **[ENHANCEMENTS_v2.md](./ENHANCEMENTS_v2.md)**: v2.0 기능 상세
- **[README_teacher.md](./README_teacher.md)**: 사용자 가이드
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)**: YAML 설정 가이드

---

## 🔒 보안 고려사항

### 1. 인증 및 권한

- IdP/SSO를 통한 인증 필수
- 역프록시에서 헤더 검증 후 주입
- 역할 기반 접근 제어 (RBAC)

### 2. 데이터 보호

- 학생 개인정보 암호화 저장
- HTTPS 필수 (Let's Encrypt)
- 데이터 접근 로그 기록

### 3. API 보안

- Bearer 토큰 인증
- Rate limiting
- CORS 정책 설정

---

**Version**: 2.0  
**Last Updated**: 2025-11-06  
**Maintainer**: DreamseedAI Engineering Team
