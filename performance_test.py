#!/usr/bin/env python3
"""
DreamSeed API 성능 테스트 스크립트
"""
import requests
import time
import statistics
import concurrent.futures
import json
from datetime import datetime

API_BASE = "http://127.0.0.1:8002"

def test_endpoint(endpoint, iterations=10):
    """단일 엔드포인트 성능 테스트"""
    print(f"\n🧪 {endpoint} 성능 테스트 ({iterations}회)")
    
    times = []
    errors = 0
    
    for i in range(iterations):
        start_time = time.time()
        try:
            response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                times.append(end_time - start_time)
            else:
                errors += 1
                print(f"  ❌ 요청 {i+1}: HTTP {response.status_code}")
        except Exception as e:
            errors += 1
            print(f"  ❌ 요청 {i+1}: {e}")
    
    if times:
        avg_time = statistics.mean(times)
        min_time = min(times)
        max_time = max(times)
        median_time = statistics.median(times)
        
        print(f"  ✅ 성공: {len(times)}/{iterations}")
        print(f"  📊 평균 응답시간: {avg_time:.3f}초")
        print(f"  📊 최소 응답시간: {min_time:.3f}초")
        print(f"  📊 최대 응답시간: {max_time:.3f}초")
        print(f"  📊 중간값: {median_time:.3f}초")
        
        return {
            'endpoint': endpoint,
            'success_rate': len(times) / iterations,
            'avg_time': avg_time,
            'min_time': min_time,
            'max_time': max_time,
            'median_time': median_time,
            'errors': errors
        }
    else:
        print(f"  ❌ 모든 요청 실패")
        return {
            'endpoint': endpoint,
            'success_rate': 0,
            'avg_time': 0,
            'min_time': 0,
            'max_time': 0,
            'median_time': 0,
            'errors': errors
        }

def test_concurrent_load(endpoint, concurrent_users=10, requests_per_user=5):
    """동시 사용자 부하 테스트"""
    print(f"\n🚀 {endpoint} 동시 부하 테스트 ({concurrent_users}명 × {requests_per_user}회)")
    
    def make_request():
        times = []
        for _ in range(requests_per_user):
            start_time = time.time()
            try:
                response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
                end_time = time.time()
                if response.status_code == 200:
                    times.append(end_time - start_time)
            except:
                pass
        return times
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrent_users) as executor:
        futures = [executor.submit(make_request) for _ in range(concurrent_users)]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    total_time = end_time - start_time
    
    all_times = []
    for result in results:
        all_times.extend(result)
    
    if all_times:
        total_requests = len(all_times)
        success_rate = total_requests / (concurrent_users * requests_per_user)
        rps = total_requests / total_time
        
        print(f"  ✅ 총 요청: {total_requests}")
        print(f"  ✅ 성공률: {success_rate:.2%}")
        print(f"  ✅ RPS: {rps:.2f}")
        print(f"  ✅ 총 시간: {total_time:.2f}초")
        print(f"  📊 평균 응답시간: {statistics.mean(all_times):.3f}초")
        
        return {
            'endpoint': endpoint,
            'concurrent_users': concurrent_users,
            'requests_per_user': requests_per_user,
            'total_requests': total_requests,
            'success_rate': success_rate,
            'rps': rps,
            'total_time': total_time,
            'avg_response_time': statistics.mean(all_times)
        }
    else:
        print(f"  ❌ 모든 요청 실패")
        return None

def test_cache_performance():
    """캐시 성능 테스트"""
    print(f"\n💾 캐시 성능 테스트")
    
    # 첫 번째 요청 (캐시 미스)
    start_time = time.time()
    response1 = requests.get(f"{API_BASE}/api/dashboard/stats")
    first_time = time.time() - start_time
    
    # 두 번째 요청 (캐시 히트)
    start_time = time.time()
    response2 = requests.get(f"{API_BASE}/api/dashboard/stats")
    second_time = time.time() - start_time
    
    print(f"  📊 첫 번째 요청 (캐시 미스): {first_time:.3f}초")
    print(f"  📊 두 번째 요청 (캐시 히트): {second_time:.3f}초")
    print(f"  📊 캐시 효과: {first_time/second_time:.1f}x 빨라짐")
    
    return {
        'cache_miss_time': first_time,
        'cache_hit_time': second_time,
        'cache_improvement': first_time / second_time
    }

def get_system_info():
    """시스템 정보 수집"""
    print(f"\n📊 시스템 정보")
    
    # Redis 정보
    try:
        cache_response = requests.get(f"{API_BASE}/api/cache/status")
        if cache_response.status_code == 200:
            cache_info = cache_response.json()
            print(f"  💾 Redis 상태: {cache_info.get('status', 'unknown')}")
            print(f"  💾 캐시된 키: {cache_info.get('cached_keys', 0)}")
            print(f"  💾 메모리 사용량: {cache_info.get('used_memory_human', 'unknown')}")
    except:
        print(f"  ❌ Redis 정보 수집 실패")
    
    # 헬스체크
    try:
        health_response = requests.get(f"{API_BASE}/healthz")
        if health_response.status_code == 200:
            health_info = health_response.json()
            print(f"  🏥 API 상태: {health_info.get('status', 'unknown')}")
            print(f"  🏥 캐시 상태: {health_info.get('cache', 'unknown')}")
    except:
        print(f"  ❌ 헬스체크 실패")

def main():
    """메인 테스트 실행"""
    print("🚀 DreamSeed API 성능 테스트 시작")
    print(f"⏰ 시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 시스템 정보
    get_system_info()
    
    # 테스트할 엔드포인트들
    endpoints = [
        "/healthz",
        "/api/dashboard/stats",
        "/api/dashboard/user-growth",
        "/api/dashboard/daily-activity",
        "/api/dashboard/country-data",
        "/api/dashboard/recent-activities"
    ]
    
    results = []
    
    # 개별 엔드포인트 테스트
    for endpoint in endpoints:
        result = test_endpoint(endpoint, iterations=5)
        results.append(result)
    
    # 캐시 성능 테스트
    cache_result = test_cache_performance()
    
    # 동시 부하 테스트 (stats 엔드포인트)
    load_result = test_concurrent_load("/api/dashboard/stats", concurrent_users=5, requests_per_user=3)
    
    # 결과 요약
    print(f"\n📋 테스트 결과 요약")
    print(f"{'엔드포인트':<30} {'성공률':<8} {'평균응답시간':<12} {'최대응답시간':<12}")
    print("-" * 70)
    
    for result in results:
        print(f"{result['endpoint']:<30} {result['success_rate']:<8.1%} {result['avg_time']:<12.3f} {result['max_time']:<12.3f}")
    
    if cache_result:
        print(f"\n💾 캐시 성능:")
        print(f"  캐시 미스: {cache_result['cache_miss_time']:.3f}초")
        print(f"  캐시 히트: {cache_result['cache_hit_time']:.3f}초")
        print(f"  성능 향상: {cache_result['cache_improvement']:.1f}x")
    
    if load_result:
        print(f"\n🚀 부하 테스트:")
        print(f"  총 요청: {load_result['total_requests']}")
        print(f"  성공률: {load_result['success_rate']:.1%}")
        print(f"  RPS: {load_result['rps']:.2f}")
        print(f"  평균 응답시간: {load_result['avg_response_time']:.3f}초")
    
    print(f"\n✅ 성능 테스트 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()

