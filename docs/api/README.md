# DreamSeed API 문서

## 📖 개요

DreamSeed AI Platform의 RESTful API 문서입니다. 이 문서는 API의 모든 엔드포인트, 요청/응답 형식, 그리고 사용 예제를 포함합니다.

## 🚀 빠른 시작

### 기본 URL
- **프로덕션**: `https://dreamseedai.com`
- **스테이징**: `http://staging.dreamseed.com`
- **로컬 개발**: `http://localhost:8002`

### 인증
현재 API는 공개적으로 접근 가능합니다. 향후 토큰 기반 인증이 추가될 예정입니다.

### 기본 사용법
```bash
# 헬스체크
curl https://dreamseedai.com/healthz

# 대시보드 통계
curl https://dreamseedai.com/api/dashboard/stats

# 사용자 증가 데이터
curl https://dreamseedai.com/api/dashboard/user-growth
```

## 📋 API 엔드포인트

### 1. 헬스체크
- **GET** `/healthz` - 시스템 상태 확인

### 2. 대시보드 데이터
- **GET** `/api/dashboard/stats` - 실시간 통계
- **GET** `/api/dashboard/user-growth` - 사용자 증가 추이
- **GET** `/api/dashboard/daily-activity` - 일일 활동 데이터
- **GET** `/api/dashboard/country-data` - 국가별 사용자 분포
- **GET** `/api/dashboard/recent-activities` - 최근 활동

### 3. 캐시 관리
- **GET** `/api/cache/status` - 캐시 상태 조회
- **POST** `/api/cache/invalidate` - 캐시 무효화

### 4. 모니터링
- **GET** `/metrics` - Prometheus 메트릭

## 📊 응답 형식

### 성공 응답
```json
{
  "status": "success",
  "data": { ... },
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### 오류 응답
```json
{
  "error": "INVALID_REQUEST",
  "message": "잘못된 요청입니다.",
  "details": { ... }
}
```

## 🔧 사용 예제

### JavaScript (Fetch API)
```javascript
// 대시보드 통계 조회
async function getDashboardStats() {
  try {
    const response = await fetch('https://dreamseedai.com/api/dashboard/stats');
    const data = await response.json();
    console.log('통계 데이터:', data);
  } catch (error) {
    console.error('오류:', error);
  }
}

// 국가별 데이터 조회 (필터 적용)
async function getCountryData(userType = 'free', timeFilter = 'realtime') {
  const url = new URL('https://dreamseedai.com/api/dashboard/country-data');
  url.searchParams.append('user_type', userType);
  url.searchParams.append('time_filter', timeFilter);
  
  const response = await fetch(url);
  const data = await response.json();
  return data;
}
```

### Python (requests)
```python
import requests

# 헬스체크
def check_health():
    response = requests.get('https://dreamseedai.com/healthz')
    return response.json()

# 대시보드 통계
def get_stats():
    response = requests.get('https://dreamseedai.com/api/dashboard/stats')
    return response.json()

# 캐시 무효화
def invalidate_cache(pattern):
    response = requests.post(
        'https://dreamseedai.com/api/cache/invalidate',
        json={'pattern': pattern}
    )
    return response.json()
```

### cURL
```bash
# 기본 통계 조회
curl -X GET "https://dreamseedai.com/api/dashboard/stats" \
  -H "Accept: application/json"

# 필터링된 국가별 데이터
curl -X GET "https://dreamseedai.com/api/dashboard/country-data?user_type=paid&time_filter=daily" \
  -H "Accept: application/json"

# 캐시 무효화
curl -X POST "https://dreamseedai.com/api/cache/invalidate" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "dreamseed:stats"}'
```

## 📈 데이터 모델

### 대시보드 통계
```json
{
  "total_users": 1250,
  "online_users": 45,
  "realtime_users": 12,
  "free_users": 800,
  "paid_users": 350,
  "premium_users": 100,
  "revenue_today": 1500.50,
  "revenue_total": 45000.00
}
```

### 국가별 데이터
```json
[
  {
    "country": "KR",
    "country_name": "대한민국",
    "users": 450,
    "today_active": 25,
    "online_users": 12,
    "realtime_users": 5
  }
]
```

### 사용자 증가 데이터
```json
{
  "labels": ["2024-01-01", "2024-01-02", "2024-01-03"],
  "datasets": [
    {
      "label": "총 사용자",
      "data": [100, 120, 150],
      "borderColor": "#3B82F6"
    }
  ]
}
```

## ⚠️ 제한사항

- **요청 제한**: 분당 100회
- **응답 크기**: 최대 10MB
- **타임아웃**: 30초
- **동시 연결**: 최대 100개

## 🔍 오류 코드

| 코드 | 설명 | 해결 방법 |
|------|------|-----------|
| 400 | 잘못된 요청 | 요청 파라미터 확인 |
| 404 | 리소스 없음 | URL 경로 확인 |
| 429 | 요청 제한 초과 | 요청 빈도 조절 |
| 500 | 서버 오류 | 잠시 후 재시도 |

## 📞 지원

- **이메일**: support@dreamseed.com
- **문서**: https://docs.dreamseed.com
- **GitHub**: https://github.com/dreamseed/platform

## 📄 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

