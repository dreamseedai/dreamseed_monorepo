# DreamSeedAI Backend

AI 기반 개인화 학습 플랫폼 백엔드 API

## 구조

```
backend/
├── app/
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── api/                 # API 엔드포인트
│   │   ├── assignment_api.py
│   │   ├── question_display_api.py
│   │   ├── mock_api.py
│   │   └── routers/
│   ├── services/            # 비즈니스 로직 & AI 서비스
│   │   ├── ai_mathml_converter.py
│   │   ├── real_ai_mathml_converter.py
│   │   ├── ai_client.py
│   │   ├── curriculum_classifier.py
│   │   ├── gpt_classification_system.py
│   │   └── enhanced_curriculum_standards.py
│   ├── utils/               # 유틸리티 함수
│   │   └── setup_openai_api.py
│   ├── models/              # 데이터 모델
│   └── core/                # 설정 및 코어 기능
└── README.md
```

## 실행 방법

### 개발 모드

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 프로덕션 모드

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 문서

서버 실행 후:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 주요 API 엔드포인트

- `GET /` - API 정보
- `GET /health` - 헬스 체크
- `POST /api/assignments/` - 과제 생성 (assignment_api.py)
- `GET /api/questions/` - 문제 표시 (question_display_api.py)

## 환경 변수

`.env` 파일 생성:

```env
DATABASE_URL=postgresql://user:password@localhost/dreamseed
OPENAI_API_KEY=your_openai_key
SECRET_KEY=your_secret_key
```

## 의존성 설치

```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv openai
```
