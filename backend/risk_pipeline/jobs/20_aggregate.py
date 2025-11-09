#!/usr/bin/env python3
"""
리스크 메트릭 집계 및 테넌트별 요약 생성
"""
import pandas as pd
import yaml
import sys
from pathlib import Path
from datetime import datetime

def load_config(yaml_path):
    """YAML 설정 로드"""
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)

def aggregate_by_tenant(metrics_df, tenants_config):
    """테넌트별 리스크 요약 생성"""
    summaries = []
    
    for tenant in tenants_config['tenants']:
        org_id = tenant['org_id']
        org_data = metrics_df[metrics_df['org_id'] == org_id]
        
        if org_data.empty:
            continue
        
        summary = {
            'org_id': org_id,
            'org_name': tenant['name'],
            'report_date': datetime.now().strftime('%Y-%m-%d'),
            'total_students': len(org_data),
            'crit_count': (org_data['risk_overall'] == 'CRIT').sum(),
            'warn_count': (org_data['risk_overall'] == 'WARN').sum(),
            'ok_count': (org_data['risk_overall'] == 'OK').sum(),
            'crit_pct': 100 * (org_data['risk_overall'] == 'CRIT').mean(),
            'warn_pct': 100 * (org_data['risk_overall'] == 'WARN').mean(),
            
            # 세부 리스크 분포
            'theta_crit': (org_data['risk_theta'] == 'CRIT').sum(),
            'theta_warn': (org_data['risk_theta'] == 'WARN').sum(),
            'omit_crit': (org_data['risk_omit'] == 'CRIT').sum(),
            'omit_warn': (org_data['risk_omit'] == 'WARN').sum(),
            'guess_crit': (org_data['risk_guess'] == 'CRIT').sum(),
            'guess_warn': (org_data['risk_guess'] == 'WARN').sum(),
            'attendance_crit': (org_data['risk_attendance'] == 'CRIT').sum(),
            'attendance_warn': (org_data['risk_attendance'] == 'WARN').sum(),
            
            # 평균 메트릭
            'avg_delta_theta_7d': org_data['delta_theta_7d'].mean(),
            'avg_omit_rate': org_data['omit_rate'].mean(),
            'avg_attendance_rate': org_data['attendance_rate_7d'].mean(),
        }
        
        summaries.append(summary)
    
    return pd.DataFrame(summaries)

def identify_top_risks(metrics_df, top_n=10):
    """상위 리스크 학생 식별"""
    # CRIT 학생 우선, 그 다음 WARN
    crit_students = metrics_df[metrics_df['risk_overall'] == 'CRIT'].copy()
    warn_students = metrics_df[metrics_df['risk_overall'] == 'WARN'].copy()
    
    # θ 하락폭 기준 정렬
    crit_students['risk_score'] = (
        -crit_students['delta_theta_7d'] * 2 +
        crit_students['omit_rate'] * 1 +
        (1 - crit_students['attendance_rate_7d']) * 1.5
    )
    
    warn_students['risk_score'] = (
        -warn_students['delta_theta_7d'] * 2 +
        warn_students['omit_rate'] * 1 +
        (1 - warn_students['attendance_rate_7d']) * 1.5
    )
    
    top_risks = pd.concat([
        crit_students.nlargest(top_n, 'risk_score'),
        warn_students.nlargest(top_n, 'risk_score')
    ]).drop_duplicates(subset=['org_id', 'user_id'])
    
    return top_risks.head(top_n)

def main():
    if len(sys.argv) < 4:
        print("Usage: python 20_aggregate.py <metrics_csv> <tenants_yaml> <output_dir>")
        sys.exit(1)
    
    metrics_csv = sys.argv[1]
    tenants_yaml = sys.argv[2]
    output_dir = Path(sys.argv[3])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 데이터 로드
    metrics_df = pd.read_csv(metrics_csv)
    tenants_config = load_config(tenants_yaml)
    
    # 테넌트별 요약 생성
    summary_df = aggregate_by_tenant(metrics_df, tenants_config)
    summary_path = output_dir / 'summary.csv'
    summary_df.to_csv(summary_path, index=False)
    print(f"✓ Summary saved to {summary_path}")
    
    # 테넌트별 상위 리스크 학생 추출
    for tenant in tenants_config['tenants']:
        org_id = tenant['org_id']
        org_data = metrics_df[metrics_df['org_id'] == org_id]
        
        if org_data.empty:
            continue
        
        # 전체 메트릭 저장
        org_metrics_path = output_dir / f'{org_id}_metrics.csv'
        org_data.to_csv(org_metrics_path, index=False)
        
        # 상위 리스크 학생 저장
        top_risks = identify_top_risks(org_data, top_n=20)
        top_risks_path = output_dir / f'{org_id}_top_risks.csv'
        top_risks.to_csv(top_risks_path, index=False)
        
        print(f"✓ {org_id}: {len(org_data)} students, {len(top_risks)} top risks")
    
    # 전체 통계 출력
    print("\n=== Overall Statistics ===")
    print(f"Total tenants: {len(summary_df)}")
    print(f"Total students: {summary_df['total_students'].sum()}")
    print(f"CRIT students: {summary_df['crit_count'].sum()} ({summary_df['crit_pct'].mean():.1f}%)")
    print(f"WARN students: {summary_df['warn_count'].sum()} ({summary_df['warn_pct'].mean():.1f}%)")

if __name__ == '__main__':
    main()
