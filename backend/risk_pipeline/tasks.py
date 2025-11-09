"""
Celery 태스크: 주간 리스크 리포트 자동화
"""
from celery import Celery, group, chain
from celery.schedules import crontab
import subprocess
import os
from pathlib import Path
from datetime import datetime
import yaml
import logging

# Celery 앱 초기화
app = Celery('risk_pipeline')
app.config_from_object('celeryconfig')

# 로깅 설정
logger = logging.getLogger(__name__)

# 경로 설정
BASE_DIR = Path(__file__).parent
JOBS_DIR = BASE_DIR / 'jobs'
CONFIG_DIR = BASE_DIR / 'config'
REPORTS_DIR = BASE_DIR / 'reports'
TEMPLATES_DIR = BASE_DIR / 'templates'

@app.task(bind=True, name='risk_pipeline.fetch_snapshots')
def fetch_snapshots(self):
    """
    Step 1: PostgreSQL에서 스냅샷 데이터 추출
    """
    logger.info("Fetching snapshots from database...")
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_file = f"/tmp/snapshot_{date_str}.csv"
    sql_file = JOBS_DIR / '00_fetch_snapshots.sql'
    
    try:
        # psql 명령 실행
        cmd = f"psql -f {sql_file} > {output_file}"
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"✓ Snapshot saved to {output_file}")
        return output_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to fetch snapshots: {e.stderr}")
        raise

@app.task(bind=True, name='risk_pipeline.compute_metrics')
def compute_metrics(self, snapshot_file):
    """
    Step 2: R 스크립트로 리스크 메트릭 계산
    """
    logger.info("Computing risk metrics...")
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_file = f"/tmp/metrics_{date_str}.csv"
    
    r_script = JOBS_DIR / '10_compute_metrics.R'
    tenants_yaml = CONFIG_DIR / 'tenants.yaml'
    thresholds_yaml = CONFIG_DIR / 'thresholds.yaml'
    
    try:
        cmd = [
            'Rscript',
            str(r_script),
            snapshot_file,
            str(tenants_yaml),
            str(thresholds_yaml),
            output_file
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"✓ Metrics computed: {output_file}")
        logger.info(result.stdout)
        return output_file
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to compute metrics: {e.stderr}")
        raise

@app.task(bind=True, name='risk_pipeline.aggregate_data')
def aggregate_data(self, metrics_file):
    """
    Step 3: Python으로 테넌트별 집계
    """
    logger.info("Aggregating data by tenant...")
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    output_dir = REPORTS_DIR / date_str
    output_dir.mkdir(parents=True, exist_ok=True)
    
    py_script = JOBS_DIR / '20_aggregate.py'
    tenants_yaml = CONFIG_DIR / 'tenants.yaml'
    
    try:
        cmd = [
            'python3',
            str(py_script),
            metrics_file,
            str(tenants_yaml),
            str(output_dir)
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"✓ Data aggregated: {output_dir}")
        logger.info(result.stdout)
        return str(output_dir)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to aggregate data: {e.stderr}")
        raise

@app.task(bind=True, name='risk_pipeline.render_report')
def render_report(self, org_id, metrics_file, output_dir):
    """
    Step 4: RMarkdown으로 리포트 렌더링 (테넌트별)
    """
    logger.info(f"Rendering report for {org_id}...")
    
    # 테넌트 설정 로드
    tenants_yaml = CONFIG_DIR / 'tenants.yaml'
    with open(tenants_yaml, 'r') as f:
        tenants_config = yaml.safe_load(f)
    
    tenant = next((t for t in tenants_config['tenants'] if t['org_id'] == org_id), None)
    if not tenant:
        logger.warning(f"Tenant {org_id} not found in config")
        return None
    
    # 출력 파일 경로
    output_file = Path(output_dir) / f"{org_id}_report.html"
    
    # RMarkdown 렌더링
    r_code = f"""
    library(rmarkdown)
    rmarkdown::render(
      input = '{TEMPLATES_DIR}/weekly_report.Rmd',
      output_file = '{output_file}',
      params = list(
        org_id = '{org_id}',
        org_name = '{tenant['name']}',
        metrics_csv = '{metrics_file}',
        primary_color = '{tenant['branding']['primary_color']}',
        logo_path = '{tenant['branding'].get('logo_path', '')}',
        report_date = Sys.Date()
      ),
      quiet = TRUE
    )
    """
    
    try:
        result = subprocess.run(
            ['Rscript', '-e', r_code],
            capture_output=True,
            text=True,
            check=True
        )
        
        logger.info(f"✓ Report rendered: {output_file}")
        return str(output_file)
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to render report for {org_id}: {e.stderr}")
        raise

@app.task(bind=True, name='risk_pipeline.send_report')
def send_report(self, org_id, report_file, summary_file):
    """
    Step 5: 이메일/슬랙으로 리포트 전송
    """
    logger.info(f"Sending report for {org_id}...")
    
    # 테넌트 설정 로드
    tenants_yaml = CONFIG_DIR / 'tenants.yaml'
    with open(tenants_yaml, 'r') as f:
        tenants_config = yaml.safe_load(f)
    
    tenant = next((t for t in tenants_config['tenants'] if t['org_id'] == org_id), None)
    if not tenant:
        logger.warning(f"Tenant {org_id} not found in config")
        return None
    
    # 이메일 전송 (구현 필요)
    if tenant.get('email_to'):
        # TODO: 이메일 전송 로직
        logger.info(f"Would send email to: {tenant['email_to']}")
    
    # 슬랙 전송 (구현 필요)
    if tenant.get('slack_webhook'):
        # TODO: 슬랙 웹훅 전송 로직
        logger.info(f"Would send Slack notification to: {tenant['slack_webhook']}")
    
    return f"Report sent for {org_id}"

@app.task(bind=True, name='risk_pipeline.run_weekly_pipeline')
def run_weekly_pipeline(self):
    """
    전체 파이프라인 오케스트레이션
    """
    logger.info("=== Starting Weekly Risk Pipeline ===")
    
    # 테넌트 목록 로드
    tenants_yaml = CONFIG_DIR / 'tenants.yaml'
    with open(tenants_yaml, 'r') as f:
        tenants_config = yaml.safe_load(f)
    
    # 파이프라인 체인 구성
    pipeline = chain(
        fetch_snapshots.s(),
        compute_metrics.s(),
        aggregate_data.s(),
    )
    
    # 파이프라인 실행
    result = pipeline.apply_async()
    output_dir = result.get()
    
    # 테넌트별 리포트 렌더링 및 전송 (병렬)
    date_str = datetime.now().strftime('%Y-%m-%d')
    metrics_file = f"/tmp/metrics_{date_str}.csv"
    summary_file = Path(output_dir) / 'summary.csv'
    
    render_tasks = []
    for tenant in tenants_config['tenants']:
        org_id = tenant['org_id']
        
        # 렌더링 → 전송 체인
        task_chain = chain(
            render_report.s(org_id, metrics_file, output_dir),
            send_report.s(org_id, str(summary_file))
        )
        render_tasks.append(task_chain)
    
    # 병렬 실행
    job = group(render_tasks)
    result = job.apply_async()
    
    logger.info("=== Weekly Risk Pipeline Completed ===")
    return "Pipeline completed successfully"

# Celery Beat 스케줄 설정
app.conf.beat_schedule = {
    'weekly-risk-report': {
        'task': 'risk_pipeline.run_weekly_pipeline',
        'schedule': crontab(hour=6, minute=0, day_of_week=1),  # 월요일 06:00
    },
}
