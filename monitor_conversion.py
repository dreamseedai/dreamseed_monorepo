#!/usr/bin/env python3
"""
배치 변환 진행 상황 모니터링 스크립트
"""

import json
import glob
import os
from datetime import datetime
from typing import List, Dict, Any

def analyze_conversion_results() -> Dict[str, Any]:
    """변환 결과 파일들을 분석하여 통계 생성"""
    
    # 결과 파일들 찾기
    result_files = glob.glob("conversion_results_batch_*.json")
    
    if not result_files:
        return {"error": "변환 결과 파일을 찾을 수 없습니다."}
    
    total_processed = 0
    total_success = 0
    total_failed = 0
    total_processing_time = 0.0
    error_messages = {}
    
    batch_stats = []
    
    for file_path in sorted(result_files):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                batch_data = json.load(f)
            
            batch_num = int(file_path.split('_')[-1].split('.')[0])
            batch_processed = len(batch_data)
            batch_success = sum(1 for item in batch_data if item['success'])
            batch_failed = batch_processed - batch_success
            batch_time = sum(item['processing_time'] for item in batch_data)
            
            batch_stats.append({
                'batch_num': batch_num,
                'processed': batch_processed,
                'success': batch_success,
                'failed': batch_failed,
                'success_rate': (batch_success / batch_processed * 100) if batch_processed > 0 else 0,
                'avg_time': batch_time / batch_processed if batch_processed > 0 else 0
            })
            
            total_processed += batch_processed
            total_success += batch_success
            total_failed += batch_failed
            total_processing_time += batch_time
            
            # 에러 메시지 수집
            for item in batch_data:
                if not item['success'] and item['error_message']:
                    error_msg = item['error_message']
                    error_messages[error_msg] = error_messages.get(error_msg, 0) + 1
                    
        except Exception as e:
            print(f"파일 {file_path} 분석 중 오류: {e}")
    
    # 전체 통계 계산
    success_rate = (total_success / total_processed * 100) if total_processed > 0 else 0
    avg_processing_time = total_processing_time / total_processed if total_processed > 0 else 0
    
    return {
        'summary': {
            'total_processed': total_processed,
            'total_success': total_success,
            'total_failed': total_failed,
            'success_rate': success_rate,
            'avg_processing_time': avg_processing_time,
            'total_processing_time': total_processing_time,
            'total_batches': len(batch_stats)
        },
        'batch_stats': batch_stats,
        'error_messages': error_messages,
        'last_updated': datetime.now().isoformat()
    }

def print_dashboard(stats: Dict[str, Any]):
    """대시보드 형태로 통계 출력"""
    
    if 'error' in stats:
        print(f"❌ {stats['error']}")
        return
    
    summary = stats['summary']
    
    print("=" * 60)
    print("📊 GPT-4.1 mini batch MathML 변환 대시보드")
    print("=" * 60)
    print(f"🕐 마지막 업데이트: {stats['last_updated']}")
    print()
    
    print("📈 전체 통계:")
    print(f"  • 총 처리량: {summary['total_processed']:,}개")
    print(f"  • 성공: {summary['total_success']:,}개 ({summary['success_rate']:.1f}%)")
    print(f"  • 실패: {summary['total_failed']:,}개")
    print(f"  • 총 배치: {summary['total_batches']}개")
    print(f"  • 평균 처리시간: {summary['avg_processing_time']:.2f}초/항목")
    print(f"  • 총 처리시간: {summary['total_processing_time']:.1f}초")
    print()
    
    print("📋 배치별 상세:")
    for batch in stats['batch_stats']:
        print(f"  배치 {batch['batch_num']:3d}: "
              f"{batch['success']:3d}/{batch['processed']:3d} "
              f"({batch['success_rate']:5.1f}%) "
              f"평균 {batch['avg_time']:5.2f}초")
    print()
    
    if stats['error_messages']:
        print("❌ 주요 에러 메시지:")
        for error, count in sorted(stats['error_messages'].items(), 
                                 key=lambda x: x[1], reverse=True)[:5]:
            print(f"  • {error}: {count}회")
        print()

def main():
    """메인 실행 함수"""
    print("배치 변환 진행 상황 분석 중...")
    
    stats = analyze_conversion_results()
    print_dashboard(stats)
    
    # 결과를 JSON 파일로도 저장
    with open('conversion_stats.json', 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print("📁 상세 통계가 conversion_stats.json에 저장되었습니다.")

if __name__ == "__main__":
    main()
