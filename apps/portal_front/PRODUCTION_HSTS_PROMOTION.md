# Production HSTS Promotion Pack

## 🚀 프로덕션 HSTS 점진적 활성화 가이드

### 1. Pre-checks (프로덕션)
```bash
# 도메인/정적 경로/API 업스트림 확인
DOMAIN=dreamseedai.com
STATIC_ROOT=/srv/portal_front/current
API_UPSTREAM=http://127.0.0.1:8000/

# Nginx 문법 체크 (현재 설정)
sudo nginx -t

# 건강 상태
curl -skI https://$DOMAIN | head -n1
curl -sk https://$DOMAIN/healthz | head -n1 || true
```

### 2. HSTS 1단계 — Short max-age ("on"으로 배포)
```bash
# 배포 (HSTS=on)
sudo ops/scripts/deploy_proxy_and_tls.sh $DOMAIN $STATIC_ROOT $API_UPSTREAM on

# 즉시 헬스체크
curl -skI https://$DOMAIN | grep -i '^strict-transport-security' || echo "(HSTS header missing)"
```

**옵션(권장)**: 단기 HSTS 헤더를 적용하고 싶다면 템플릿에서 다음과 같이 교체 후 배포:
```nginx
# Strict-Transport-Security: short stage
add_header Strict-Transport-Security "max-age=86400" always;  # 1 day
```

### 3. 브라우저 레벨 검증 (Playwright: prod)
```bash
cd webtests && npm ci
TARGET_URL=https://$DOMAIN ENV=prod npm test
```

**기대**: 테스트 통과, 특히 security headers 테스트에서 HSTS 존재 단언 성공.
콘솔 에러 제로, 혼합 콘텐츠 없음.

### 4. 모니터링 윈도우 (24–48h)
- 에러 비율(5xx), 응답 시간, 콘솔 에러/JS 오류, 사용자 제보 모니터링
- 인증서 만료 경보/업타임 체크 정상 동작 확인

### 5. HSTS 2단계 — 장기 max-age
안정화 확인 후 max-age를 수 주 → 1년(31536000)으로 상향.

하위 도메인까지 보장하려면 includeSubDomains 추가(도메인 체계 중복 확인 필요).

```nginx
# Strict-Transport-Security: long stage
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

배포 후 반복 검증:
```bash
sudo nginx -t && sudo systemctl reload nginx
curl -skI https://$DOMAIN | grep -i strict-transport-security
cd webtests && TARGET_URL=https://$DOMAIN ENV=prod npm test
```

### 6. (선택) HSTS Preload 등록 가이드
**매우 신중**: 되돌리기 어렵습니다.

요건: max-age>=31536000; includeSubDomains; preload 필요 + 전체 서브도메인 HTTPS 보장.

템플릿 헤더 예시:
```nginx
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

이후 https://hstspreload.org 제출 → 승인 모니터링.

### 7. Cloud/CDN 사용 시 주의
- Cloudflare/ELB 등에서 HSTS가 중복/무시될 수 있음 → 한 곳에서만 관리
- 프록시가 TLS 종료를 담당하면 원 서버 대신 프록시에서 HSTS 설정 필요

### 8. 롤백 절차 (Prod)
```bash
# 직전 백업 conf로 복원 → nginx -t && reload
OUT=/etc/nginx/sites-available/${DOMAIN}.conf
LATEST=$(ls -1t ${OUT}.bak.* | head -n1)
sudo cp -af "$LATEST" "$OUT"
sudo nginx -t && sudo systemctl reload nginx
```

긴급 회피: 임시로 HSTS 제거 배포(헤더 제거) → 캐시/브라우저 정책 영향은 단기 max-age였을 때 완화가 빠름.

### 9. 최종 승인 기준 (Prod)
- nginx -t OK, HTTP→HTTPS 301 정상
- HSTS 헤더 존재(장기 max-age), 콘솔 에러 0, 혼합 콘텐츠 0
- /healthz 200, 업스트림 오류율 정상 범위
- Playwright(prod) 통과, CI 아티팩트 업로드

### 10. 실행 요약 (복붙용)
```bash
DOMAIN=dreamseedai.com
STATIC_ROOT=/srv/portal_front/current
API_UPSTREAM=http://127.0.0.1:8000/

# Step 1: enable HSTS (short or long per 정책)
sudo ops/scripts/deploy_proxy_and_tls.sh $DOMAIN $STATIC_ROOT $API_UPSTREAM on

# Step 2: verify
curl -skI https://$DOMAIN | grep -i strict-transport-security
cd webtests && npm ci && TARGET_URL=https://$DOMAIN ENV=prod npm test

# Step 3: monitor 24–48h → if stable, bump to long max-age & (option) includeSubDomains
# (edit template header)
sudo nginx -t && sudo systemctl reload nginx

# Step 4: (optional) preload after full subdomain HTTPS readiness
```
