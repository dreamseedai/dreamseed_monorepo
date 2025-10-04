#!/usr/bin/env python3
"""
DreamSeed 부하 테스트 (Locust)
"""
from locust import HttpUser, task, between
import random

class DreamSeedUser(HttpUser):
    """DreamSeed 사용자 시뮬레이션"""
    
    wait_time = between(1, 3)  # 1-3초 대기
    
    def on_start(self):
        """사용자 시작 시 실행"""
        print("👤 사용자 세션 시작")
    
    @task(3)
    def check_health(self):
        """헬스체크 (가중치 3)"""
        with self.client.get("/healthz", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check failed: {response.status_code}")
    
    @task(5)
    def get_dashboard_stats(self):
        """대시보드 통계 조회 (가중치 5)"""
        with self.client.get("/api/dashboard/stats", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if 'total_users' in data and 'online_users' in data:
                    response.success()
                else:
                    response.failure("Invalid response data")
            else:
                response.failure(f"Stats request failed: {response.status_code}")
    
    @task(2)
    def get_user_growth(self):
        """사용자 증가 데이터 조회 (가중치 2)"""
        with self.client.get("/api/dashboard/user-growth", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if 'labels' in data and 'datasets' in data:
                    response.success()
                else:
                    response.failure("Invalid growth data")
            else:
                response.failure(f"Growth request failed: {response.status_code}")
    
    @task(2)
    def get_daily_activity(self):
        """일일 활동 데이터 조회 (가중치 2)"""
        with self.client.get("/api/dashboard/daily-activity", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if 'labels' in data and 'datasets' in data:
                    response.success()
                else:
                    response.failure("Invalid activity data")
            else:
                response.failure(f"Activity request failed: {response.status_code}")
    
    @task(1)
    def get_country_data(self):
        """국가별 데이터 조회 (가중치 1)"""
        with self.client.get("/api/dashboard/country-data", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    response.success()
                else:
                    response.failure("Invalid country data")
            else:
                response.failure(f"Country data request failed: {response.status_code}")
    
    @task(1)
    def get_recent_activities(self):
        """최근 활동 조회 (가중치 1)"""
        with self.client.get("/api/dashboard/recent-activities", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    response.success()
                else:
                    response.failure("Invalid activities data")
            else:
                response.failure(f"Activities request failed: {response.status_code}")
    
    @task(1)
    def get_cache_status(self):
        """캐시 상태 조회 (가중치 1)"""
        with self.client.get("/api/cache/status", catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                if 'status' in data:
                    response.success()
                else:
                    response.failure("Invalid cache status")
            else:
                response.failure(f"Cache status request failed: {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """메트릭 조회 (가중치 1)"""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                content = response.text
                if '# HELP' in content and '# TYPE' in content:
                    response.success()
                else:
                    response.failure("Invalid metrics format")
            else:
                response.failure(f"Metrics request failed: {response.status_code}")
    
    @task(1)
    def simulate_user_behavior(self):
        """사용자 행동 시뮬레이션 (가중치 1)"""
        # 랜덤하게 여러 엔드포인트 연속 호출
        endpoints = [
            "/api/dashboard/stats",
            "/api/dashboard/user-growth",
            "/api/dashboard/daily-activity"
        ]
        
        for endpoint in random.sample(endpoints, random.randint(1, 3)):
            with self.client.get(endpoint, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Behavior simulation failed: {response.status_code}")
    
    def on_stop(self):
        """사용자 종료 시 실행"""
        print("👋 사용자 세션 종료")

class AdminUser(HttpUser):
    """관리자 사용자 시뮬레이션"""
    
    wait_time = between(2, 5)  # 2-5초 대기
    
    def on_start(self):
        """관리자 세션 시작"""
        print("👨‍💼 관리자 세션 시작")
    
    @task(3)
    def check_system_health(self):
        """시스템 헬스체크"""
        with self.client.get("/healthz", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"System health check failed: {response.status_code}")
    
    @task(2)
    def get_detailed_stats(self):
        """상세 통계 조회"""
        with self.client.get("/api/dashboard/stats", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Detailed stats failed: {response.status_code}")
    
    @task(1)
    def check_cache_status(self):
        """캐시 상태 확인"""
        with self.client.get("/api/cache/status", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Cache status check failed: {response.status_code}")
    
    @task(1)
    def get_metrics(self):
        """메트릭 조회"""
        with self.client.get("/metrics", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Metrics check failed: {response.status_code}")
    
    def on_stop(self):
        """관리자 세션 종료"""
        print("👋 관리자 세션 종료")

