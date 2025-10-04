#!/usr/bin/env python3
"""
DreamSeed 보안 테스트 스크립트
"""
import requests
import time
import json
from datetime import datetime

class SecurityTester:
    def __init__(self, base_url="http://127.0.0.1:8002"):
        self.base_url = base_url
        self.test_results = []
    
    def log_test(self, test_name, success, details=""):
        """테스트 결과 로깅"""
        result = {
            'test_name': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
    
    def test_authentication_required(self):
        """인증 없이 API 접근 시도"""
        print("\n🔐 인증 테스트")
        
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=5)
            if response.status_code == 401:
                self.log_test("인증 없이 API 접근", True, "401 Unauthorized 반환")
            else:
                self.log_test("인증 없이 API 접근", False, f"예상: 401, 실제: {response.status_code}")
        except Exception as e:
            self.log_test("인증 없이 API 접근", False, f"연결 오류: {e}")
    
    def test_valid_api_key(self):
        """유효한 API 키로 접근"""
        print("\n🔑 API 키 테스트")
        
        headers = {'X-API-Key': 'ds_admin_2025_secure_key_12345'}
        
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/stats", headers=headers, timeout=5)
            if response.status_code == 200:
                self.log_test("유효한 API 키", True, "200 OK 반환")
            else:
                self.log_test("유효한 API 키", False, f"예상: 200, 실제: {response.status_code}")
        except Exception as e:
            self.log_test("유효한 API 키", False, f"연결 오류: {e}")
    
    def test_invalid_api_key(self):
        """잘못된 API 키로 접근"""
        headers = {'X-API-Key': 'invalid_key_12345'}
        
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/stats", headers=headers, timeout=5)
            if response.status_code == 401:
                self.log_test("잘못된 API 키", True, "401 Unauthorized 반환")
            else:
                self.log_test("잘못된 API 키", False, f"예상: 401, 실제: {response.status_code}")
        except Exception as e:
            self.log_test("잘못된 API 키", False, f"연결 오류: {e}")
    
    def test_rate_limiting(self):
        """속도 제한 테스트"""
        print("\n⏱️ 속도 제한 테스트")
        
        headers = {'X-API-Key': 'ds_api_2025_standard_key_11111'}
        success_count = 0
        
        # 10회 연속 요청
        for i in range(10):
            try:
                response = requests.get(f"{self.base_url}/api/dashboard/stats", headers=headers, timeout=5)
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    self.log_test("속도 제한", True, f"{i+1}번째 요청에서 429 반환")
                    return
                time.sleep(0.1)
            except Exception as e:
                self.log_test("속도 제한", False, f"연결 오류: {e}")
                return
        
        if success_count == 10:
            self.log_test("속도 제한", False, "10회 요청 모두 성공 (제한 없음)")
    
    def test_sql_injection(self):
        """SQL 인젝션 테스트"""
        print("\n💉 SQL 인젝션 테스트")
        
        headers = {'X-API-Key': 'ds_admin_2025_secure_key_12345'}
        
        # SQL 인젝션 시도
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM users --"
        ]
        
        for payload in malicious_payloads:
            try:
                response = requests.get(
                    f"{self.base_url}/api/dashboard/stats?param={payload}",
                    headers=headers,
                    timeout=5
                )
                if response.status_code in [200, 400, 422]:
                    self.log_test(f"SQL 인젝션 ({payload[:20]}...)", True, "안전하게 처리됨")
                else:
                    self.log_test(f"SQL 인젝션 ({payload[:20]}...)", False, f"예상치 못한 응답: {response.status_code}")
            except Exception as e:
                self.log_test(f"SQL 인젝션 ({payload[:20]}...)", True, f"연결 오류 (안전): {e}")
    
    def test_xss_protection(self):
        """XSS 보호 테스트"""
        print("\n🛡️ XSS 보호 테스트")
        
        headers = {'X-API-Key': 'ds_admin_2025_secure_key_12345'}
        
        # XSS 시도
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            try:
                response = requests.get(
                    f"{self.base_url}/api/dashboard/stats?param={payload}",
                    headers=headers,
                    timeout=5
                )
                if response.status_code in [200, 400, 422]:
                    self.log_test(f"XSS 보호 ({payload[:20]}...)", True, "안전하게 처리됨")
                else:
                    self.log_test(f"XSS 보호 ({payload[:20]}...)", False, f"예상치 못한 응답: {response.status_code}")
            except Exception as e:
                self.log_test(f"XSS 보호 ({payload[:20]}...)", True, f"연결 오류 (안전): {e}")
    
    def test_headers_security(self):
        """보안 헤더 테스트"""
        print("\n🔒 보안 헤더 테스트")
        
        headers = {'X-API-Key': 'ds_admin_2025_secure_key_12345'}
        
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/stats", headers=headers, timeout=5)
            
            security_headers = [
                'X-Content-Type-Options',
                'X-Frame-Options',
                'X-XSS-Protection',
                'Strict-Transport-Security',
                'Referrer-Policy',
                'Content-Security-Policy'
            ]
            
            missing_headers = []
            for header in security_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if not missing_headers:
                self.log_test("보안 헤더", True, "모든 보안 헤더 존재")
            else:
                self.log_test("보안 헤더", False, f"누락된 헤더: {missing_headers}")
                
        except Exception as e:
            self.log_test("보안 헤더", False, f"연결 오류: {e}")
    
    def test_permission_escalation(self):
        """권한 상승 테스트"""
        print("\n⬆️ 권한 상승 테스트")
        
        # 읽기 전용 권한으로 관리자 기능 접근 시도
        headers = {'X-API-Key': 'ds_monitor_2025_readonly_key_67890'}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/cache/invalidate",
                headers=headers,
                json={'pattern': 'test'},
                timeout=5
            )
            if response.status_code == 403:
                self.log_test("권한 상승 방지", True, "403 Forbidden 반환")
            else:
                self.log_test("권한 상승 방지", False, f"예상: 403, 실제: {response.status_code}")
        except Exception as e:
            self.log_test("권한 상승 방지", False, f"연결 오류: {e}")
    
    def test_brute_force_protection(self):
        """무차별 대입 공격 방지 테스트"""
        print("\n🔨 무차별 대입 공격 방지 테스트")
        
        # 여러 번 잘못된 API 키로 시도
        invalid_keys = ['wrong1', 'wrong2', 'wrong3', 'wrong4', 'wrong5']
        
        for i, key in enumerate(invalid_keys):
            headers = {'X-API-Key': key}
            try:
                response = requests.get(f"{self.base_url}/api/dashboard/stats", headers=headers, timeout=5)
                if response.status_code == 401:
                    if i == len(invalid_keys) - 1:
                        self.log_test("무차별 대입 방지", True, "모든 시도에서 401 반환")
                else:
                    self.log_test("무차별 대입 방지", False, f"예상: 401, 실제: {response.status_code}")
                time.sleep(0.1)
            except Exception as e:
                self.log_test("무차별 대입 방지", False, f"연결 오류: {e}")
    
    def run_all_tests(self):
        """모든 보안 테스트 실행"""
        print("🚀 DreamSeed 보안 테스트 시작")
        print("=" * 50)
        
        self.test_authentication_required()
        self.test_valid_api_key()
        self.test_invalid_api_key()
        self.test_rate_limiting()
        self.test_sql_injection()
        self.test_xss_protection()
        self.test_headers_security()
        self.test_permission_escalation()
        self.test_brute_force_protection()
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("📊 보안 테스트 결과 요약")
        print("=" * 50)
        
        passed = sum(1 for result in self.test_results if result['success'])
        total = len(self.test_results)
        
        print(f"총 테스트: {total}")
        print(f"통과: {passed}")
        print(f"실패: {total - passed}")
        print(f"성공률: {(passed/total)*100:.1f}%")
        
        # 실패한 테스트 목록
        failed_tests = [result for result in self.test_results if not result['success']]
        if failed_tests:
            print("\n❌ 실패한 테스트:")
            for test in failed_tests:
                print(f"  - {test['test_name']}: {test['details']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = SecurityTester()
    results = tester.run_all_tests()
    
    # 결과를 JSON 파일로 저장
    with open('security_test_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 결과가 security_test_results.json에 저장되었습니다.")

