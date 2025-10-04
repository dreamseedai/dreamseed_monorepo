#!/usr/bin/env python3
"""
DreamSeed API 단위 테스트
"""
import pytest
import json
import time
from unittest.mock import patch, MagicMock
import sys
import os

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.dashboard_data import app, get_realtime_stats, get_cached_data, set_cached_data

class TestDashboardAPI:
    """대시보드 API 테스트"""
    
    @pytest.fixture
    def client(self):
        """Flask 테스트 클라이언트"""
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_healthz_endpoint(self, client):
        """헬스체크 엔드포인트 테스트"""
        response = client.get('/healthz')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'timestamp' in data
        assert 'version' in data
    
    def test_metrics_endpoint(self, client):
        """메트릭 엔드포인트 테스트"""
        response = client.get('/metrics')
        assert response.status_code == 200
        assert 'text/plain' in response.content_type
        
        # Prometheus 메트릭 형식 확인
        content = response.data.decode('utf-8')
        assert '# HELP' in content
        assert '# TYPE' in content
    
    def test_dashboard_stats_endpoint(self, client):
        """대시보드 통계 엔드포인트 테스트"""
        response = client.get('/api/dashboard/stats')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'total_users' in data
        assert 'online_users' in data
        assert 'realtime_users' in data
    
    def test_user_growth_endpoint(self, client):
        """사용자 증가 엔드포인트 테스트"""
        response = client.get('/api/dashboard/user-growth')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'datasets' in data
        assert len(data['datasets']) > 0
    
    def test_daily_activity_endpoint(self, client):
        """일일 활동 엔드포인트 테스트"""
        response = client.get('/api/dashboard/daily-activity')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'labels' in data
        assert 'datasets' in data
    
    def test_country_data_endpoint(self, client):
        """국가별 데이터 엔드포인트 테스트"""
        response = client.get('/api/dashboard/country-data')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
        if data:  # 데이터가 있는 경우
            assert 'country' in data[0]
            assert 'users' in data[0]
    
    def test_recent_activities_endpoint(self, client):
        """최근 활동 엔드포인트 테스트"""
        response = client.get('/api/dashboard/recent-activities')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert isinstance(data, list)
    
    def test_cache_status_endpoint(self, client):
        """캐시 상태 엔드포인트 테스트"""
        response = client.get('/api/cache/status')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'status' in data
    
    @patch('api.dashboard_data.redis_client')
    def test_cache_invalidate_endpoint(self, mock_redis, client):
        """캐시 무효화 엔드포인트 테스트"""
        mock_redis.keys.return_value = ['dreamseed:test']
        mock_redis.delete.return_value = 1
        
        response = client.post('/api/cache/invalidate', 
                             json={'pattern': 'dreamseed:test'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'message' in data
    
    def test_invalid_endpoint(self, client):
        """존재하지 않는 엔드포인트 테스트"""
        response = client.get('/api/invalid-endpoint')
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """CORS 헤더 테스트"""
        response = client.get('/api/dashboard/stats')
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_security_headers(self, client):
        """보안 헤더 테스트"""
        response = client.get('/api/dashboard/stats')
        assert 'X-Content-Type-Options' in response.headers
        assert 'X-Frame-Options' in response.headers
        assert 'X-XSS-Protection' in response.headers

class TestDataFunctions:
    """데이터 함수 테스트"""
    
    @patch('api.dashboard_data.sqlite3.connect')
    def test_get_realtime_stats(self, mock_connect):
        """실시간 통계 함수 테스트"""
        # Mock 데이터베이스 연결
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock 쿼리 결과
        mock_cursor.fetchone.return_value = (100, 50, 10, 5, 2, 1)
        
        stats = get_realtime_stats()
        
        assert 'total_users' in stats
        assert 'online_users' in stats
        assert 'realtime_users' in stats
        assert isinstance(stats['total_users'], int)
    
    @patch('api.dashboard_data.redis_client')
    def test_cache_functions(self, mock_redis):
        """캐시 함수 테스트"""
        # Mock Redis 클라이언트
        mock_redis.get.return_value = '{"test": "data"}'
        mock_redis.setex.return_value = True
        
        # 캐시 조회 테스트
        cached_data = get_cached_data('test_key')
        assert cached_data == {"test": "data"}
        
        # 캐시 저장 테스트
        result = set_cached_data('test_key', {"test": "data"}, 300)
        assert result is None  # 성공 시 None 반환

class TestPerformance:
    """성능 테스트"""
    
    def test_response_time(self, client):
        """응답 시간 테스트"""
        start_time = time.time()
        response = client.get('/api/dashboard/stats')
        end_time = time.time()
        
        response_time = end_time - start_time
        assert response.status_code == 200
        assert response_time < 1.0  # 1초 이내 응답
    
    def test_concurrent_requests(self, client):
        """동시 요청 테스트"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = client.get('/api/dashboard/stats')
            results.put(response.status_code)
        
        # 10개의 동시 요청
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # 모든 스레드 완료 대기
        for thread in threads:
            thread.join()
        
        # 모든 요청이 성공했는지 확인
        while not results.empty():
            assert results.get() == 200

if __name__ == '__main__':
    pytest.main([__file__, '-v'])

