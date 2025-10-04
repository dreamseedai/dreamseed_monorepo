# DreamSeedAI Backend APIs

이 디렉토리는 DreamSeedAI의 백엔드 API 서버들을 포함합니다.

## 📁 구조

```
backend/
├── python/          # FastAPI 서버
│   ├── app/
│   │   └── main.py
│   └── requirements.txt
└── node/            # Express 서버
    ├── src/
    │   ├── routes/
    │   │   └── diagnostics.ts
    │   └── server.ts
    ├── package.json
    └── tsconfig.json
```

## 🚀 실행 방법

### FastAPI (Python)

```bash
# 의존성 설치
cd backend/python
pip install -r requirements.txt

# 서버 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 또는 직접 실행
python app/main.py
```

### Express (Node.js)

```bash
# 의존성 설치
cd backend/node
npm install

# 개발 서버 실행
npm run dev

# 또는 빌드 후 실행
npm run build
npm start
```

## 🧪 API 테스트

### 진단 API 테스트

```bash
# FastAPI 또는 Express 서버 실행 후
curl -X POST http://localhost:8000/api/diagnostics/run \
  -H 'Content-Type: application/json' \
  -d '{
    "userId": "u123",
    "context": {
      "country": "US",
      "grade": "G11", 
      "goal": "SAT_1500_PLUS"
    }
  }'
```

### 프로파일 API 테스트

```bash
# 프로파일 조회
curl http://localhost:8000/api/profile/u123

# 프로파일 생성/업데이트
curl -X POST http://localhost:8000/api/profile \
  -H 'Content-Type: application/json' \
  -d '{
    "userId": "u123",
    "country": "US",
    "grade": "G11",
    "goals": ["SAT_1500_PLUS"],
    "languages": ["en"]
  }'
```

## 📋 API 엔드포인트

### 진단 API

- `POST /api/diagnostics/run` - 사용자 진단 실행
- `GET /api/profile/{userId}` - 사용자 프로파일 조회
- `POST /api/profile` - 사용자 프로파일 생성/업데이트

### 헬스체크

- `GET /` - API 상태 확인
- `GET /health` - 헬스체크

## 🔧 환경 설정

### CORS 설정

두 서버 모두 다음 도메인에서의 요청을 허용합니다:
- `https://dreamseedai.com`
- `https://staging.dreamseedai.com`
- `http://localhost:5173` (개발용)
- `http://localhost:3000` (개발용)

### 포트 설정

기본 포트: `8000`
환경 변수 `PORT`로 변경 가능

## 📝 프론트엔드 연결

프론트엔드에서 API를 호출할 때:

```typescript
// src/api/diagnostics.ts
import { DiagnosticRequest, DiagnosticResponse } from './types/profile';

export async function runDiagnostics(request: DiagnosticRequest): Promise<DiagnosticResponse> {
  const response = await fetch('/api/diagnostics/run', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });
  
  if (!response.ok) {
    throw new Error('Diagnostic request failed');
  }
  
  return response.json();
}
```

## 🐳 Docker 실행 (선택사항)

### FastAPI Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Express Dockerfile

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
CMD ["npm", "start"]
```


