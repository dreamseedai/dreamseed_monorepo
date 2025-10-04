#!/usr/bin/env python3
"""
DreamSeed 모니터링 시스템 테스트
"""
import requests
import time
import json
from datetime import datetime

class MonitoringTester:
    def __init__(self):
        self.base_urls = {
            "api": "http://127.0.0.1:8002",
            "prometheus": "http://127.0.0.1:9090",
            "grafana": "http://127.0.0.1:3000",
            "node_exporter": "http://127.0.0.1:9100"
        }
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
    
    def test_api_health(self):
        """API 헬스체크 테스트"""
        print("\n🏥 API 헬스체크 테스트")
        
        try:
            response = requests.get(f"{self.base_urls['api']}/healthz", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.log_test("API 헬스체크", True, f"상태: {data.get('status')}")
            else:
                self.log_test("API 헬스체크", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("API 헬스체크", False, f"연결 오류: {e}")
    
    def test_api_metrics(self):
        """API 메트릭 엔드포인트 테스트"""
        try:
            response = requests.get(f"{self.base_urls['api']}/metrics", timeout=5)
            if response.status_code == 200:
                metrics_text = response.text
                if "http_requests_total" in metrics_text and "dreamseed_active_users" in metrics_text:
                    self.log_test("API 메트릭", True, "Prometheus 메트릭 정상")
                else:
                    self.log_test("API 메트릭", False, "메트릭 데이터 부족")
            else:
                self.log_test("API 메트릭", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("API 메트릭", False, f"연결 오류: {e}")
    
    def test_prometheus_status(self):
        """Prometheus 상태 테스트"""
        print("\n📊 Prometheus 상태 테스트")
        
        try:
            response = requests.get(f"{self.base_urls['prometheus']}/api/v1/status/config", timeout=5)
            if response.status_code == 200:
                self.log_test("Prometheus 상태", True, "정상 작동")
            else:
                self.log_test("Prometheus 상태", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Prometheus 상태", False, f"연결 오류: {e}")
    
    def test_prometheus_targets(self):
        """Prometheus 타겟 테스트"""
        try:
            response = requests.get(f"{self.base_urls['prometheus']}/api/v1/targets", timeout=5)
            if response.status_code == 200:
                data = response.json()
                active_targets = data.get('data', {}).get('activeTargets', [])
                
                if active_targets:
                    healthy_count = sum(1 for target in active_targets if target.get('health') == 'up')
                    self.log_test("Prometheus 타겟", True, f"{healthy_count}/{len(active_targets)} 타겟 정상")
                else:
                    self.log_test("Prometheus 타겟", False, "타겟 없음")
            else:
                self.log_test("Prometheus 타겟", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Prometheus 타겟", False, f"연결 오류: {e}")
    
    def test_grafana_status(self):
        """Grafana 상태 테스트"""
        print("\n📈 Grafana 상태 테스트")
        
        try:
            response = requests.get(f"{self.base_urls['grafana']}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get('database') == 'ok':
                    self.log_test("Grafana 상태", True, "정상 작동")
                else:
                    self.log_test("Grafana 상태", False, f"데이터베이스: {data.get('database')}")
            else:
                self.log_test("Grafana 상태", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Grafana 상태", False, f"연결 오류: {e}")
    
    def test_node_exporter(self):
        """Node Exporter 테스트"""
        print("\n🖥️ Node Exporter 테스트")
        
        try:
            response = requests.get(f"{self.base_urls['node_exporter']}/metrics", timeout=5)
            if response.status_code == 200:
                metrics_text = response.text
                if "node_cpu_seconds_total" in metrics_text and "node_memory_MemTotal_bytes" in metrics_text:
                    self.log_test("Node Exporter", True, "시스템 메트릭 정상")
                else:
                    self.log_test("Node Exporter", False, "메트릭 데이터 부족")
            else:
                self.log_test("Node Exporter", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Node Exporter", False, f"연결 오류: {e}")
    
    def test_api_performance(self):
        """API 성능 테스트"""
        print("\n⚡ API 성능 테스트")
        
        endpoints = [
            "/healthz",
            "/api/dashboard/stats",
            "/api/dashboard/user-growth",
            "/api/cache/status"
        ]
        
        for endpoint in endpoints:
            try:
                start_time = time.time()
                response = requests.get(f"{self.base_urls['api']}{endpoint}", timeout=10)
                end_time = time.time()
                
                response_time = end_time - start_time
                
                if response.status_code == 200:
                    if response_time < 1.0:
                        self.log_test(f"API 성능 {endpoint}", True, f"{response_time:.3f}초")
                    else:
                        self.log_test(f"API 성능 {endpoint}", False, f"느린 응답: {response_time:.3f}초")
                else:
                    self.log_test(f"API 성능 {endpoint}", False, f"HTTP {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"API 성능 {endpoint}", False, f"오류: {e}")
    
    def test_metrics_collection(self):
        """메트릭 수집 테스트"""
        print("\n📊 메트릭 수집 테스트")
        
        # API 요청을 여러 번 보내서 메트릭 생성
        for i in range(5):
            try:
                requests.get(f"{self.base_urls['api']}/api/dashboard/stats", timeout=5)
                time.sleep(0.1)
            except:
                pass
        
        # 메트릭 확인
        try:
            response = requests.get(f"{self.base_urls['api']}/metrics", timeout=5)
            if response.status_code == 200:
                metrics_text = response.text
                
                # 특정 메트릭 확인
                metrics_to_check = [
                    "http_requests_total",
                    "http_request_duration_seconds",
                    "dreamseed_active_users",
                    "dreamseed_cache_hits_total",
                    "dreamseed_cache_misses_total"
                ]
                
                found_metrics = []
                for metric in metrics_to_check:
                    if metric in metrics_text:
                        found_metrics.append(metric)
                
                if len(found_metrics) >= 3:
                    self.log_test("메트릭 수집", True, f"{len(found_metrics)}개 메트릭 확인")
                else:
                    self.log_test("메트릭 수집", False, f"메트릭 부족: {found_metrics}")
            else:
                self.log_test("메트릭 수집", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("메트릭 수집", False, f"오류: {e}")
    
    def test_alert_system(self):
        """알림 시스템 테스트"""
        print("\n🚨 알림 시스템 테스트")
        
        try:
            from alert_manager import AlertManager
            alert_manager = AlertManager()
            
            # 테스트 알림 전송
            success, total = alert_manager.send_alert(
                "모니터링 테스트",
                "DreamSeed 모니터링 시스템이 정상적으로 작동하고 있습니다.",
                "INFO"
            )
            
            if success > 0:
                self.log_test("알림 시스템", True, f"{success}/{total} 채널 성공")
            else:
                self.log_test("알림 시스템", False, "알림 전송 실패")
                
        except Exception as e:
            self.log_test("알림 시스템", False, f"오류: {e}")
    
    def test_health_monitoring(self):
        """헬스체크 모니터링 테스트"""
        print("\n💓 헬스체크 모니터링 테스트")
        
        try:
            from health_monitor import HealthMonitor
            monitor = HealthMonitor()
            
            # 서비스 상태 확인
            status = monitor.get_service_status()
            
            if status:
                healthy_services = sum(1 for s in status.values() if s['status'] == 'healthy')
                total_services = len(status)
                
                if healthy_services > 0:
                    self.log_test("헬스체크 모니터링", True, f"{healthy_services}/{total_services} 서비스 정상")
                else:
                    self.log_test("헬스체크 모니터링", False, "정상 서비스 없음")
            else:
                self.log_test("헬스체크 모니터링", False, "서비스 상태 없음")
                
        except Exception as e:
            self.log_test("헬스체크 모니터링", False, f"오류: {e}")
    
    def test_log_analysis(self):
        """로그 분석 테스트"""
        print("\n📝 로그 분석 테스트")
        
        try:
            from log_analyzer import LogAnalyzer
            analyzer = LogAnalyzer()
            
            # 샘플 로그 생성
            sample_logs = [
                "2025-10-03T15:00:00Z INFO dreamseed-api: Test log message",
                "2025-10-03T15:01:00Z ERROR dreamseed-api: Test error message",
                "2025-10-03T15:02:00Z WARNING dreamseed-api: Test warning message"
            ]
            
            for log_line in sample_logs:
                log_data = analyzer.parse_log_line(log_line)
                if log_data:
                    analyzer.store_log_entry(log_data)
            
            # 로그 분석
            analysis = analyzer.analyze_logs(1)  # 최근 1시간
            
            if analysis and analysis.get('total_logs', 0) > 0:
                self.log_test("로그 분석", True, f"{analysis['total_logs']}개 로그 분석 완료")
            else:
                self.log_test("로그 분석", False, "로그 분석 실패")
                
        except Exception as e:
            self.log_test("로그 분석", False, f"오류: {e}")
    
    def run_all_tests(self):
        """모든 테스트 실행"""
        print("🚀 DreamSeed 모니터링 시스템 테스트 시작")
        print("=" * 60)
        
        self.test_api_health()
        self.test_api_metrics()
        self.test_prometheus_status()
        self.test_prometheus_targets()
        self.test_grafana_status()
        self.test_node_exporter()
        self.test_api_performance()
        self.test_metrics_collection()
        self.test_alert_system()
        self.test_health_monitoring()
        self.test_log_analysis()
        
        # 결과 요약
        print("\n" + "=" * 60)
        print("📊 모니터링 시스템 테스트 결과 요약")
        print("=" * 60)
        
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
        with open('monitoring_test_results.json', 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 결과가 monitoring_test_results.json에 저장되었습니다.")
        
        return self.test_results

if __name__ == "__main__":
    tester = MonitoringTester()
    results = tester.run_all_tests()

