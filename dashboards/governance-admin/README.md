# Governance Admin Dashboard

## 개요
거버넌스 정책 관리 및 모니터링 대시보드

## 주요 기능
- 정책 번들 전환 (Phase 0/1/2/3)
- RBAC 권한 매트릭스 뷰
- Feature Flags 콘솔
- 승인 요청 대기열
- 감사 로그 뷰어

## 개발 예정
현재는 placeholder입니다. 다음 기술 스택으로 구현 예정:
- React + TypeScript
- TanStack Query (React Query)
- Tailwind CSS
- Recharts (차트)

## API 엔드포인트
```
GET  /api/v1/governance/dashboard    - 대시보드 데이터
POST /api/v1/governance/reload       - 정책 번들 핫리로드
GET  /api/v1/governance/approvals    - 승인 대기 목록
GET  /api/v1/governance/audit        - 감사 로그
```

## 빠른 시작
```bash
# 개발 서버 시작 (예정)
npm run dev
```
