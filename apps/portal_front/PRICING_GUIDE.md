# DreamSeedAI 홈 화면 - Free/Pro/Premium 구조

## 🎯 구현된 기능

### ✅ 요금제 구조
- **Free**: 무료 - 기본 학습 자료와 가이드
- **Pro**: $25/월 - 개인화된 학습 계획과 고급 기능
- **Premium**: $99/월 (학생) - 최고급 기능과 1:1 멘토링

### ✅ 환경변수 제어
- `VITE_BILLING_ENABLED`: 결제 시스템 활성화 여부
- `VITE_PAID_READY`: 유료 콘텐츠 준비 완료 여부

## 🚀 사용 방법

### 개발 환경 (무료 모드)
```bash
npm run dev
```
- Pro/Premium 카드에 "Coming soon" 배지 표시
- 결제 버튼 비활성화

### 개발 환경 (유료 모드)
```bash
npm run dev:paid
```
- 모든 기능 활성화
- 결제 버튼 활성화

### 프로덕션 빌드
```bash
# 무료 모드
npm run build

# 유료 모드
npm run build:paid
```

## 📝 주요 컴포넌트

### 1. Hero Section
- 메인 타이틀과 CTA 버튼
- "내 전략 보기" 버튼으로 가이드 탐색

### 2. Quick Start
- 국가/학년/목표 선택기
- 맞춤형 학습 계획 생성

### 3. Learning Modules
- 6개 주요 학습 모듈
- English, Math, Science, Social Studies, AP Courses, Test Prep

### 4. Pricing Plans
- 3단계 요금제 카드
- 환경변수에 따른 활성화/비활성화

## 🔧 환경변수 설정

### 개발 환경
```bash
# .env.development
VITE_BILLING_ENABLED=false
VITE_PAID_READY=false
```

### 프로덕션 환경
```bash
# .env.production
VITE_BILLING_ENABLED=true
VITE_PAID_READY=true
```

## 📱 반응형 디자인

- **모바일**: 1열 레이아웃
- **태블릿**: 2열 레이아웃
- **데스크톱**: 3열 레이아웃

## 🌐 다국어 지원

현재 한국어/영어 지원:
- `copy.ko`: 한국어 텍스트
- `copy.en`: 영어 텍스트
- 추후 i18n 라이브러리로 확장 가능

## 🎨 스타일링

- **Tailwind CSS** 사용
- **다크 모드** 지원
- **그라데이션** 및 **그림자** 효과
- **호버 애니메이션** 포함

## 🔄 다음 단계

1. **목표 선택 → 내 전략 보기**: `/plan?country=US&grade=G11&goal=SAT1500`
2. **Pro 기능 연결**: 사용자 프로파일 API (`/api/profile/*`)
3. **Premium 분석 대시보드**: `/dashboard`에 성취도 곡선 추가
4. **결제 연동**: BILLING_ENABLED=true일 때 `/billing/checkout` 연결

## 📊 요금제 비교

| 기능 | Free | Pro | Premium |
|------|------|-----|---------|
| 기본 학습 가이드 | ✅ | ✅ | ✅ |
| 개인화된 학습 계획 | ❌ | ✅ | ✅ |
| 무제한 문제 풀이 | ❌ | ✅ | ✅ |
| 고급 AI 추천 | ❌ | ✅ | ✅ |
| 1:1 멘토링 | ❌ | ❌ | ✅ |
| 고급 분석 대시보드 | ❌ | ❌ | ✅ |
| 전문가 상담 | ❌ | ❌ | ✅ |

## 🚨 주의사항

- 유료 콘텐츠가 충분히 준비될 때까지 `VITE_PAID_READY=false`로 설정
- 실제 결제 연동 전까지는 데모 모드로 운영
- 가족/학교 패키지는 별도 문의 안내


