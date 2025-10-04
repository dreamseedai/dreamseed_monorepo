# Staging Deployment Guide

## 🚀 스테이징 배포 실행 순서 (요약)

### 1. DNS 설정
```bash
# DNS A staging.dreamseedai.com → server IP
```

### 2. 정적 경로 준비
```bash
sudo mkdir -p /var/www/dreamseed/static
sudo ln -sfn /srv/portal_front/current /var/www/dreamseed/static
sudo chown -R www-data:www-data /var/www/dreamseed
```

### 3. 스테이징 배포 (HSTS OFF)
```bash
sudo ops/scripts/deploy_proxy_and_tls.sh staging.dreamseedai.com /var/www/dreamseed/static http://127.0.0.1:8000/ off
```

### 4. 스테이징 Basic Auth 설정
```bash
sudo ops/scripts/setup_staging_auth.sh
```

### 5. 로그 로테이션 설정
```bash
sudo ops/scripts/setup_log_rotation.sh
```

### 6. 에러 모니터링 설정
```bash
sudo ops/scripts/setup_error_monitoring.sh
```

### 7. 인증서 모니터링 설정
```bash
sudo ops/scripts/setup_cert_monitoring.sh staging.dreamseedai.com
```

### 8. 헬스체크
```bash
curl -skI http://staging.dreamseedai.com | head -n1     # 301
curl -skI https://staging.dreamseedai.com | head -n1    # 200/304
curl -sk https://staging.dreamseedai.com/healthz        # 200
```

### 9. 브라우저 테스트
```bash
cd webtests && npm ci && npm run install:browsers
TARGET_URL=https://staging.dreamseedai.com ENV=staging npm test
```

### 10. 포트 정책 검증
```bash
ops/scripts/ports_policy.sh ops/nginx
sudo nginx -t
```

## 📋 승인 기준 체크리스트

- ✅ **포트 정책**: 차단 포트 없음 확인
- ✅ **Nginx 설정**: 문법 검증 통과
- ✅ **HTTPS 리다이렉트**: HTTP → HTTPS 301 정상
- ✅ **스테이징 보호**: Basic Auth로 외부 접근 차단
- ✅ **HSTS 설정**: 스테이징 OFF, 프로덕션 ON 준비
- ✅ **보안 헤더**: 모든 필수 헤더 포함
- ✅ **롤백 기능**: 배포 실패 시 자동 복구
- ✅ **헬스체크**: 의존성 모니터링 포함
- ✅ **테스트**: 콘솔 에러 및 혼합 콘텐츠 검사
- ✅ **CI/CD**: 아티팩트 업로드 및 포트 정책 검사
- ✅ **모니터링**: 에러 알림 및 인증서 만료 감시
- ✅ **로그 관리**: 로테이션 및 압축 설정

## 🎯 24-48시간 모니터링 후 프로덕션 승급

스테이징에서 안정성 확인 후 `PRODUCTION_HSTS_PROMOTION.md` 가이드에 따라 프로덕션으로 승급하세요.
