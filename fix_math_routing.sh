#!/bin/bash

echo "🔧 Math 라우팅 문제 해결 시작..."

# 1. 프론트엔드 빌드
echo "📦 프론트엔드 빌드 중..."
cd apps/portal_front
npm run build

if [ $? -eq 0 ]; then
    echo "✅ 프론트엔드 빌드 성공"
else
    echo "❌ 프론트엔드 빌드 실패"
    exit 1
fi

# 2. 배포 디렉토리로 복사
echo "📁 배포 파일 복사 중..."
sudo cp -r dist/* /srv/portal_front/current/

if [ $? -eq 0 ]; then
    echo "✅ 배포 파일 복사 성공"
else
    echo "❌ 배포 파일 복사 실패"
    exit 1
fi

# 3. nginx 설정 업데이트
echo "⚙️ nginx 설정 업데이트 중..."
cd ../..
sudo cp infra/nginx/portal.dreamseedai.com.conf /etc/nginx/sites-available/portal.dreamseedai.com

if [ $? -eq 0 ]; then
    echo "✅ nginx 설정 복사 성공"
else
    echo "❌ nginx 설정 복사 실패"
    exit 1
fi

# 4. nginx 설정 테스트
echo "🧪 nginx 설정 테스트 중..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ nginx 설정 테스트 성공"
else
    echo "❌ nginx 설정 테스트 실패"
    exit 1
fi

# 5. nginx 재시작
echo "🔄 nginx 재시작 중..."
sudo systemctl reload nginx

if [ $? -eq 0 ]; then
    echo "✅ nginx 재시작 성공"
else
    echo "❌ nginx 재시작 실패"
    exit 1
fi

# 6. 캐시 클리어
echo "🧹 캐시 클리어 중..."
sudo systemctl restart nginx

echo "🎉 Math 라우팅 문제 해결 완료!"
echo ""
echo "📝 테스트 방법:"
echo "   1. https://dreamseedai.com/ 접속"
echo "   2. Math 버튼 클릭 → 학년 선택 페이지 확인"
echo "   3. https://dreamseedai.com/math 직접 접근 → 학년 선택 페이지 확인"
echo ""
echo "🔍 문제가 지속되면:"
echo "   - 브라우저 캐시 클리어 (Ctrl + F5)"
echo "   - 시크릿 모드에서 테스트"
