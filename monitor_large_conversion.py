#!/usr/bin/env python3
"""
대용량 MathML 변환 진행 상황 모니터링 스크립트
"""

import json
import time
import os
import glob
from datetime import datetime

def monitor_large_conversion():
    """대용량 변환 진행 상황 모니터링"""
    print("🚀 대용량 MathML 변환 진행 상황 모니터링 시작 (Ctrl+C로 종료)")
    print("-" * 60)
    
    last_processed = -1
    last_total = -1
    start_time = time.time()
    
    try:
        while True:
            # 배치 결과 파일들 확인
            batch_files = glob.glob("conversion_results_batch_*.json")
            batch_files.sort()
            
            if batch_files:
                # 마지막 배치 파일에서 진행 상황 확인
                latest_batch = batch_files[-1]
                
                try:
                    with open(latest_batch, "r", encoding="utf-8") as f:
                        batch_data = json.load(f)
                    
                    # 현재까지 처리된 총 개수 계산
                    total_processed = 0
                    total_success = 0
                    total_failed = 0
                    
                    for batch_file in batch_files:
                        with open(batch_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            total_processed += len(data)
                            total_success += sum(1 for item in data if item.get('success', False))
                            total_failed += sum(1 for item in data if not item.get('success', False))
                    
                    # 진행률 계산 (총 1000개 가정)
                    estimated_total = 1000  # 실제로는 데이터베이스에서 조회
                    progress_percentage = (total_processed / estimated_total) * 100
                    
                    # 시간 정보
                    elapsed_time = time.time() - start_time
                    hours = int(elapsed_time // 3600)
                    minutes = int((elapsed_time % 3600) // 60)
                    seconds = int(elapsed_time % 60)
                    
                    # 진행 상황 출력
                    if total_processed != last_processed:
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                              f"진행률: {total_processed}/{estimated_total} ({progress_percentage:.1f}%) | "
                              f"성공: {total_success} | 실패: {total_failed} | "
                              f"경과시간: {hours:02d}:{minutes:02d}:{seconds:02d}")
                        
                        last_processed = total_processed
                        
                        # 완료 확인
                        if total_processed >= estimated_total:
                            print("✅ 모든 변환이 완료되었습니다!")
                            break
                    
                    # 처리 속도 계산
                    if elapsed_time > 0:
                        rate = total_processed / elapsed_time
                        print(f"   처리 속도: {rate:.2f} 항목/초")
                    
                except json.JSONDecodeError:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {latest_batch} 파일이 유효한 JSON 형식이 아닙니다.")
                except Exception as e:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 오류 발생: {e}")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 배치 결과 파일을 찾을 수 없습니다. 변환이 시작되지 않았거나 파일이 생성되지 않았습니다.")
            
            time.sleep(10)  # 10초마다 업데이트
            
    except KeyboardInterrupt:
        print("\n모니터링을 중단합니다.")
    except Exception as e:
        print(f"모니터링 중 오류 발생: {e}")

def show_summary():
    """변환 결과 요약 출력"""
    print("\n📊 변환 결과 요약:")
    print("-" * 40)
    
    batch_files = glob.glob("conversion_results_batch_*.json")
    batch_files.sort()
    
    if not batch_files:
        print("❌ 배치 결과 파일이 없습니다.")
        return
    
    total_processed = 0
    total_success = 0
    total_failed = 0
    total_time = 0
    
    for batch_file in batch_files:
        try:
            with open(batch_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                total_processed += len(data)
                total_success += sum(1 for item in data if item.get('success', False))
                total_failed += sum(1 for item in data if not item.get('success', False))
                total_time += sum(item.get('processing_time', 0) for item in data)
        except Exception as e:
            print(f"❌ {batch_file} 읽기 실패: {e}")
    
    success_rate = (total_success / total_processed * 100) if total_processed > 0 else 0
    avg_time = (total_time / total_processed) if total_processed > 0 else 0
    
    print(f"📁 총 배치 파일: {len(batch_files)}개")
    print(f"📝 총 처리 항목: {total_processed}개")
    print(f"✅ 성공: {total_success}개 ({success_rate:.1f}%)")
    print(f"❌ 실패: {total_failed}개")
    print(f"⏱️ 평균 처리 시간: {avg_time:.2f}초/항목")
    print(f"📊 총 처리 시간: {total_time:.2f}초")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "summary":
        show_summary()
    else:
        monitor_large_conversion()
