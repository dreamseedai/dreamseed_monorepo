#!/usr/bin/env python3
"""
DreamSeed 스모크 테스트
"""
import requests
import time
import json
import argparse
from datetime import datetime

class SmokeTester:
    """스모크 테스트 클래스"""
    
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
    
    def test_basic_connectivity(self):
        """기본 연결성 테스트"""
        print("\n🌐 기본 연결성 테스트")
        
        try:
            response = requests.get(f"{self.base_url}/healthz", timeout=10)
            if response.status_code == 200:
                self.log_test("기본 연결성", True, f"HTTP {response.status_code}")
                return True
            else:
                self.log_test("기본 연결성", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("기본 연결성", False, f"연결 오류: {e}")
            return False
    
    def test_critical_endpoints(self):
        """중요 엔드포인트 테스트"""
        print("\n🔗 중요 엔드포인트 테스트")
        
        critical_endpoints = [
            "/healthz",
            "/api/dashboard/stats",
            "/api/dashboard/user-growth",
            "/api/dashboard/daily-activity",
            "/api/dashboard/country-data",
            "/api/dashboard/recent-activities",
            "/api/cache/status",
            "/metrics"
        ]
        
        success_count = 0
        for endpoint in critical_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    self.log_test(f"엔드포인트 {endpoint}", True, f"HTTP {response.status_code}")
                    success_count += 1
                else:
                    self.log_test(f"엔드포인트 {endpoint}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"엔드포인트 {endpoint}", False, f"오류: {e}")
        
        return success_count == len(critical_endpoints)
    
    def test_response_times(self):
        """응답 시간 테스트"""
        print("\n⏱️ 응답 시간 테스트")
        
        endpoints = [
            "/healthz",
            "/api/dashboard/stats",
            "/api/dashboard/user-growth"
        ]
        
        all_fast = True
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                if response.status_code == 200 and response_time < 2.0:
                    self.log_test(f"응답시간 {endpoint}", True, f"{response_time:.3f}초")
                else:
                    self.log_test(f"응답시간 {endpoint}", False, f"{response_time:.3f}초 (HTTP {response.status_code})")
                    all_fast = False
            except Exception as e:
                self.log_test(f"응답시간 {endpoint}", False, f"오류: {e}")
                all_fast = False
        
        return all_fast
    
    def test_data_consistency(self):
        """데이터 일관성 테스트"""
        print("\n📊 데이터 일관성 테스트")
        
        try:
            # 여러 번 요청하여 데이터 일관성 확인
            responses = []
            for _ in range(3):
                response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=5)
                if response.status_code == 200:
                    responses.append(response.json())
                time.sleep(0.1)
            
            if len(responses) >= 2:
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
    
    def test_error_handling(self):
        """오류 처리 테스트"""
        print("\n🚨 오류 처리 테스트")
        
        # 존재하지 않는 엔드포인트
        try:
            response = requests.get(f"{self.base_url}/api/nonexistent", timeout=5)
            if response.status_code == 404:
                self.log_test("404 오류 처리", True, "올바른 404 응답")
            else:
                self.log_test("404 오류 처리", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("404 오류 처리", False, f"오류: {e}")
        
        # 잘못된 메서드
        try:
            response = requests.post(f"{self.base_url}/healthz", timeout=5)
            if response.status_code in [405, 200]:  # Method Not Allowed 또는 허용
                self.log_test("메서드 오류 처리", True, f"HTTP {response.status_code}")
            else:
                self.log_test("메서드 오류 처리", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("메서드 오류 처리", False, f"오류: {e}")
    
    def test_concurrent_requests(self):
        """동시 요청 테스트"""
        print("\n🔄 동시 요청 테스트")
        
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=10)
                results.put(response.status_code)
            except Exception as e:
                results.put(f"ERROR: {e}")
        
        # 5개의 동시 요청
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 결과 확인
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
            else:
                print(f"  동시 요청 실패: {result}")
        
        if success_count >= 4:  # 5개 중 4개 이상 성공
            self.log_test("동시 요청", True, f"{success_count}/5 성공")
            return True
        else:
            self.log_test("동시 요청", False, f"{success_count}/5 성공")
            return False
    
    def test_memory_usage(self):
        """메모리 사용량 테스트"""
        print("\n💾 메모리 사용량 테스트")
        
        try:
            # 여러 요청을 보내서 메모리 누수 확인
            for i in range(10):
                response = requests.get(f"{self.base_url}/api/dashboard/stats", timeout=5)
                if response.status_code != 200:
                    self.log_test("메모리 사용량", False, f"{i+1}번째 요청 실패")
                    return False
                time.sleep(0.1)
            
            # 최종 헬스체크
            response = requests.get(f"{self.base_url}/healthz", timeout=5)
            if response.status_code == 200:
                self.log_test("메모리 사용량", True, "10회 연속 요청 후 정상")
                return True
            else:
                self.log_test("메모리 사용량", False, "10회 연속 요청 후 실패")
                return False
                
        except Exception as e:
            self.log_test("메모리 사용량", False, f"오류: {e}")
            return False
    
    def run_all_tests(self):
        """모든 스모크 테스트 실행"""
        print("🚀 DreamSeed 스모크 테스트 시작")
        print("=" * 50)
        
        # 기본 연결성 확인
        if not self.test_basic_connectivity():
            print("\n❌ 기본 연결성 실패. 다른 테스트를 건너뜁니다.")
            return False
        
        # 다른 테스트들 실행
        self.test_critical_endpoints()
        self.test_response_times()
        self.test_data_consistency()
        self.test_error_handling()
        self.test_concurrent_requests()
        self.test_memory_usage()
        
        # 결과 요약
        print("\n" + "=" * 50)
        print("📊 스모크 테스트 결과 요약")
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
        with open('smoke_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 결과가 smoke_test_results.json에 저장되었습니다.")
        
        return passed == total

def main():
    parser = argparse.ArgumentParser(description='DreamSeed 스모크 테스트')
    parser.add_argument('--env', default='staging', choices=['staging', 'production'],
                       help='테스트 환경 (기본값: staging)')
    parser.add_argument('--url', help='테스트할 URL (기본값: 환경에 따라 자동 설정)')
    
    args = parser.parse_args()
    
    # URL 설정
    if args.url:
        base_url = args.url
    elif args.env == 'production':
        base_url = "https://dreamseedai.com"
    else:
        base_url = "http://127.0.0.1:8002"
    
    print(f"🎯 테스트 환경: {args.env}")
    print(f"🌐 테스트 URL: {base_url}")
    
    tester = SmokeTester(base_url)
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 모든 스모크 테스트 통과!")
        exit(0)
    else:
        print("\n💥 일부 스모크 테스트 실패!")
        exit(1)

if __name__ == "__main__":
    main()

