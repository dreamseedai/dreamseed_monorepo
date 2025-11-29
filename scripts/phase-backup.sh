#!/bin/bash
# Phase 작업물 자동 백업 스크립트

set -e

PHASE_NUM=$1
if [ -z "$PHASE_NUM" ]; then
    echo "Usage: $0 <phase_number>"
    echo "Example: $0 2"
    exit 1
fi

PHASE_DIR="ops/phase${PHASE_NUM}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=".backups/phase${PHASE_NUM}_${TIMESTAMP}"

echo "🔄 Phase ${PHASE_NUM} 백업 시작..."

# 백업 디렉토리 생성
mkdir -p "$BACKUP_DIR"

# Phase 파일 복사
if [ -d "$PHASE_DIR" ]; then
    cp -r "$PHASE_DIR" "$BACKUP_DIR/"
    echo "✅ $PHASE_DIR 백업 완료"
else
    echo "⚠️  $PHASE_DIR 디렉토리가 없습니다"
fi

# Backend Phase 문서 복사
find backend -name "PHASE${PHASE_NUM}_*.md" -exec cp {} "$BACKUP_DIR/" \; 2>/dev/null || true

# Git에 추가
echo "📝 Git에 추가 중..."
git add -f "$PHASE_DIR/" 2>/dev/null || true
git add -f backend/PHASE${PHASE_NUM}_*.md 2>/dev/null || true

# 상태 확인
echo -e "\n📊 현재 상태:"
echo "- Phase 파일: $(find $PHASE_DIR -type f 2>/dev/null | wc -l)개"
echo "- Git 추적: $(git ls-files $PHASE_DIR 2>/dev/null | wc -l)개"
echo "- 백업 위치: $BACKUP_DIR"

echo -e "\n✅ 백업 완료!"
echo "다음 명령으로 커밋하세요:"
echo "  git commit -m 'docs: Complete Phase ${PHASE_NUM}'"
