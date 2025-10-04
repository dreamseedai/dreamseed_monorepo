#!/usr/bin/env python3
"""
DreamSeed 알림 관리 시스템
"""
import json
import smtplib
import requests
import time
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

class AlertManager:
    def __init__(self, config_file="alert_config.json"):
        self.config = self.load_config(config_file)
        self.alert_history = []
    
    def load_config(self, config_file):
        """알림 설정 로드"""
        default_config = {
            "email": {
                "enabled": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "",
                "password": "",
                "from_email": "dreamseed@example.com",
                "to_emails": ["admin@dreamseed.com"]
            },
            "slack": {
                "enabled": False,
                "webhook_url": "",
                "channel": "#alerts",
                "username": "DreamSeed Bot"
            },
            "webhook": {
                "enabled": False,
                "url": "",
                "headers": {"Content-Type": "application/json"}
            },
            "thresholds": {
                "cpu_usage": 80,
                "memory_usage": 90,
                "disk_usage": 85,
                "response_time": 2.0,
                "error_rate": 5.0
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
            # 설정 파일이 없으면 기본값 저장
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            return default_config
    
    def send_email_alert(self, subject: str, message: str, severity: str = "INFO"):
        """이메일 알림 전송"""
        if not self.config["email"]["enabled"]:
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.config["email"]["from_email"]
            msg['To'] = ", ".join(self.config["email"]["to_emails"])
            msg['Subject'] = f"[{severity}] {subject}"
            
            body = f"""
DreamSeed 시스템 알림

심각도: {severity}
시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

내용:
{message}

---
DreamSeed 모니터링 시스템
            """
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(
                self.config["email"]["smtp_server"],
                self.config["email"]["smtp_port"]
            )
            server.starttls()
            server.login(
                self.config["email"]["username"],
                self.config["email"]["password"]
            )
            
            text = msg.as_string()
            server.sendmail(
                self.config["email"]["from_email"],
                self.config["email"]["to_emails"],
                text
            )
            server.quit()
            
            self.log_alert("EMAIL", subject, severity, "SUCCESS")
            return True
            
        except Exception as e:
            self.log_alert("EMAIL", subject, severity, f"FAILED: {e}")
            return False
    
    def send_slack_alert(self, message: str, severity: str = "INFO"):
        """Slack 알림 전송"""
        if not self.config["slack"]["enabled"]:
            return False
        
        try:
            # 심각도에 따른 색상 설정
            color_map = {
                "INFO": "#36a64f",      # 녹색
                "WARNING": "#ffaa00",   # 주황색
                "CRITICAL": "#ff0000",  # 빨간색
                "ERROR": "#ff0000"      # 빨간색
            }
            
            payload = {
                "channel": self.config["slack"]["channel"],
                "username": self.config["slack"]["username"],
                "attachments": [{
                    "color": color_map.get(severity, "#36a64f"),
                    "title": f"DreamSeed 알림 [{severity}]",
                    "text": message,
                    "footer": "DreamSeed 모니터링",
                    "ts": int(time.time())
                }]
            }
            
            response = requests.post(
                self.config["slack"]["webhook_url"],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_alert("SLACK", message, severity, "SUCCESS")
                return True
            else:
                self.log_alert("SLACK", message, severity, f"FAILED: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_alert("SLACK", message, severity, f"FAILED: {e}")
            return False
    
    def send_webhook_alert(self, data: Dict):
        """웹훅 알림 전송"""
        if not self.config["webhook"]["enabled"]:
            return False
        
        try:
            response = requests.post(
                self.config["webhook"]["url"],
                json=data,
                headers=self.config["webhook"]["headers"],
                timeout=10
            )
            
            if response.status_code in [200, 201, 202]:
                self.log_alert("WEBHOOK", data.get("message", ""), data.get("severity", "INFO"), "SUCCESS")
                return True
            else:
                self.log_alert("WEBHOOK", data.get("message", ""), data.get("severity", "INFO"), f"FAILED: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_alert("WEBHOOK", data.get("message", ""), data.get("severity", "INFO"), f"FAILED: {e}")
            return False
    
    def send_alert(self, subject: str, message: str, severity: str = "INFO", alert_type: str = "all"):
        """통합 알림 전송"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "subject": subject,
            "message": message,
            "severity": severity,
            "alert_type": alert_type
        }
        
        success_count = 0
        total_count = 0
        
        # 이메일 알림
        if alert_type in ["all", "email"] and self.config["email"]["enabled"]:
            total_count += 1
            if self.send_email_alert(subject, message, severity):
                success_count += 1
        
        # Slack 알림
        if alert_type in ["all", "slack"] and self.config["slack"]["enabled"]:
            total_count += 1
            if self.send_slack_alert(message, severity):
                success_count += 1
        
        # 웹훅 알림
        if alert_type in ["all", "webhook"] and self.config["webhook"]["enabled"]:
            total_count += 1
            if self.send_webhook_alert(alert_data):
                success_count += 1
        
        # 알림 기록 저장
        self.alert_history.append(alert_data)
        
        return success_count, total_count
    
    def log_alert(self, method: str, subject: str, severity: str, status: str):
        """알림 로그 기록"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "subject": subject,
            "severity": severity,
            "status": status
        }
        
        # 로그 파일에 저장
        with open("alert_log.json", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def check_thresholds(self, metrics: Dict):
        """메트릭 임계값 확인"""
        alerts = []
        
        # CPU 사용률 확인
        if "cpu_usage" in metrics:
            if metrics["cpu_usage"] > self.config["thresholds"]["cpu_usage"]:
                alerts.append({
                    "subject": "높은 CPU 사용률",
                    "message": f"CPU 사용률이 {metrics['cpu_usage']:.1f}%로 임계값 {self.config['thresholds']['cpu_usage']}%를 초과했습니다.",
                    "severity": "WARNING"
                })
        
        # 메모리 사용률 확인
        if "memory_usage" in metrics:
            if metrics["memory_usage"] > self.config["thresholds"]["memory_usage"]:
                alerts.append({
                    "subject": "높은 메모리 사용률",
                    "message": f"메모리 사용률이 {metrics['memory_usage']:.1f}%로 임계값 {self.config['thresholds']['memory_usage']}%를 초과했습니다.",
                    "severity": "WARNING"
                })
        
        # 디스크 사용률 확인
        if "disk_usage" in metrics:
            if metrics["disk_usage"] > self.config["thresholds"]["disk_usage"]:
                alerts.append({
                    "subject": "높은 디스크 사용률",
                    "message": f"디스크 사용률이 {metrics['disk_usage']:.1f}%로 임계값 {self.config['thresholds']['disk_usage']}%를 초과했습니다.",
                    "severity": "WARNING"
                })
        
        # 응답 시간 확인
        if "response_time" in metrics:
            if metrics["response_time"] > self.config["thresholds"]["response_time"]:
                alerts.append({
                    "subject": "높은 응답 시간",
                    "message": f"평균 응답 시간이 {metrics['response_time']:.2f}초로 임계값 {self.config['thresholds']['response_time']}초를 초과했습니다.",
                    "severity": "WARNING"
                })
        
        # 에러율 확인
        if "error_rate" in metrics:
            if metrics["error_rate"] > self.config["thresholds"]["error_rate"]:
                alerts.append({
                    "subject": "높은 에러율",
                    "message": f"에러율이 {metrics['error_rate']:.1f}%로 임계값 {self.config['thresholds']['error_rate']}%를 초과했습니다.",
                    "severity": "CRITICAL"
                })
        
        return alerts
    
    def get_alert_history(self, limit: int = 100):
        """알림 기록 조회"""
        return self.alert_history[-limit:]
    
    def test_alerts(self):
        """알림 테스트"""
        test_message = "DreamSeed 알림 시스템 테스트입니다."
        
        print("🧪 알림 시스템 테스트 시작...")
        
        # 이메일 테스트
        if self.config["email"]["enabled"]:
            print("📧 이메일 알림 테스트...")
            success, total = self.send_alert("테스트 알림", test_message, "INFO", "email")
            print(f"   결과: {success}/{total} 성공")
        
        # Slack 테스트
        if self.config["slack"]["enabled"]:
            print("💬 Slack 알림 테스트...")
            success, total = self.send_alert("테스트 알림", test_message, "INFO", "slack")
            print(f"   결과: {success}/{total} 성공")
        
        # 웹훅 테스트
        if self.config["webhook"]["enabled"]:
            print("🔗 웹훅 알림 테스트...")
            success, total = self.send_alert("테스트 알림", test_message, "INFO", "webhook")
            print(f"   결과: {success}/{total} 성공")
        
        print("✅ 알림 시스템 테스트 완료")

# 사용 예시
if __name__ == "__main__":
    alert_manager = AlertManager()
    
    # 테스트 알림 전송
    alert_manager.send_alert(
        "시스템 상태 확인",
        "DreamSeed 시스템이 정상적으로 작동하고 있습니다.",
        "INFO"
    )
    
    # 임계값 테스트
    test_metrics = {
        "cpu_usage": 85.5,
        "memory_usage": 92.3,
        "disk_usage": 88.7,
        "response_time": 2.5,
        "error_rate": 6.2
    }
    
    alerts = alert_manager.check_thresholds(test_metrics)
    for alert in alerts:
        alert_manager.send_alert(**alert)
    
    # 알림 테스트
    alert_manager.test_alerts()

