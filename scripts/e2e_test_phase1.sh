#!/bin/bash
# Phase 1 E2E Test Script
# Tests full user journey: Register → Login → Dashboard → Exam Flow

set -e

API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3001}"

echo "🧪 Phase 1 E2E Test Suite"
echo "=========================="
echo "API: $API_BASE_URL"
echo "Frontend: $FRONTEND_URL"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
test_passed() {
    echo -e "${GREEN}✓ $1${NC}"
    ((TESTS_PASSED++))
}

test_failed() {
    echo -e "${RED}✗ $1${NC}"
    ((TESTS_FAILED++))
}

# Generate random test user
TEST_EMAIL="test_$(date +%s)@dreamseed.ai"
TEST_PASSWORD="TestPass123!"

echo "📝 Test User: $TEST_EMAIL"
echo ""

# Test 1: Health Check
echo "Test 1: Backend Health Check"
if curl -f "$API_BASE_URL/" > /dev/null 2>&1; then
    test_passed "Backend is healthy"
else
    test_failed "Backend health check failed"
    exit 1
fi

# Test 2: User Registration
echo ""
echo "Test 2: User Registration"
REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"role\":\"student\"}")

if echo "$REGISTER_RESPONSE" | grep -q "id"; then
    test_passed "User registration successful"
    USER_ID=$(echo "$REGISTER_RESPONSE" | grep -o '"id":[0-9]*' | grep -o '[0-9]*')
    echo "   User ID: $USER_ID"
else
    test_failed "User registration failed: $REGISTER_RESPONSE"
    exit 1
fi

# Test 3: User Login
echo ""
echo "Test 3: User Login"
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_EMAIL&password=$TEST_PASSWORD")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    test_passed "User login successful"
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
    echo "   Token: ${ACCESS_TOKEN:0:20}..."
else
    test_failed "User login failed: $LOGIN_RESPONSE"
    exit 1
fi

# Test 4: Get Current User
echo ""
echo "Test 4: Get Current User (/api/auth/me)"
ME_RESPONSE=$(curl -s "$API_BASE_URL/api/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ME_RESPONSE" | grep -q "$TEST_EMAIL"; then
    test_passed "Current user endpoint working"
else
    test_failed "Current user endpoint failed: $ME_RESPONSE"
fi

# Test 5: Frontend Health
echo ""
echo "Test 5: Frontend Health Check"
if curl -f "$FRONTEND_URL" > /dev/null 2>&1; then
    test_passed "Frontend is accessible"
else
    test_failed "Frontend health check failed"
fi

# Test 6: List Exams (if available)
echo ""
echo "Test 6: List Exams (optional)"
EXAMS_RESPONSE=$(curl -s "$API_BASE_URL/api/exams" \
    -H "Authorization: Bearer $ACCESS_TOKEN" 2>&1)

if echo "$EXAMS_RESPONSE" | grep -q "Not Found"; then
    echo "   ⚠ Exam list endpoint not implemented yet (expected)"
else
    test_passed "Exam list endpoint responding"
fi

# Summary
echo ""
echo "=========================="
echo "📊 Test Summary"
echo "=========================="
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
echo -e "${RED}Failed: $TESTS_FAILED${NC}"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "🎉 All critical tests passed!"
    exit 0
else
    echo "❌ Some tests failed"
    exit 1
fi
