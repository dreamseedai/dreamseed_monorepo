#!/usr/bin/env python3
"""
샘플 데이터 생성 스크립트 (테스트용)
"""
import pandas as pd
import numpy as np
import datetime as dt
import sys
import random

def generate_sample_data(output_file, num_days=14, num_students_per_tenant=20):
    """
    테스트용 샘플 데이터 생성
    
    Args:
        output_file: 출력 CSV 파일 경로
        num_days: 생성할 일수 (기본 14일)
        num_students_per_tenant: 테넌트당 학생 수
    """
    today = dt.date.today()
    dates = [today - dt.timedelta(days=i) for i in range(num_days)]
    
    # 테넌트 목록 (dreamseedai로 변경)
    tenants = ["dreamseedai-seoul", "school-alpha", "collegeprepai-demo"]
    
    rows = []
    
    for org in tenants:
        # 테넌트별 학생 생성
        for u in range(1001, 1001 + num_students_per_tenant):
            # 초기 θ 값 (학생마다 다름)
            theta = np.random.normal(0.0, 0.5)
            
            # 학생별 특성 (일부는 리스크 있게)
            is_at_risk = random.random() < 0.2  # 20% 학생은 리스크
            omit_prob = 0.15 if is_at_risk else 0.03
            attend_prob = 0.75 if is_at_risk else 0.95
            theta_decline = -0.02 if is_at_risk else 0.01
            
            for d in sorted(dates):
                # θ 변화 (리스크 학생은 하락)
                theta += np.random.normal(theta_decline, 0.05)
                
                # 데이터 포인트 생성
                rows.append({
                    'org_id': org,
                    'user_id': u,
                    'test_id': f"T{d.isoformat()}",
                    'd': d,
                    'theta_estimate': round(theta, 4),
                    'correct': np.random.randint(0, 2),
                    'omitted': np.random.binomial(1, omit_prob),
                    'attended': np.random.binomial(1, attend_prob)
                })
    
    # DataFrame 생성 및 저장
    df = pd.DataFrame(rows)
    df.to_csv(output_file, index=False)
    
    # 통계 출력
    print(f"✓ Sample data generated: {output_file}")
    print(f"  - Tenants: {len(tenants)}")
    print(f"  - Students per tenant: {num_students_per_tenant}")
    print(f"  - Days: {num_days}")
    print(f"  - Total rows: {len(df)}")
    print(f"\n  Distribution by tenant:")
    print(df.groupby('org_id')['user_id'].nunique())

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python generate_sample_data.py <output_file>")
        sys.exit(1)
    
    output_file = sys.argv[1]
    generate_sample_data(output_file)
