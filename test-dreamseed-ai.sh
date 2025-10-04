#!/bin/bash

# DreamSeedAI Auto Mode 테스트 스크립트

echo "🧪 DreamSeedAI Auto Mode 테스트 시작..."

# 라우터 헬스 체크
echo "1️⃣ 라우터 헬스 체크..."
curl -s http://127.0.0.1:8010/health | jq . || echo "❌ 라우터가 실행 중이 아닙니다."

echo ""
echo "2️⃣ 모델 목록 확인..."
curl -s http://127.0.0.1:8010/models | jq . || echo "❌ 모델 목록을 가져올 수 없습니다."

echo ""
echo "3️⃣ 일반 가이드 테스트 (Llama 3 8B)..."
curl -s http://127.0.0.1:8010/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dummy' \
  -d '{"model":"auto","messages":[{"role":"user","content":"DreamSeedAI.com의 목적 지향형 AI Guide 개요를 설명해줘."}]}' \
  | jq '.choices[0].message.content' || echo "❌ 일반 가이드 테스트 실패"

echo ""
echo "4️⃣ 코딩 테스트 (Qwen2.5-Coder 7B)..."
curl -s http://127.0.0.1:8010/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dummy' \
  -d '{"model":"auto","messages":[{"role":"user","content":"파이썬으로 이진탐색 함수 코드 작성해줘."}]}' \
  | jq '.choices[0].message.content' || echo "❌ 코딩 테스트 실패"

echo ""
echo "5️⃣ 빠른 응답 테스트 (Mistral 7B)..."
curl -s http://127.0.0.1:8010/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer dummy' \
  -d '{"model":"auto","messages":[{"role":"user","content":"짧게 핵심만 요약해줘"}]}' \
  | jq '.choices[0].message.content' || echo "❌ 빠른 응답 테스트 실패"

echo ""
echo "✅ DreamSeedAI Auto Mode 테스트 완료!"
