# DreamSeed AI Platform 문서

이 디렉토리는 DreamSeed AI Platform의 모든 문서를 포함합니다.

## 📚 문서 구조

```
docs/
├── README.md                 # 이 파일
├── api/                      # API 문서
│   └── README.md            # API 사용법 및 예제
├── user/                     # 사용자 문서
│   └── user_manual.md       # 사용자 매뉴얼
├── developer/                # 개발자 문서
│   └── developer_guide.md   # 개발자 가이드
├── deployment/               # 배포 문서
│   └── deployment_guide.md  # 배포 가이드
└── troubleshooting/          # 문제 해결 문서
    └── troubleshooting_guide.md  # 문제 해결 가이드
```

## 🎯 문서별 목적

### 📖 사용자 문서 (`user/`)
- **대상**: 일반 사용자, 관리자
- **목적**: 플랫폼 사용법 안내
- **내용**: 
  - 로그인 및 기본 사용법
  - 대시보드 사용법
  - 문제 관리
  - 사용자 관리
  - AI 채팅 사용법
  - MathML 변환 도구

### 🔌 API 문서 (`api/`)
- **대상**: 개발자, 시스템 통합자
- **목적**: API 사용법 및 통합 가이드
- **내용**:
  - API 엔드포인트 목록
  - 요청/응답 형식
  - 인증 방법
  - 사용 예제 (JavaScript, Python, cURL)
  - 오류 코드 및 해결 방법

### 🛠️ 개발자 문서 (`developer/`)
- **대상**: 개발자, 기여자
- **목적**: 개발 환경 설정 및 개발 가이드
- **내용**:
  - 개발 환경 설정
  - 프로젝트 구조
  - API 개발 가이드
  - 프론트엔드 개발
  - 데이터베이스 관리
  - 테스트 작성
  - 기여 가이드

### 🚀 배포 문서 (`deployment/`)
- **대상**: DevOps, 시스템 관리자
- **목적**: 프로덕션 배포 가이드
- **내용**:
  - 개발/스테이징/프로덕션 환경 설정
  - Docker 배포
  - Kubernetes 배포
  - 모니터링 설정
  - 백업 및 복구

### 🔧 문제 해결 문서 (`troubleshooting/`)
- **대상**: 모든 사용자
- **목적**: 일반적인 문제 해결
- **내용**:
  - 일반적인 문제
  - API 관련 문제
  - 데이터베이스 문제
  - 캐시 문제
  - 웹 인터페이스 문제
  - 성능 문제
  - 보안 문제

## 📖 문서 사용법

### 빠른 시작
1. **사용자**: [사용자 매뉴얼](user/user_manual.md)부터 시작
2. **개발자**: [개발자 가이드](developer/developer_guide.md)부터 시작
3. **DevOps**: [배포 가이드](deployment/deployment_guide.md)부터 시작

### 문제 해결
- 문제가 발생했을 때: [문제 해결 가이드](troubleshooting/troubleshooting_guide.md) 참조
- API 사용 시 문제: [API 문서](api/README.md)의 오류 코드 섹션 참조

### 문서 업데이트
- 문서는 프로젝트와 함께 지속적으로 업데이트됩니다
- 최신 버전은 항상 이 저장소에서 확인할 수 있습니다
- 문서에 오류가 있거나 개선 사항이 있으면 [GitHub Issues](https://github.com/dreamseed/platform/issues)에 보고해주세요

## 🔍 문서 검색

### 키워드별 검색
- **설치**: deployment/README.md, developer/developer_guide.md
- **API**: api/README.md
- **오류**: troubleshooting/troubleshooting_guide.md
- **사용법**: user/user_manual.md
- **개발**: developer/developer_guide.md

### 기능별 검색
- **대시보드**: user/user_manual.md의 "대시보드 사용법" 섹션
- **MathML 변환**: user/user_manual.md의 "MathML 변환" 섹션
- **모니터링**: deployment/deployment_guide.md의 "모니터링 설정" 섹션
- **테스트**: developer/developer_guide.md의 "테스트" 섹션

## 📝 문서 기여

### 문서 개선
1. **이슈 생성**: 문서 개선 사항을 [GitHub Issues](https://github.com/dreamseed/platform/issues)에 등록
2. **브랜치 생성**: `git checkout -b docs/improve-documentation`
3. **문서 수정**: 해당 문서 파일 편집
4. **Pull Request**: 변경사항을 PR로 제출

### 새 문서 추가
1. **문서 구조**: 기존 구조를 따라 적절한 디렉토리에 배치
2. **링크 추가**: README.md에 새 문서 링크 추가
3. **검색 키워드**: 문서에 적절한 키워드 포함

### 문서 스타일 가이드
- **언어**: 한국어 (기본), 영어 (선택)
- **형식**: Markdown (.md)
- **구조**: 목차, 섹션, 코드 블록, 예제 포함
- **링크**: 상대 경로 사용
- **이미지**: `docs/images/` 디렉토리에 저장

## 🔄 문서 버전 관리

### 버전 정보
- **현재 버전**: v1.0.0
- **최종 업데이트**: 2024년 1월 15일
- **다음 업데이트**: 기능 추가 시

### 변경 이력
- **v1.0.0** (2024-01-15): 초기 문서 작성
  - 사용자 매뉴얼 작성
  - API 문서 작성
  - 개발자 가이드 작성
  - 배포 가이드 작성
  - 문제 해결 가이드 작성

## 📞 문서 관련 문의

- **문서 오류**: [GitHub Issues](https://github.com/dreamseed/platform/issues)
- **문서 개선**: [GitHub Discussions](https://github.com/dreamseed/platform/discussions)
- **직접 문의**: docs@dreamseed.com

---

*이 문서는 DreamSeed AI Platform v1.0.0 기준으로 작성되었습니다.*
*최신 업데이트: 2024년 1월 15일*

