#!/usr/bin/env python3
"""
DreamSeed 로그 분석 시스템
"""
import json
import re
import sqlite3
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Tuple

class LogAnalyzer:
    def __init__(self, db_path="dreamseed_logs.db"):
        self.db_path = db_path
        self.init_log_db()
    
    def init_log_db(self):
        """로그 데이터베이스 초기화"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                service TEXT NOT NULL,
                message TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT UNIQUE NOT NULL,
                description TEXT,
                severity TEXT DEFAULT 'INFO',
                count INTEGER DEFAULT 0,
                last_seen TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                service TEXT NOT NULL,
                level TEXT NOT NULL,
                count INTEGER DEFAULT 0,
                avg_response_time REAL DEFAULT 0,
                error_rate REAL DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def parse_log_line(self, log_line: str) -> Optional[Dict]:
        """로그 라인 파싱"""
        # 다양한 로그 포맷 지원
        patterns = [
            # JSON 로그
            r'^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)\s+(\w+)\s+(\w+):\s+(.+)$',
            # 일반 로그
            r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+(\w+):\s+(.+)$',
            # Nginx 로그
            r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+-\s+-\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)\s+"([^"]+)"\s+"([^"]+)"$',
            # Apache 로그
            r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+-\s+-\s+\[([^\]]+)\]\s+"([^"]+)"\s+(\d+)\s+(\d+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, log_line.strip())
            if match:
                groups = match.groups()
                if len(groups) >= 4:
                    return {
                        'timestamp': groups[0],
                        'level': groups[1] if len(groups) > 1 else 'INFO',
                        'service': groups[2] if len(groups) > 2 else 'unknown',
                        'message': groups[3] if len(groups) > 3 else log_line,
                        'raw': log_line
                    }
        
        # 파싱 실패 시 기본값
        return {
            'timestamp': datetime.now().isoformat(),
            'level': 'UNKNOWN',
            'service': 'unknown',
            'message': log_line,
            'raw': log_line
        }
    
    def store_log_entry(self, log_data: Dict):
        """로그 엔트리 저장"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO log_entries (timestamp, level, service, message, metadata)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            log_data['timestamp'],
            log_data['level'],
            log_data['service'],
            log_data['message'],
            json.dumps(log_data.get('metadata', {}))
        ))
        
        conn.commit()
        conn.close()
    
    def analyze_logs(self, hours: int = 24) -> Dict:
        """로그 분석"""
        since = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 기본 통계
        cursor.execute('''
            SELECT 
                level,
                service,
                COUNT(*) as count
            FROM log_entries 
            WHERE timestamp > ?
            GROUP BY level, service
            ORDER BY count DESC
        ''', (since.isoformat(),))
        
        level_stats = defaultdict(lambda: defaultdict(int))
        for level, service, count in cursor.fetchall():
            level_stats[level][service] = count
        
        # 에러 패턴 분석
        cursor.execute('''
            SELECT message, COUNT(*) as count
            FROM log_entries 
            WHERE timestamp > ? AND level IN ('ERROR', 'CRITICAL', 'FATAL')
            GROUP BY message
            ORDER BY count DESC
            LIMIT 10
        ''', (since.isoformat(),))
        
        error_patterns = dict(cursor.fetchall())
        
        # 시간대별 로그 분포
        cursor.execute('''
            SELECT 
                strftime('%H', timestamp) as hour,
                COUNT(*) as count
            FROM log_entries 
            WHERE timestamp > ?
            GROUP BY hour
            ORDER BY hour
        ''', (since.isoformat(),))
        
        hourly_distribution = dict(cursor.fetchall())
        
        # 서비스별 응답 시간 (메시지에서 추출)
        cursor.execute('''
            SELECT service, message
            FROM log_entries 
            WHERE timestamp > ? AND message LIKE '%response_time%'
        ''', (since.isoformat(),))
        
        response_times = defaultdict(list)
        for service, message in cursor.fetchall():
            # 응답 시간 추출 (예: "response_time: 1.23s")
            match = re.search(r'response_time[:\s]+([\d.]+)', message)
            if match:
                response_times[service].append(float(match.group(1)))
        
        # 평균 응답 시간 계산
        avg_response_times = {}
        for service, times in response_times.items():
            if times:
                avg_response_times[service] = sum(times) / len(times)
        
        conn.close()
        
        return {
            'period_hours': hours,
            'level_stats': dict(level_stats),
            'error_patterns': error_patterns,
            'hourly_distribution': hourly_distribution,
            'avg_response_times': avg_response_times,
            'total_logs': sum(sum(service_counts.values()) for service_counts in level_stats.values())
        }
    
    def detect_anomalies(self, hours: int = 24) -> List[Dict]:
        """이상 패턴 감지"""
        since = datetime.now() - timedelta(hours=hours)
        anomalies = []
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 급격한 에러 증가 감지
        cursor.execute('''
            SELECT 
                service,
                strftime('%H', timestamp) as hour,
                COUNT(*) as error_count
            FROM log_entries 
            WHERE timestamp > ? AND level IN ('ERROR', 'CRITICAL', 'FATAL')
            GROUP BY service, hour
            HAVING error_count > 10
            ORDER BY error_count DESC
        ''', (since.isoformat(),))
        
        for service, hour, count in cursor.fetchall():
            anomalies.append({
                'type': 'HIGH_ERROR_RATE',
                'service': service,
                'hour': hour,
                'count': count,
                'severity': 'WARNING',
                'description': f'{service}에서 {hour}시에 {count}개의 에러가 발생했습니다.'
            })
        
        # 반복되는 에러 패턴 감지
        cursor.execute('''
            SELECT message, COUNT(*) as count
            FROM log_entries 
            WHERE timestamp > ? AND level IN ('ERROR', 'CRITICAL', 'FATAL')
            GROUP BY message
            HAVING count > 5
            ORDER BY count DESC
        ''', (since.isoformat(),))
        
        for message, count in cursor.fetchall():
            anomalies.append({
                'type': 'REPEATED_ERROR',
                'message': message[:100] + '...' if len(message) > 100 else message,
                'count': count,
                'severity': 'WARNING',
                'description': f'동일한 에러가 {count}번 반복되었습니다.'
            })
        
        # 서비스 다운 감지 (최근 1시간 로그 없음)
        cursor.execute('''
            SELECT DISTINCT service
            FROM log_entries 
            WHERE timestamp > ?
        ''', (since.isoformat(),))
        
        active_services = {row[0] for row in cursor.fetchall()}
        
        # 최근 1시간 로그가 있는 서비스 확인
        recent_since = datetime.now() - timedelta(hours=1)
        cursor.execute('''
            SELECT DISTINCT service
            FROM log_entries 
            WHERE timestamp > ?
        ''', (recent_since.isoformat(),))
        
        recent_services = {row[0] for row in cursor.fetchall()}
        
        for service in active_services:
            if service not in recent_services:
                anomalies.append({
                    'type': 'SERVICE_DOWN',
                    'service': service,
                    'severity': 'CRITICAL',
                    'description': f'{service} 서비스가 최근 1시간 동안 로그를 생성하지 않았습니다.'
                })
        
        conn.close()
        return anomalies
    
    def generate_report(self, hours: int = 24) -> str:
        """로그 분석 리포트 생성"""
        analysis = self.analyze_logs(hours)
        anomalies = self.detect_anomalies(hours)
        
        report = f"""
# DreamSeed 로그 분석 리포트

## 분석 기간
- 기간: 최근 {hours}시간
- 생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 전체 통계
- 총 로그 수: {analysis['total_logs']:,}개

## 로그 레벨별 분포
"""
        
        for level, services in analysis['level_stats'].items():
            total = sum(services.values())
            report += f"\n### {level} ({total:,}개)\n"
            for service, count in sorted(services.items(), key=lambda x: x[1], reverse=True):
                report += f"- {service}: {count:,}개\n"
        
        if analysis['error_patterns']:
            report += "\n## 주요 에러 패턴\n"
            for pattern, count in list(analysis['error_patterns'].items())[:5]:
                report += f"- {pattern[:80]}... ({count}회)\n"
        
        if analysis['avg_response_times']:
            report += "\n## 서비스별 평균 응답 시간\n"
            for service, avg_time in analysis['avg_response_times'].items():
                report += f"- {service}: {avg_time:.3f}초\n"
        
        if anomalies:
            report += "\n## 감지된 이상 패턴\n"
            for anomaly in anomalies:
                report += f"- **{anomaly['type']}** ({anomaly['severity']}): {anomaly['description']}\n"
        else:
            report += "\n## 이상 패턴\n- 감지된 이상 패턴이 없습니다.\n"
        
        return report
    
    def export_logs(self, hours: int = 24, format: str = "json") -> str:
        """로그 내보내기"""
        since = datetime.now() - timedelta(hours=hours)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT timestamp, level, service, message, metadata
            FROM log_entries 
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (since.isoformat(),))
        
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'timestamp': row[0],
                'level': row[1],
                'service': row[2],
                'message': row[3],
                'metadata': json.loads(row[4]) if row[4] else {}
            })
        
        conn.close()
        
        if format == "json":
            return json.dumps(logs, indent=2, ensure_ascii=False)
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=['timestamp', 'level', 'service', 'message'])
            writer.writeheader()
            for log in logs:
                writer.writerow({
                    'timestamp': log['timestamp'],
                    'level': log['level'],
                    'service': log['service'],
                    'message': log['message']
                })
            return output.getvalue()
        
        return ""

# 사용 예시
if __name__ == "__main__":
    analyzer = LogAnalyzer()
    
    # 샘플 로그 데이터 생성
    sample_logs = [
        "2025-10-03T15:00:00Z INFO dreamseed-api: User login successful",
        "2025-10-03T15:01:00Z ERROR dreamseed-api: Database connection failed",
        "2025-10-03T15:02:00Z WARNING dreamseed-api: High memory usage: 85%",
        "2025-10-03T15:03:00Z INFO dreamseed-api: response_time: 1.23s",
        "2025-10-03T15:04:00Z ERROR dreamseed-api: Database connection failed",
        "2025-10-03T15:05:00Z CRITICAL dreamseed-api: Service unavailable",
    ]
    
    # 로그 파싱 및 저장
    for log_line in sample_logs:
        log_data = analyzer.parse_log_line(log_line)
        if log_data:
            analyzer.store_log_entry(log_data)
    
    # 로그 분석
    analysis = analyzer.analyze_logs(24)
    print("로그 분석 결과:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
    
    # 이상 패턴 감지
    anomalies = analyzer.detect_anomalies(24)
    print("\n감지된 이상 패턴:")
    for anomaly in anomalies:
        print(f"- {anomaly['type']}: {anomaly['description']}")
    
    # 리포트 생성
    report = analyzer.generate_report(24)
    print("\n로그 분석 리포트:")
    print(report)

