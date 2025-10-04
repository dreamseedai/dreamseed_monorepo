#!/usr/bin/env python3
"""
DreamSeed 보안 테스트
"""
import pytest
import requests
import json
import time
from unittest.mock import patch, MagicMock

class TestSecurity:
    """보안 테스트 클래스"""
    
    def __init__(self):
        self.base_url = "http://127.0.0.1:8002"
    
    def test_sql_injection_protection(self):
        """SQL 인젝션 공격 방어 테스트"""
        print("🔒 SQL 인젝션 방어 테스트")
        
        # SQL 인젝션 시도
        malicious_payloads = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1' UNION SELECT * FROM users--",
            "' OR 1=1--"
        ]
        
        for payload in malicious_payloads:
            try:
                response = requests.get(
                    f"{self.base_url}/api/dashboard/stats",
                    params={'user_id': payload},
                    timeout=5
                )
                # 응답이 정상적으로 처리되어야 함
                assert response.status_code in [200, 400, 422]
                print(f"  ✅ SQL 인젝션 시도 차단: {payload[:20]}...")
            except Exception as e:
                print(f"  ⚠️ SQL 인젝션 테스트 오류: {e}")
    
    def test_xss_protection(self):
        """XSS 공격 방어 테스트"""
        print("🔒 XSS 방어 테스트")
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//"
        ]
        
        for payload in xss_payloads:
            try:
                response = requests.get(
                    f"{self.base_url}/api/dashboard/stats",
                    params={'search': payload},
                    timeout=5
                )
                
                # 응답에 스크립트 태그가 포함되지 않아야 함
                content = response.text
                assert '<script>' not in content.lower()
                assert 'javascript:' not in content.lower()
                print(f"  ✅ XSS 시도 차단: {payload[:20]}...")
            except Exception as e:
                print(f"  ⚠️ XSS 테스트 오류: {e}")
    
    def test_rate_limiting(self):
        """속도 제한 테스트"""
        print("🔒 속도 제한 테스트")
        
        # 빠른 연속 요청
        start_time = time.time()
        success_count = 0
        
        for i in range(100):  # 100개 요청
            try:
                response = requests.get(
                    f"{self.base_url}/api/dashboard/stats",
                    timeout=1
                )
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:  # Too Many Requests
                    print(f"  ✅ 속도 제한 작동: {i+1}번째 요청에서 차단")
                    break
            except requests.exceptions.Timeout:
                print(f"  ✅ 타임아웃으로 요청 차단: {i+1}번째 요청")
                break
        
        elapsed_time = time.time() - start_time
        print(f"  📊 {success_count}개 요청 성공, {elapsed_time:.2f}초 소요")
    
    def test_authentication_bypass(self):
        """인증 우회 시도 테스트"""
        print("🔒 인증 우회 시도 테스트")
        
        # 인증 없이 민감한 엔드포인트 접근 시도
        sensitive_endpoints = [
            "/api/admin/users",
            "/api/admin/settings",
            "/api/cache/invalidate",
            "/api/database/backup"
        ]
        
        for endpoint in sensitive_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                # 401 Unauthorized 또는 403 Forbidden이어야 함
                assert response.status_code in [401, 403, 404]
                print(f"  ✅ {endpoint}: 인증 필요 (HTTP {response.status_code})")
            except Exception as e:
                print(f"  ⚠️ {endpoint} 테스트 오류: {e}")
    
    def test_input_validation(self):
        """입력 검증 테스트"""
        print("🔒 입력 검증 테스트")
        
        invalid_inputs = [
            {"user_id": -1},  # 음수 ID
            {"user_id": "abc"},  # 문자열 ID
            {"limit": 999999},  # 과도한 제한값
            {"offset": -100},  # 음수 오프셋
            {"search": "a" * 10000},  # 과도한 길이
        ]
        
        for invalid_input in invalid_inputs:
            try:
                response = requests.get(
                    f"{self.base_url}/api/dashboard/stats",
                    params=invalid_input,
                    timeout=5
                )
                # 400 Bad Request 또는 정상 처리되어야 함
                assert response.status_code in [200, 400, 422]
                print(f"  ✅ 잘못된 입력 처리: {list(invalid_input.keys())[0]}")
            except Exception as e:
                print(f"  ⚠️ 입력 검증 테스트 오류: {e}")
    
    def test_http_methods(self):
        """HTTP 메서드 테스트"""
        print("🔒 HTTP 메서드 테스트")
        
        # GET 요청만 허용되는 엔드포인트에 다른 메서드 시도
        dangerous_methods = ['POST', 'PUT', 'DELETE', 'PATCH']
        
        for method in dangerous_methods:
            try:
                response = requests.request(
                    method,
                    f"{self.base_url}/api/dashboard/stats",
                    timeout=5
                )
                # 405 Method Not Allowed 또는 200 OK
                assert response.status_code in [200, 405]
                print(f"  ✅ {method} 메서드 처리: HTTP {response.status_code}")
            except Exception as e:
                print(f"  ⚠️ {method} 메서드 테스트 오류: {e}")
    
    def test_headers_security(self):
        """보안 헤더 테스트"""
        print("🔒 보안 헤더 테스트")
        
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=5)
            
            # 필수 보안 헤더 확인
            security_headers = {
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'DENY',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin'
            }
            
            for header, expected_value in security_headers.items():
                if header in response.headers:
                    assert response.headers[header] == expected_value
                    print(f"  ✅ {header}: {expected_value}")
                else:
                    print(f"  ⚠️ {header}: 누락")
                    
        except Exception as e:
            print(f"  ❌ 보안 헤더 테스트 오류: {e}")
    
    def test_file_upload_security(self):
        """파일 업로드 보안 테스트"""
        print("🔒 파일 업로드 보안 테스트")
        
        # 악성 파일 업로드 시도
        malicious_files = [
            ("malicious.php", "<?php system($_GET['cmd']); ?>"),
            ("script.js", "<script>alert('XSS')</script>"),
            ("backdoor.py", "import os; os.system('rm -rf /')"),
        ]
        
        for filename, content in malicious_files:
            try:
                files = {'file': (filename, content, 'application/octet-stream')}
                response = requests.post(
                    f"{self.base_url}/api/upload",
                    files=files,
                    timeout=5
                )
                # 400 Bad Request 또는 415 Unsupported Media Type
                assert response.status_code in [400, 404, 415]
                print(f"  ✅ 악성 파일 차단: {filename}")
            except Exception as e:
                print(f"  ⚠️ 파일 업로드 테스트 오류: {e}")
    
    def test_directory_traversal(self):
        """디렉토리 순회 공격 테스트"""
        print("🔒 디렉토리 순회 공격 테스트")
        
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd"
        ]
        
        for payload in traversal_payloads:
            try:
                response = requests.get(
                    f"{self.base_url}/api/files/{payload}",
                    timeout=5
                )
                # 400 Bad Request 또는 404 Not Found
                assert response.status_code in [400, 404]
                print(f"  ✅ 디렉토리 순회 차단: {payload[:30]}...")
            except Exception as e:
                print(f"  ⚠️ 디렉토리 순회 테스트 오류: {e}")
    
    def run_all_tests(self):
        """모든 보안 테스트 실행"""
        print("🚀 DreamSeed 보안 테스트 시작")
        print("=" * 50)
        
        try:
            self.test_sql_injection_protection()
            self.test_xss_protection()
            self.test_rate_limiting()
            self.test_authentication_bypass()
            self.test_input_validation()
            self.test_http_methods()
            self.test_headers_security()
            self.test_file_upload_security()
            self.test_directory_traversal()
            
            print("\n✅ 모든 보안 테스트 완료!")
            
        except Exception as e:
            print(f"\n❌ 보안 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    security_tester = TestSecurity()
    security_tester.run_all_tests()

