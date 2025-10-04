#!/usr/bin/env python3
"""
DreamSeed 보안 모니터링 시스템
"""
import json
import time
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SecurityMonitor:
    def __init__(self, db_path="dreamseed_security.db"):
        self.db_path = db_path
        self.init_security_db()
        
        # 실시간 모니터링 데이터
        self.failed_attempts = defaultdict(int)
        self.suspicious_ips = set()
        self.rate_limits = defaultdict(lambda: deque())
        
        # 알림 설정
        self.alert_thresholds = {
            'failed_auth': 5,      # 5회 실패 시 알림
            'rate_limit': 100,     # 1시간에 100회 요청 시 알림
            'suspicious_pattern': 3 # 3회 의심스러운 패턴 시 알림
        }
        
        # 모니터링 시작
        self.start_monitoring()
    
    def init_security_db(self):
        """보안 이벤트 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                client_ip TEXT NOT NULL,
                user_agent TEXT,
                endpoint TEXT,
                details TEXT,
                severity TEXT DEFAULT 'INFO',
                resolved BOOLEAN DEFAULT FALSE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocked_ips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT UNIQUE NOT NULL,
                reason TEXT NOT NULL,
                blocked_at TEXT NOT NULL,
                expires_at TEXT,
                is_active BOOLEAN DEFAULT TRUE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS security_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_type TEXT NOT NULL,
                message TEXT NOT NULL,
                severity TEXT NOT NULL,
                created_at TEXT NOT NULL,
                acknowledged BOOLEAN DEFAULT FALSE,
                acknowledged_by TEXT,
                acknowledged_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_security_event(self, event_type, client_ip, user_agent=None, endpoint=None, details=None, severity='INFO'):
        """보안 이벤트 로깅"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_events 
            (timestamp, event_type, client_ip, user_agent, endpoint, details, severity)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            event_type,
            client_ip,
            user_agent,
            endpoint,
            json.dumps(details) if details else None,
            severity
        ))
        
        conn.commit()
        conn.close()
        
        # 실시간 모니터링 업데이트
        self.update_realtime_monitoring(event_type, client_ip)
    
    def update_realtime_monitoring(self, event_type, client_ip):
        """실시간 모니터링 데이터 업데이트"""
        current_time = time.time()
        
        if event_type == 'FAILED_AUTH':
            self.failed_attempts[client_ip] += 1
            
            # 실패 횟수 임계값 확인
            if self.failed_attempts[client_ip] >= self.alert_thresholds['failed_auth']:
                self.create_security_alert(
                    'HIGH_FAILED_AUTH',
                    f'IP {client_ip}에서 {self.failed_attempts[client_ip]}회 인증 실패',
                    'HIGH'
                )
                self.block_ip(client_ip, 'Multiple failed authentication attempts')
        
        elif event_type == 'RATE_LIMIT_EXCEEDED':
            self.rate_limits[client_ip].append(current_time)
            
            # 1시간 내 요청 수 확인
            hour_ago = current_time - 3600
            recent_requests = [req_time for req_time in self.rate_limits[client_ip] if req_time > hour_ago]
            
            if len(recent_requests) >= self.alert_thresholds['rate_limit']:
                self.create_security_alert(
                    'HIGH_RATE_LIMIT',
                    f'IP {client_ip}에서 1시간 내 {len(recent_requests)}회 요청 (임계값 초과)',
                    'MEDIUM'
                )
        
        elif event_type == 'SUSPICIOUS_ACTIVITY':
            self.suspicious_ips.add(client_ip)
            
            # 의심스러운 IP 임계값 확인
            if len(self.suspicious_ips) >= self.alert_thresholds['suspicious_pattern']:
                self.create_security_alert(
                    'SUSPICIOUS_PATTERN',
                    f'IP {client_ip}에서 의심스러운 활동 패턴 감지',
                    'MEDIUM'
                )
    
    def create_security_alert(self, alert_type, message, severity):
        """보안 알림 생성"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO security_alerts (alert_type, message, severity, created_at)
            VALUES (?, ?, ?, ?)
        ''', (alert_type, message, severity, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        # 콘솔에 알림 출력
        print(f"🚨 SECURITY ALERT [{severity}]: {message}")
        
        # 이메일 알림 (설정된 경우)
        self.send_email_alert(alert_type, message, severity)
    
    def block_ip(self, ip_address, reason, duration_hours=24):
        """IP 주소 차단"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=duration_hours)
        
        cursor.execute('''
            INSERT OR REPLACE INTO blocked_ips 
            (ip_address, reason, blocked_at, expires_at, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (ip_address, reason, datetime.now().isoformat(), expires_at.isoformat(), True))
        
        conn.commit()
        conn.close()
        
        print(f"🚫 IP {ip_address} 차단됨: {reason}")
    
    def is_ip_blocked(self, ip_address):
        """IP 주소 차단 여부 확인"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM blocked_ips 
            WHERE ip_address = ? AND is_active = TRUE 
            AND (expires_at IS NULL OR expires_at > ?)
        ''', (ip_address, datetime.now().isoformat()))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def get_security_stats(self, hours=24):
        """보안 통계 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        # 이벤트 유형별 통계
        cursor.execute('''
            SELECT event_type, COUNT(*) as count
            FROM security_events 
            WHERE timestamp > ?
            GROUP BY event_type
        ''', (since.isoformat(),))
        
        event_stats = dict(cursor.fetchall())
        
        # 심각도별 통계
        cursor.execute('''
            SELECT severity, COUNT(*) as count
            FROM security_events 
            WHERE timestamp > ?
            GROUP BY severity
        ''', (since.isoformat(),))
        
        severity_stats = dict(cursor.fetchall())
        
        # 활성 알림 수
        cursor.execute('''
            SELECT COUNT(*) FROM security_alerts 
            WHERE acknowledged = FALSE
        ''')
        
        active_alerts = cursor.fetchone()[0]
        
        # 차단된 IP 수
        cursor.execute('''
            SELECT COUNT(*) FROM blocked_ips 
            WHERE is_active = TRUE
        ''')
        
        blocked_ips = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'event_stats': event_stats,
            'severity_stats': severity_stats,
            'active_alerts': active_alerts,
            'blocked_ips': blocked_ips,
            'period_hours': hours
        }
    
    def send_email_alert(self, alert_type, message, severity):
        """이메일 알림 전송 (설정된 경우)"""
        # 실제 운영에서는 SMTP 설정 필요
        # 여기서는 로그만 출력
        print(f"📧 EMAIL ALERT [{severity}]: {alert_type} - {message}")
    
    def start_monitoring(self):
        """모니터링 시작"""
        def cleanup_old_data():
            while True:
                time.sleep(3600)  # 1시간마다 실행
                self.cleanup_old_data()
        
        cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
        cleanup_thread.start()
    
    def cleanup_old_data(self):
        """오래된 데이터 정리"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 30일 이상 된 보안 이벤트 삭제
        thirty_days_ago = datetime.now() - timedelta(days=30)
        cursor.execute('''
            DELETE FROM security_events 
            WHERE timestamp < ?
        ''', (thirty_days_ago.isoformat(),))
        
        # 만료된 IP 차단 해제
        cursor.execute('''
            UPDATE blocked_ips 
            SET is_active = FALSE 
            WHERE expires_at < ? AND is_active = TRUE
        ''', (datetime.now().isoformat(),))
        
        conn.commit()
        conn.close()
    
    def get_security_dashboard_data(self):
        """보안 대시보드 데이터"""
        stats = self.get_security_stats(24)
        
        return {
            'total_events': sum(stats['event_stats'].values()),
            'high_severity_events': stats['severity_stats'].get('HIGH', 0),
            'active_alerts': stats['active_alerts'],
            'blocked_ips': stats['blocked_ips'],
            'top_event_types': sorted(stats['event_stats'].items(), key=lambda x: x[1], reverse=True)[:5],
            'recent_events': self.get_recent_events(10)
        }
    
    def get_recent_events(self, limit=10):
        """최근 보안 이벤트 조회"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, event_type, client_ip, severity, details
            FROM security_events 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (limit,))
        
        events = []
        for row in cursor.fetchall():
            events.append({
                'timestamp': row[0],
                'event_type': row[1],
                'client_ip': row[2],
                'severity': row[3],
                'details': json.loads(row[4]) if row[4] else None
            })
        
        conn.close()
        return events

# 전역 보안 모니터 인스턴스
security_monitor = SecurityMonitor()

# 사용 예시
if __name__ == "__main__":
    # 보안 이벤트 로깅 테스트
    security_monitor.log_security_event(
        'FAILED_AUTH',
        '192.168.1.100',
        'Mozilla/5.0...',
        '/api/dashboard/stats',
        {'attempts': 3},
        'WARNING'
    )
    
    # 보안 통계 조회
    stats = security_monitor.get_security_stats(24)
    print("보안 통계:", stats)
    
    # 대시보드 데이터
    dashboard_data = security_monitor.get_security_dashboard_data()
    print("대시보드 데이터:", dashboard_data)

