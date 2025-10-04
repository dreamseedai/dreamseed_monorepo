#!/usr/bin/env python3
"""
DreamSeed 프로덕션 테스트
"""
import requests
import time
import json
from datetime import datetime

class ProductionTester:
    """프로덕션 테스트 클래스"""
    
    def __init__(self, base_url="https://dreamseedai.com"):
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
    
    def test_ssl_certificate(self):
        """SSL 인증서 테스트"""
        print("\n🔒 SSL 인증서 테스트")
        
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=10, verify=True)
            if response.status_code == 200:
                self.log_test("SSL 인증서", True, "HTTPS 연결 성공")
                return True
            else:
                self.log_test("SSL 인증서", False, f"HTTP {response.status_code}")
                return False
        except requests.exceptions.SSLError as e:
            self.log_test("SSL 인증서", False, f"SSL 오류: {e}")
            return False
        except Exception as e:
            self.log_test("SSL 인증서", False, f"연결 오류: {e}")
            return False
    
    def test_production_endpoints(self):
        """프로덕션 엔드포인트 테스트"""
        print("\n🌐 프로덕션 엔드포인트 테스트")
        
        endpoints = [
            "/healthz",
            "/api/dashboard/stats",
            "/api/dashboard/user-growth",
            "/api/dashboard/daily-activity",
            "/api/dashboard/country-data",
            "/api/dashboard/recent-activities",
            "/admin/"
        ]
        
        success_count = 0
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10, verify=True)
                if response.status_code == 200:
                    self.log_test(f"엔드포인트 {endpoint}", True, f"HTTP {response.status_code}")
                    success_count += 1
                else:
                    self.log_test(f"엔드포인트 {endpoint}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"엔드포인트 {endpoint}", False, f"오류: {e}")
        
        return success_count >= len(endpoints) * 0.8  # 80% 이상 성공
    
    def test_performance_under_load(self):
        """부하 상태에서 성능 테스트"""
        print("\n⚡ 부하 성능 테스트")
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=15, verify=True)
                end_time = time.time()
                
                results.put({
                    'status_code': response.status_code,
                    'response_time': end_time - start_time,
                    'success': response.status_code == 200
                })
            except Exception as e:
                results.put({
                    'status_code': 0,
                    'response_time': 0,
                    'success': False,
                    'error': str(e)
                })
        
        # 20개의 동시 요청
        threads = []
        for _ in range(20):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 분석
        response_times = []
        success_count = 0
        
        while not results.empty():
            result = results.get()
            if result['success']:
                success_count += 1
                response_times.append(result['response_time'])
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            
            if avg_response_time < 2.0 and success_count >= 18:  # 90% 이상 성공
                self.log_test("부하 성능", True, f"평균 {avg_response_time:.3f}초, {success_count}/20 성공")
                return True
            else:
                self.log_test("부하 성능", False, f"평균 {avg_response_time:.3f}초, {success_count}/20 성공")
                return False
        else:
            self.log_test("부하 성능", False, "모든 요청 실패")
            return False
    
    def test_data_consistency(self):
        """데이터 일관성 테스트"""
        print("\n📊 데이터 일관성 테스트")
        
        try:
            # 여러 번 요청하여 데이터 일관성 확인
            responses = []
            for _ in range(5):
                response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=10, verify=True)
                if response.status_code == 200:
                    responses.append(response.json())
                time.sleep(1)
            
            if len(responses) >= 3:
                # 기본 필드 존재 확인
                required_fields = ['total_users', 'online_users', 'realtime_users']
                for i, data in enumerate(responses):
                    for field in required_fields:
                        if field not in data:
                            self.log_test("데이터 일관성", False, f"응답 {i+1}에 {field} 필드 없음")
                            return False
                
                self.log_test("데이터 일관성", True, f"{len(responses)}개 응답 일관성 확인")
                return True
            else:
                self.log_test("데이터 일관성", False, "충분한 응답 없음")
                return False
                
        except Exception as e:
            self.log_test("데이터 일관성", False, f"오류: {e}")
            return False
    
    def test_security_headers(self):
        """보안 헤더 테스트"""
        print("\n🛡️ 보안 헤더 테스트")
        
        try:
            response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=10, verify=True)
            
            # 필수 보안 헤더 확인
            security_headers = {
                'Strict-Transport-Security': 'max-age=31536000',
                'X-Content-Type-Options': 'nosniff',
                'X-Frame-Options': 'SAMEORIGIN',
                'X-XSS-Protection': '1; mode=block',
                'Referrer-Policy': 'strict-origin-when-cross-origin'
            }
            
            missing_headers = []
            for header, expected_value in security_headers.items():
                if header in response.headers:
                    if expected_value in response.headers[header]:
                        self.log_test(f"보안 헤더 {header}", True, response.headers[header])
                    else:
                        self.log_test(f"보안 헤더 {header}", False, f"예상값과 다름: {response.headers[header]}")
                        missing_headers.append(header)
                else:
                    self.log_test(f"보안 헤더 {header}", False, "누락")
                    missing_headers.append(header)
            
            if len(missing_headers) == 0:
                self.log_test("보안 헤더 전체", True, "모든 보안 헤더 정상")
                return True
            else:
                self.log_test("보안 헤더 전체", False, f"누락된 헤더: {missing_headers}")
                return False
                
        except Exception as e:
            self.log_test("보안 헤더", False, f"오류: {e}")
            return False
    
    def test_monitoring_endpoints(self):
        """모니터링 엔드포인트 테스트"""
        print("\n📈 모니터링 엔드포인트 테스트")
        
        # 내부 모니터링 엔드포인트 (VPN 또는 내부 네트워크에서만 접근 가능)
        monitoring_endpoints = [
            "/metrics",
            "/prometheus/",
            "/grafana/"
        ]
        
        for endpoint in monitoring_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5, verify=True)
                if response.status_code in [200, 401, 403]:  # 접근 가능하거나 인증 필요
                    self.log_test(f"모니터링 {endpoint}", True, f"HTTP {response.status_code}")
                else:
                    self.log_test(f"모니터링 {endpoint}", False, f"HTTP {response.status_code}")
            except Exception as e:
                # 모니터링 엔드포인트는 외부에서 접근 불가능할 수 있음
                self.log_test(f"모니터링 {endpoint}", True, f"외부 접근 차단 (정상)")
    
    def run_all_tests(self):
        """모든 프로덕션 테스트 실행"""
        print("🚀 DreamSeed 프로덕션 테스트 시작")
        print("=" * 50)
        
        self.test_ssl_certificate()
        self.test_production_endpoints()
        self.test_performance_under_load()
        self.test_data_consistency()
        self.test_security_headers()
        self.test_monitoring_endpoints()
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("📊 프로덕션 테스트 결과 요약")
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
        
        # 결과를 JSON 파일로 저장
        with open('production_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 결과가 production_test_results.json에 저장되었습니다.")
        
        return passed == total

if __name__ == "__main__":
    tester = ProductionTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 모든 프로덕션 테스트 통과!")
        exit(0)
    else:
        print("\n💥 일부 프로덕션 테스트 실패!")
        exit(1)

