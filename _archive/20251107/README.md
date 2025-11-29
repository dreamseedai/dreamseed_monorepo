# Archive 2025-11-07

## seedtest-web

**아카이브 날짜**: 2025-11-07  
**아카이브 사유**: 레거시 프로젝트, 소스 코드 부재 (빌드 아티팩트만 존재)

### 상태
- 소스 코드 없음 (package.json, 컴포넌트 파일 등 부재)
- 빌드 아티팩트만 존재 (.next/, node_modules/)
- 마지막 빌드: 2025-10-16

### 대체 프로젝트
**examinee-frontend** (`/apps/examinee-frontend/`)
- Next.js 14 + React 18 + TypeScript
- 완전한 소스 코드 및 테스트
- CI/CD 파이프라인 (Vercel)
- 국제화 지원

### 복원 방법
필요 시 Git 히스토리에서 소스 코드 복원:
```bash
git log --all --full-history -- apps/seedtest-web/
```

### 참고
- 환경 설정: Flask 백엔드 참조 (현재는 FastAPI로 전환됨)
- 빌드 ID: WhOX8l4YzXdok6c0_Pzax
