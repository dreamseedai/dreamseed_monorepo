#!/usr/bin/env python3
"""
DreamSeed 헬스체크 및 자동 복구 시스템
"""
import requests
import subprocess
import time
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class HealthMonitor:
    def __init__(self, config_file="health_config.json"):
        self.config = self.load_config(config_file)
        self.health_db = "dreamseed_health.db"
        self.init_health_db()
    
    def load_config(self, config_file):
        """헬스체크 설정 로드"""
        default_config = {
            "services": {
                "dreamseed-api": {
                    "url": "http://127.0.0.1:8002/healthz",
                    "timeout": 5,
                    "retry_count": 3,
                    "check_interval": 30,
                    "auto_restart": True,
                    "restart_command": "sudo systemctl restart dreamseed-api"
                },
                "redis": {
                    "url": "http://127.0.0.1:6379",
                    "timeout": 5,
                    "retry_count": 3,
                    "check_interval": 60,
                    "auto_restart": True,
                    "restart_command": "sudo systemctl restart redis-server"
                },
                "nginx": {
                    "url": "http://127.0.0.1:80",
                    "timeout": 5,
                    "retry_count": 3,
                    "check_interval": 60,
                    "auto_restart": True,
                    "restart_command": "sudo systemctl restart nginx"
                }
            },
            "alerts": {
                "enabled": True,
                "email": "admin@dreamseed.com",
                "slack_webhook": ""
            },
            "recovery": {
                "max_restart_attempts": 3,
                "restart_cooldown": 300,  # 5분
                "escalation_delay": 1800  # 30분
            }
        }
        
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # 기본값과 병합
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
        except FileNotFoundError:
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def init_health_db(self):
        """헬스체크 데이터베이스 초기화"""
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                status TEXT NOT NULL,
                response_time REAL,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_restarts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                service_name TEXT NOT NULL,
                restart_time TEXT NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                attempt_count INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS service_status (
                service_name TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                last_check TEXT NOT NULL,
                consecutive_failures INTEGER DEFAULT 0,
                last_restart TEXT,
                restart_count INTEGER DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def check_service_health(self, service_name: str, service_config: Dict) -> Dict:
        """개별 서비스 헬스체크"""
        start_time = time.time()
        
        try:
            response = requests.get(
                service_config["url"],
                timeout=service_config["timeout"]
            )
            
            response_time = time.time() - start_time
            status = "healthy" if response.status_code == 200 else "unhealthy"
            
            result = {
                "service_name": service_name,
                "status": status,
                "response_time": response_time,
                "status_code": response.status_code,
                "error_message": None,
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.Timeout:
            result = {
                "service_name": service_name,
                "status": "timeout",
                "response_time": service_config["timeout"],
                "status_code": None,
                "error_message": "Request timeout",
                "timestamp": datetime.now().isoformat()
            }
            
        except requests.exceptions.ConnectionError:
            result = {
                "service_name": service_name,
                "status": "unreachable",
                "response_time": None,
                "status_code": None,
                "error_message": "Connection refused",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            result = {
                "service_name": service_name,
                "status": "error",
                "response_time": None,
                "status_code": None,
                "error_message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        
        # 결과 저장
        self.save_health_check(result)
        
        return result
    
    def save_health_check(self, result: Dict):
        """헬스체크 결과 저장"""
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO health_checks 
            (service_name, timestamp, status, response_time, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            result["service_name"],
            result["timestamp"],
            result["status"],
            result["response_time"],
            result["error_message"]
        ))
        
        # 서비스 상태 업데이트
        cursor.execute('''
            INSERT OR REPLACE INTO service_status 
            (service_name, status, last_check, consecutive_failures, last_restart, restart_count)
            VALUES (?, ?, ?, 
                CASE WHEN ? = 'healthy' THEN 0 ELSE 
                    (SELECT consecutive_failures + 1 FROM service_status WHERE service_name = ?)
                END,
                (SELECT last_restart FROM service_status WHERE service_name = ?),
                (SELECT restart_count FROM service_status WHERE service_name = ?)
            )
        ''', (
            result["service_name"],
            result["status"],
            result["timestamp"],
            result["status"],
            result["service_name"],
            result["service_name"],
            result["service_name"]
        ))
        
        conn.commit()
        conn.close()
    
    def restart_service(self, service_name: str, service_config: Dict) -> bool:
        """서비스 재시작"""
        if not service_config.get("auto_restart", False):
            return False
        
        restart_command = service_config.get("restart_command", "")
        if not restart_command:
            return False
        
        try:
            # 재시작 시도
            result = subprocess.run(
                restart_command.split(),
                capture_output=True,
                text=True,
                timeout=30
            )
            
            success = result.returncode == 0
            
            # 재시작 기록 저장
            self.save_restart_attempt(service_name, success, result.stderr)
            
            if success:
                # 서비스 상태 업데이트
                self.update_service_restart_status(service_name)
                print(f"✅ {service_name} 서비스 재시작 성공")
            else:
                print(f"❌ {service_name} 서비스 재시작 실패: {result.stderr}")
            
            return success
            
        except subprocess.TimeoutExpired:
            self.save_restart_attempt(service_name, False, "Restart command timeout")
            print(f"❌ {service_name} 서비스 재시작 타임아웃")
            return False
            
        except Exception as e:
            self.save_restart_attempt(service_name, False, str(e))
            print(f"❌ {service_name} 서비스 재시작 오류: {e}")
            return False
    
    def save_restart_attempt(self, service_name: str, success: bool, error_message: str = None):
        """재시작 시도 기록 저장"""
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        # 재시작 횟수 조회
        cursor.execute('''
            SELECT restart_count FROM service_status WHERE service_name = ?
        ''', (service_name,))
        
        result = cursor.fetchone()
        attempt_count = (result[0] + 1) if result else 1
        
        cursor.execute('''
            INSERT INTO service_restarts 
            (service_name, restart_time, success, error_message, attempt_count)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            service_name,
            datetime.now().isoformat(),
            success,
            error_message,
            attempt_count
        ))
        
        conn.commit()
        conn.close()
    
    def update_service_restart_status(self, service_name: str):
        """서비스 재시작 상태 업데이트"""
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE service_status 
            SET last_restart = ?, restart_count = restart_count + 1, consecutive_failures = 0
            WHERE service_name = ?
        ''', (datetime.now().isoformat(), service_name))
        
        conn.commit()
        conn.close()
    
    def should_restart_service(self, service_name: str) -> bool:
        """서비스 재시작 여부 판단"""
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT consecutive_failures, last_restart, restart_count
            FROM service_status 
            WHERE service_name = ?
        ''', (service_name,))
        
        result = cursor.fetchone()
        if not result:
            return False
        
        consecutive_failures, last_restart, restart_count = result
        
        # 연속 실패 횟수 확인
        if consecutive_failures < 3:
            return False
        
        # 최대 재시작 횟수 확인
        if restart_count >= self.config["recovery"]["max_restart_attempts"]:
            return False
        
        # 재시작 쿨다운 확인
        if last_restart:
            last_restart_time = datetime.fromisoformat(last_restart)
            cooldown = timedelta(seconds=self.config["recovery"]["restart_cooldown"])
            if datetime.now() - last_restart_time < cooldown:
                return False
        
        conn.close()
        return True
    
    def check_all_services(self) -> List[Dict]:
        """모든 서비스 헬스체크"""
        results = []
        
        for service_name, service_config in self.config["services"].items():
            print(f"🔍 {service_name} 헬스체크 중...")
            
            # 재시도 로직
            for attempt in range(service_config.get("retry_count", 1)):
                result = self.check_service_health(service_name, service_config)
                results.append(result)
                
                if result["status"] == "healthy":
                    print(f"✅ {service_name}: 정상")
                    break
                else:
                    print(f"⚠️ {service_name}: {result['status']} (시도 {attempt + 1}/{service_config.get('retry_count', 1)})")
                    if attempt < service_config.get("retry_count", 1) - 1:
                        time.sleep(2)  # 재시도 전 대기
            
            # 서비스 재시작 필요 여부 확인
            if result["status"] != "healthy" and self.should_restart_service(service_name):
                print(f"🔄 {service_name} 서비스 재시작 시도...")
                self.restart_service(service_name, service_config)
        
        return results
    
    def get_service_status(self) -> Dict:
        """서비스 상태 조회"""
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT service_name, status, last_check, consecutive_failures, restart_count
            FROM service_status
            ORDER BY service_name
        ''')
        
        services = {}
        for row in cursor.fetchall():
            services[row[0]] = {
                "status": row[1],
                "last_check": row[2],
                "consecutive_failures": row[3],
                "restart_count": row[4]
            }
        
        conn.close()
        return services
    
    def get_health_summary(self, hours: int = 24) -> Dict:
        """헬스체크 요약 정보"""
        since = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.health_db)
        cursor = conn.cursor()
        
        # 전체 통계
        cursor.execute('''
            SELECT 
                COUNT(*) as total_checks,
                SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_checks,
                AVG(response_time) as avg_response_time
            FROM health_checks 
            WHERE timestamp > ?
        ''', (since.isoformat(),))
        
        total_checks, healthy_checks, avg_response_time = cursor.fetchone()
        uptime_percentage = (healthy_checks / total_checks * 100) if total_checks > 0 else 0
        
        # 서비스별 통계
        cursor.execute('''
            SELECT 
                service_name,
                COUNT(*) as total_checks,
                SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_checks,
                AVG(response_time) as avg_response_time
            FROM health_checks 
            WHERE timestamp > ?
            GROUP BY service_name
        ''', (since.isoformat(),))
        
        service_stats = {}
        for row in cursor.fetchall():
            service_name, total, healthy, avg_time = row
            service_stats[service_name] = {
                "total_checks": total,
                "healthy_checks": healthy,
                "uptime_percentage": (healthy / total * 100) if total > 0 else 0,
                "avg_response_time": avg_time or 0
            }
        
        conn.close()
        
        return {
            "period_hours": hours,
            "total_checks": total_checks,
            "healthy_checks": healthy_checks,
            "uptime_percentage": uptime_percentage,
            "avg_response_time": avg_response_time or 0,
            "service_stats": service_stats
        }
    
    def start_monitoring(self):
        """헬스체크 모니터링 시작"""
        print("🚀 DreamSeed 헬스체크 모니터링 시작")
        
        while True:
            try:
                results = self.check_all_services()
                
                # 비정상 서비스 알림
                unhealthy_services = [r for r in results if r["status"] != "healthy"]
                if unhealthy_services and self.config["alerts"]["enabled"]:
                    self.send_alert(unhealthy_services)
                
                # 다음 체크까지 대기
                time.sleep(30)  # 30초마다 체크
                
            except KeyboardInterrupt:
                print("\n🛑 헬스체크 모니터링 중지")
                break
            except Exception as e:
                print(f"❌ 헬스체크 오류: {e}")
                time.sleep(60)  # 오류 시 1분 대기
    
    def send_alert(self, unhealthy_services: List[Dict]):
        """비정상 서비스 알림 전송"""
        # 실제 구현에서는 이메일, Slack 등으로 알림 전송
        print(f"🚨 비정상 서비스 감지: {[s['service_name'] for s in unhealthy_services]}")

# 사용 예시
if __name__ == "__main__":
    monitor = HealthMonitor()
    
    # 단일 헬스체크
    print("=== 단일 서비스 헬스체크 ===")
    api_config = monitor.config["services"]["dreamseed-api"]
    result = monitor.check_service_health("dreamseed-api", api_config)
    print(f"결과: {result}")
    
    # 모든 서비스 체크
    print("\n=== 모든 서비스 헬스체크 ===")
    results = monitor.check_all_services()
    for result in results:
        print(f"{result['service_name']}: {result['status']}")
    
    # 서비스 상태 조회
    print("\n=== 서비스 상태 ===")
    status = monitor.get_service_status()
    for service, info in status.items():
        print(f"{service}: {info['status']} (실패: {info['consecutive_failures']}회)")
    
    # 헬스체크 요약
    print("\n=== 헬스체크 요약 ===")
    summary = monitor.get_health_summary(24)
    print(f"가동률: {summary['uptime_percentage']:.1f}%")
    print(f"평균 응답시간: {summary['avg_response_time']:.3f}초")

