# API Integration Guide

**Document**: 04_API_INTEGRATION_GUIDE.md  
**Part of**: IRT System Documentation Series  
**Created**: 2025-11-05  
**Status**: ✅ Production Ready  

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Authentication](#authentication)
3. [API Endpoints](#api-endpoints)
4. [Request/Response Examples](#requestresponse-examples)
5. [Error Handling](#error-handling)
6. [Rate Limiting](#rate-limiting)
7. [Integration Patterns](#integration-patterns)
8. [한글 가이드 (Korean Guide)](#한글-가이드-korean-guide)

---

## Quick Start

### Base URL

```
Production: https://api.dreamseedai.com/api/irt
Staging:    https://staging-api.dreamseedai.com/api/irt
Local:      http://localhost:8000/api/irt
```

### Quick Test

```bash
# Get API health
curl https://api.dreamseedai.com/api/irt/health

# Get drift summary (requires auth)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.dreamseedai.com/api/irt/drift/summary
```

---

## Authentication

### JWT Token Authentication

All IRT endpoints require JWT authentication.

#### 1. Obtain Token

```bash
# Login to get token
curl -X POST https://api.dreamseedai.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@dreamseedai.com",
    "password": "your_password"
  }'

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

#### 2. Use Token in Requests

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  https://api.dreamseedai.com/api/irt/drift/summary
```

### Python Example

```python
import requests

# Login
response = requests.post(
    'https://api.dreamseedai.com/api/auth/login',
    json={'email': 'admin@example.com', 'password': 'password'}
)
token = response.json()['access_token']

# Use token
headers = {'Authorization': f'Bearer {token}'}
response = requests.get(
    'https://api.dreamseedai.com/api/irt/drift/summary',
    headers=headers
)
data = response.json()
```

---

## API Endpoints

### 1. Drift Detection

#### GET `/drift/summary`

Get drift detection summary for all windows.

**Response**:
```json
{
  "windows": [
    {
      "window_id": 12,
      "window_start": "2024-10-01",
      "window_end": "2024-10-31",
      "alert_counts": {
        "critical": 3,
        "high": 12,
        "medium": 45
      }
    }
  ]
}
```

---

#### GET `/drift/alerts`

Get all drift alerts with filtering.

**Query Parameters**:
- `window_id` (optional): Filter by window
- `severity` (optional): Filter by severity (critical/high/medium)
- `metric` (optional): Filter by metric (difficulty/discrimination/guessing)
- `skip` (default: 0): Pagination offset
- `limit` (default: 100): Pagination limit

**Example**:
```bash
GET /drift/alerts?severity=critical&limit=20
```

**Response**:
```json
{
  "total": 3,
  "items": [
    {
      "alert_id": 101,
      "window_id": 12,
      "item_id": 2045,
      "metric": "difficulty",
      "old_value": 0.5,
      "new_value": 1.2,
      "delta": 0.7,
      "severity": "critical",
      "detected_at": "2024-11-01T08:30:00Z"
    }
  ]
}
```

---

### 2. Item Parameters

#### GET `/items/{item_id}/parameters`

Get current parameters for a specific item.

**Response**:
```json
{
  "item_id": 2045,
  "a": 1.2,
  "b": 0.8,
  "c": 0.23,
  "a_se": 0.15,
  "b_se": 0.12,
  "c_se": 0.04,
  "model": "3PL",
  "calibrated_at": "2024-11-01T08:00:00Z"
}
```

---

#### GET `/items/{item_id}/history`

Get parameter history for an item across all windows.

**Query Parameters**:
- `limit` (default: 10): Number of windows to return

**Response**:
```json
{
  "item_id": 2045,
  "history": [
    {
      "window_id": 12,
      "window_start": "2024-10-01",
      "window_end": "2024-10-31",
      "a": 1.2,
      "b": 0.8,
      "c": 0.23
    },
    {
      "window_id": 11,
      "window_start": "2024-09-01",
      "window_end": "2024-09-30",
      "a": 1.15,
      "b": 0.5,
      "c": 0.22
    }
  ]
}
```

---

### 3. Item Characteristic Curves

#### GET `/items/{item_id}/icc`

Get Item Characteristic Curve data.

**Query Parameters**:
- `theta_min` (default: -3.0): Minimum ability
- `theta_max` (default: 3.0): Maximum ability
- `points` (default: 61): Number of points

**Response**:
```json
{
  "item_id": 2045,
  "model": "3PL",
  "a": 1.2,
  "b": 0.8,
  "c": 0.23,
  "curve": [
    {"theta": -3.0, "prob": 0.23},
    {"theta": -2.9, "prob": 0.24},
    ...
    {"theta": 3.0, "prob": 0.99}
  ]
}
```

---

#### GET `/items/{item_id}/iif`

Get Item Information Function data.

**Response**:
```json
{
  "item_id": 2045,
  "model": "3PL",
  "information": [
    {"theta": -3.0, "info": 0.05},
    {"theta": -2.9, "info": 0.06},
    ...
    {"theta": 0.8, "info": 0.85},
    ...
    {"theta": 3.0, "info": 0.04}
  ],
  "max_info": 0.85,
  "max_info_theta": 0.8
}
```

---

### 4. Ability Estimation

#### POST `/estimate/eap`

Estimate ability using Expected A Posteriori (EAP).

**Request**:
```json
{
  "responses": [
    {"item_id": 2045, "correct": true},
    {"item_id": 2046, "correct": false},
    {"item_id": 2047, "correct": true}
  ],
  "prior_mean": 0.0,
  "prior_sd": 1.0
}
```

**Response**:
```json
{
  "theta": 0.42,
  "se": 0.35,
  "method": "EAP"
}
```

---

#### POST `/estimate/mle`

Estimate ability using Maximum Likelihood Estimation (MLE).

**Request**: Same as EAP

**Response**:
```json
{
  "theta": 0.45,
  "se": 0.38,
  "method": "MLE"
}
```

---

### 5. CAT Item Selection

#### POST `/cat/select`

Select next item for Computer Adaptive Testing.

**Request**:
```json
{
  "theta_current": 0.5,
  "responses": [
    {"item_id": 2045, "correct": true},
    {"item_id": 2046, "correct": false}
  ],
  "exclude_items": [2045, 2046],
  "method": "MFI",
  "exposure_control": true,
  "content_balancing": {
    "algebra": 0.3,
    "geometry": 0.3,
    "statistics": 0.4
  }
}
```

**Response**:
```json
{
  "item_id": 2050,
  "expected_info": 0.82,
  "selection_method": "MFI",
  "item_details": {
    "a": 1.5,
    "b": 0.55,
    "c": 0.20,
    "content_area": "algebra"
  }
}
```

---

### 6. DIF Analysis

#### GET `/dif/items/{item_id}`

Get DIF analysis for a specific item.

**Query Parameters**:
- `window_id`: Calibration window
- `group_column`: Demographic column (gender/language/age_group)

**Response**:
```json
{
  "item_id": 2045,
  "window_id": 12,
  "group_column": "gender",
  "comparisons": {
    "male_vs_female": {
      "delta_mean": 0.35,
      "delta_median": 0.32,
      "prob_dif": 0.94,
      "ci_95": [0.15, 0.55],
      "bayes_factor": 15.2,
      "evidence": "Strong DIF"
    }
  }
}
```

---

### 7. Reports

#### GET `/report/monthly/{window_id}`

Download monthly calibration report (PDF).

**Response**: PDF file (application/pdf)

**Example**:
```bash
curl -H "Authorization: Bearer TOKEN" \
  https://api.dreamseedai.com/api/irt/report/monthly/12 \
  -o report_2024_10.pdf
```

---

#### POST `/report/custom`

Generate custom report with selected items.

**Request**:
```json
{
  "window_id": 12,
  "item_ids": [2045, 2046, 2047],
  "include_icc": true,
  "include_iif": true,
  "include_history": true
}
```

**Response**: PDF file

---

### 8. Calibration Status

#### GET `/calibration/status`

Get current calibration job status.

**Response**:
```json
{
  "window_id": 12,
  "status": "running",
  "method": "pymc",
  "started_at": "2024-11-01T02:00:00Z",
  "progress": 65,
  "estimated_completion": "2024-11-01T03:15:00Z"
}
```

---

#### POST `/calibration/trigger`

Manually trigger calibration (admin only).

**Request**:
```json
{
  "window_start": "2024-10-01",
  "window_end": "2024-10-31",
  "method": "pymc",
  "model": "3PL"
}
```

**Response**:
```json
{
  "job_id": "calib_20241101_120000",
  "status": "queued",
  "message": "Calibration job queued successfully"
}
```

---

## Request/Response Examples

### Example 1: Get Drift Alerts for Critical Items

```python
import requests

API_BASE = 'https://api.dreamseedai.com/api/irt'
headers = {'Authorization': f'Bearer {token}'}

# Get critical alerts
response = requests.get(
    f'{API_BASE}/drift/alerts',
    headers=headers,
    params={'severity': 'critical', 'limit': 50}
)

alerts = response.json()['items']

for alert in alerts:
    print(f"Item {alert['item_id']}: {alert['metric']}")
    print(f"  Old: {alert['old_value']:.3f}")
    print(f"  New: {alert['new_value']:.3f}")
    print(f"  Δ: {alert['delta']:+.3f}\n")
```

---

### Example 2: Plot Item Characteristic Curve

```python
import requests
import matplotlib.pyplot as plt

# Get ICC data
response = requests.get(
    f'{API_BASE}/items/2045/icc',
    headers=headers,
    params={'theta_min': -3, 'theta_max': 3, 'points': 61}
)

data = response.json()
curve = data['curve']

# Plot
theta = [p['theta'] for p in curve]
prob = [p['prob'] for p in curve]

plt.figure(figsize=(10, 6))
plt.plot(theta, prob, linewidth=2)
plt.axvline(data['b'], color='red', linestyle='--', 
            label=f'b = {data["b"]:.2f}')
plt.xlabel('Ability (θ)')
plt.ylabel('P(correct)')
plt.title(f'Item {data["item_id"]} - ICC')
plt.grid(True, alpha=0.3)
plt.legend()
plt.show()
```

---

### Example 3: CAT Session

```python
class CATSession:
    def __init__(self, api_base, token):
        self.api_base = api_base
        self.headers = {'Authorization': f'Bearer {token}'}
        self.responses = []
        self.theta_current = 0.0
        self.se_current = 1.0
    
    def select_next_item(self):
        """Select next item using MFI."""
        response = requests.post(
            f'{self.api_base}/cat/select',
            headers=self.headers,
            json={
                'theta_current': self.theta_current,
                'responses': self.responses,
                'exclude_items': [r['item_id'] for r in self.responses],
                'method': 'MFI',
                'exposure_control': True
            }
        )
        return response.json()
    
    def submit_response(self, item_id, correct):
        """Submit response and update theta."""
        self.responses.append({
            'item_id': item_id,
            'correct': correct
        })
        
        # Re-estimate theta
        response = requests.post(
            f'{self.api_base}/estimate/eap',
            headers=self.headers,
            json={
                'responses': self.responses,
                'prior_mean': 0.0,
                'prior_sd': 1.0
            }
        )
        
        result = response.json()
        self.theta_current = result['theta']
        self.se_current = result['se']
        
        return result
    
    def is_complete(self, min_items=10, max_se=0.3):
        """Check if CAT is complete."""
        return (len(self.responses) >= min_items and 
                self.se_current < max_se)

# Usage
cat = CATSession(API_BASE, token)

while not cat.is_complete():
    # Select next item
    item = cat.select_next_item()
    print(f"Next item: {item['item_id']}")
    
    # Administer item and get response (from test-taker)
    correct = get_response_from_test_taker(item['item_id'])
    
    # Submit and update
    result = cat.submit_response(item['item_id'], correct)
    print(f"θ = {result['theta']:.2f} ± {result['se']:.2f}")

print(f"CAT complete! Final θ = {cat.theta_current:.2f}")
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "IRT_ERROR_CODE",
  "status_code": 400
}
```

### Common Error Codes

| Code | HTTP Status | Meaning | Solution |
|------|-------------|---------|----------|
| `IRT_ITEM_NOT_FOUND` | 404 | Item doesn't exist | Check item_id |
| `IRT_WINDOW_NOT_FOUND` | 404 | Window doesn't exist | Check window_id |
| `IRT_NO_PARAMETERS` | 404 | Item not calibrated yet | Wait for calibration |
| `IRT_INVALID_THETA` | 400 | Theta out of range | Use θ ∈ [-4, 4] |
| `IRT_INSUFFICIENT_RESPONSES` | 400 | Too few responses for CAT | Need ≥ 3 responses |
| `IRT_CALIBRATION_RUNNING` | 409 | Calibration in progress | Wait for completion |
| `AUTH_UNAUTHORIZED` | 401 | Invalid/expired token | Re-authenticate |
| `AUTH_FORBIDDEN` | 403 | Insufficient permissions | Contact admin |

---

### Python Error Handling

```python
import requests
from requests.exceptions import HTTPError

try:
    response = requests.get(
        f'{API_BASE}/items/9999/parameters',
        headers=headers
    )
    response.raise_for_status()
    data = response.json()
    
except HTTPError as e:
    if e.response.status_code == 404:
        print("Item not found or not calibrated")
    elif e.response.status_code == 401:
        print("Token expired, re-authenticating...")
        # Re-authenticate
    else:
        error_detail = e.response.json()
        print(f"Error: {error_detail['detail']}")
        print(f"Code: {error_detail.get('error_code')}")
```

---

## Rate Limiting

### Limits

| Endpoint Category | Rate Limit | Window |
|-------------------|------------|--------|
| Read (GET) | 1000 requests | 1 hour |
| Write (POST/PUT) | 100 requests | 1 hour |
| Report Generation | 10 requests | 1 hour |
| CAT Selection | 500 requests | 1 hour |

### Rate Limit Headers

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 847
X-RateLimit-Reset: 1699012800
```

### Handling Rate Limits

```python
import time

def api_call_with_retry(url, headers, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url, headers=headers)
        
        if response.status_code == 429:  # Rate limited
            reset_time = int(response.headers['X-RateLimit-Reset'])
            wait_seconds = reset_time - int(time.time())
            print(f"Rate limited. Waiting {wait_seconds}s...")
            time.sleep(wait_seconds + 1)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

---

## Integration Patterns

### Pattern 1: React Dashboard

```typescript
// File: portal_front/src/hooks/useIrtApi.ts

import { useState, useEffect } from 'react';
import axios from 'axios';

interface DriftAlert {
  alert_id: number;
  item_id: number;
  metric: string;
  delta: number;
  severity: string;
}

export function useIrtDriftAlerts(windowId?: number) {
  const [alerts, setAlerts] = useState<DriftAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const response = await axios.get('/api/irt/drift/alerts', {
          params: { window_id: windowId, severity: 'critical' },
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        });
        setAlerts(response.data.items);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, [windowId]);

  return { alerts, loading, error };
}

// Usage in component
function DriftDashboard() {
  const { alerts, loading, error } = useIrtDriftAlerts(12);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h2>Critical Drift Alerts</h2>
      {alerts.map(alert => (
        <div key={alert.alert_id}>
          Item {alert.item_id}: {alert.metric} Δ={alert.delta.toFixed(3)}
        </div>
      ))}
    </div>
  );
}
```

---

### Pattern 2: Scheduled Job (Python)

```python
# File: scripts/nightly_drift_report.py

import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

API_BASE = 'https://api.dreamseedai.com/api/irt'
TOKEN = get_api_token()  # From environment or config

def generate_nightly_report():
    """Generate and email nightly drift report."""
    headers = {'Authorization': f'Bearer {TOKEN}'}
    
    # Get critical alerts
    response = requests.get(
        f'{API_BASE}/drift/alerts',
        headers=headers,
        params={'severity': 'critical'}
    )
    alerts = response.json()['items']
    
    if not alerts:
        print("No critical alerts today")
        return
    
    # Format email
    body = f"Daily IRT Drift Report - {datetime.now():%Y-%m-%d}\n\n"
    body += f"Critical Alerts: {len(alerts)}\n\n"
    
    for alert in alerts:
        body += f"- Item {alert['item_id']}: {alert['metric']}\n"
        body += f"  Old: {alert['old_value']:.3f}, "
        body += f"New: {alert['new_value']:.3f}, "
        body += f"Δ: {alert['delta']:+.3f}\n\n"
    
    # Send email
    msg = MIMEText(body)
    msg['Subject'] = f'IRT Drift Alert - {len(alerts)} Critical Items'
    msg['From'] = 'irt-system@dreamseedai.com'
    msg['To'] = 'admin@dreamseedai.com'
    
    with smtplib.SMTP('localhost') as smtp:
        smtp.send_message(msg)
    
    print(f"Report sent: {len(alerts)} alerts")

if __name__ == '__main__':
    generate_nightly_report()
```

**Cron job**:
```bash
# Run daily at 9 AM
0 9 * * * /usr/bin/python3 /path/to/nightly_drift_report.py
```

---

### Pattern 3: CAT Integration

```python
# File: apps/seedtest_api/routes/test_session.py

from fastapi import APIRouter, Depends
import requests

router = APIRouter()
IRT_API = 'http://localhost:8000/api/irt'

@router.post('/test-session/{session_id}/next-item')
async def get_next_item(
    session_id: int,
    current_user = Depends(get_current_user)
):
    """Get next CAT item for test session."""
    
    # Get session data
    session = get_test_session(session_id)
    
    # Call IRT API
    response = requests.post(
        f'{IRT_API}/cat/select',
        json={
            'theta_current': session.theta_estimate,
            'responses': session.responses,
            'exclude_items': [r['item_id'] for r in session.responses],
            'method': 'MFI',
            'exposure_control': True
        },
        headers={'Authorization': f'Bearer {get_irt_token()}'}
    )
    
    next_item = response.json()
    
    # Log item selection
    log_item_selection(session_id, next_item['item_id'])
    
    return {
        'item_id': next_item['item_id'],
        'content': get_item_content(next_item['item_id']),
        'current_theta': session.theta_estimate
    }
```

---

## 한글 가이드 (Korean Guide)

### 빠른 시작

**API 주소**:
```
프로덕션: https://api.dreamseedai.com/api/irt
스테이징: https://staging-api.dreamseedai.com/api/irt
```

**인증**:
```bash
# 1. 토큰 받기
curl -X POST https://api.dreamseedai.com/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "password"}'

# 2. API 호출
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.dreamseedai.com/api/irt/drift/summary
```

---

### 주요 엔드포인트

#### 1. 드리프트 알림 조회
```bash
GET /drift/alerts?severity=critical
```

**응답**:
```json
{
  "items": [
    {
      "item_id": 2045,
      "metric": "difficulty",
      "delta": 0.7,
      "severity": "critical"
    }
  ]
}
```

---

#### 2. 문항 파라미터 조회
```bash
GET /items/2045/parameters
```

**응답**:
```json
{
  "item_id": 2045,
  "a": 1.2,
  "b": 0.8,
  "c": 0.23
}
```

---

#### 3. CAT 문항 선택
```bash
POST /cat/select
```

**요청**:
```json
{
  "theta_current": 0.5,
  "responses": [...],
  "method": "MFI"
}
```

**응답**:
```json
{
  "item_id": 2050,
  "expected_info": 0.82
}
```

---

### Python 예제

```python
import requests

# API 설정
API_BASE = 'https://api.dreamseedai.com/api/irt'
token = 'YOUR_TOKEN'
headers = {'Authorization': f'Bearer {token}'}

# 심각한 드리프트 알림 가져오기
response = requests.get(
    f'{API_BASE}/drift/alerts',
    headers=headers,
    params={'severity': 'critical'}
)

alerts = response.json()['items']
print(f"심각한 알림: {len(alerts)}개")

for alert in alerts:
    print(f"문항 {alert['item_id']}: Δ={alert['delta']:.3f}")
```

---

### 오류 처리

**일반적인 오류**:
- `404`: 문항 없음 또는 미캘리브레이션
- `401`: 토큰 만료 → 재인증 필요
- `429`: 요청 제한 초과 → 대기 후 재시도

**Python 예제**:
```python
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()
except requests.HTTPError as e:
    if e.response.status_code == 404:
        print("문항을 찾을 수 없습니다")
    elif e.response.status_code == 401:
        print("토큰이 만료되었습니다")
```

---

### React 통합

```typescript
// 커스텀 훅
function useIrtAlerts(windowId) {
  const [alerts, setAlerts] = useState([]);
  
  useEffect(() => {
    fetch(`/api/irt/drift/alerts?window_id=${windowId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setAlerts(data.items));
  }, [windowId]);
  
  return alerts;
}

// 컴포넌트에서 사용
function Dashboard() {
  const alerts = useIrtAlerts(12);
  
  return (
    <div>
      <h2>드리프트 알림</h2>
      {alerts.map(alert => (
        <div key={alert.alert_id}>
          문항 {alert.item_id}: {alert.metric}
        </div>
      ))}
    </div>
  );
}
```

---

### 다음 단계

1. **토큰 발급**: 관리자에게 API 접근 권한 요청
2. **테스트**: Postman이나 curl로 엔드포인트 테스트
3. **통합**: 프론트엔드 또는 백엔드에 API 호출 추가
4. **모니터링**: 오류 및 응답 시간 모니터링

---

**작성자**: DreamSeed AI Team  
**최종 업데이트**: 2025-11-05  
**관련 문서**: 01_IMPLEMENTATION_REPORT.md, 03_DRIFT_DETECTION_GUIDE.md
