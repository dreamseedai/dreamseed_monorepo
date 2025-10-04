# GPT-4.1 mini batch MathML 변환 가이드

## 🎯 개요
100 단위로 배치 처리하여 전체 MathML 데이터를 효율적으로 MathLive 형식으로 변환하는 시스템입니다.

## 🚀 빠른 시작

### 1. 환경 설정
```bash
# OpenAI API 키 설정
export OPENAI_API_KEY='your-api-key-here'

# Python 의존성 설치
pip3 install aiohttp
```

### 2. 배치 변환 실행
```bash
# 기본 설정 (100개씩, 총 1000개)
./run_batch_conversion.sh

# 커스텀 설정 (50개씩, 총 500개)
./run_batch_conversion.sh 50 500

# 대량 처리 (100개씩, 총 10000개)
./run_batch_conversion.sh 100 10000
```

### 3. 진행 상황 모니터링
```bash
# 실시간 대시보드 확인
python3 monitor_conversion.py

# 로그 파일 확인
tail -f batch_conversion_*.log
```

## 📊 시스템 특징

### ✅ 효율성
- **비동기 처리**: 여러 요청을 동시에 처리
- **배치 단위**: 100개씩 묶어서 효율적 처리
- **API 제한 고려**: 배치 간 자동 대기

### ✅ 안정성
- **에러 처리**: 개별 실패가 전체에 영향 없음
- **진행 상황 저장**: 각 배치별 결과 자동 저장
- **상세 로깅**: 모든 과정이 로그에 기록

### ✅ 모니터링
- **실시간 대시보드**: 진행 상황 실시간 확인
- **통계 분석**: 성공률, 처리시간 등 상세 통계
- **에러 분석**: 실패 원인 분석 및 개선점 도출

## 📁 출력 파일

### 변환 결과
- `conversion_results_batch_001.json` - 1번째 배치 결과
- `conversion_results_batch_002.json` - 2번째 배치 결과
- ...

### 로그 및 통계
- `batch_conversion_YYYYMMDD_HHMMSS.log` - 실행 로그
- `conversion_stats.json` - 전체 통계 (JSON)
- `batch_conversion.log` - 상세 변환 로그

## 🔧 고급 설정

### 배치 크기 조정
```python
# batch_mathml_processor.py에서 수정
processor = BatchMathMLProcessor(api_key, batch_size=50)  # 50개씩 처리
```

### API 제한 고려
```python
# 배치 간 대기 시간 조정
wait_time = 5  # 5초 대기 (API 제한에 따라 조정)
```

### 데이터베이스 연동
```python
def load_data_from_database(self, limit: int = None):
    # 실제 PostgreSQL 연결 코드
    import psycopg2
    conn = psycopg2.connect("your-database-url")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT question_id, mathml, subject, grade 
        FROM questions 
        WHERE mathml IS NOT NULL 
        ORDER BY question_id
        LIMIT %s
    """, (limit,))
    # ... 데이터 처리
```

## 📈 성능 최적화

### 권장 설정
- **배치 크기**: 100개 (API 제한과 효율성의 균형)
- **동시 요청**: 10-20개 (서버 부하 고려)
- **대기 시간**: 2-5초 (API 제한 고려)

### 모니터링 지표
- **성공률**: 95% 이상 목표
- **평균 처리시간**: 2-5초/항목
- **에러율**: 5% 이하 유지

## 🚨 문제 해결

### 일반적인 문제
1. **API 키 오류**: `OPENAI_API_KEY` 환경변수 확인
2. **네트워크 오류**: 인터넷 연결 및 방화벽 확인
3. **메모리 부족**: 배치 크기 줄이기 (50개로)
4. **API 제한**: 대기 시간 늘리기 (5초로)

### 로그 확인
```bash
# 에러 로그 확인
grep "ERROR" batch_conversion_*.log

# 성공률 확인
grep "성공" batch_conversion_*.log | tail -10
```

## 🎯 다음 단계

1. **데이터베이스 연동**: 실제 PostgreSQL 연결
2. **결과 저장**: 변환된 데이터를 DB에 업데이트
3. **자동화**: cron job으로 정기 실행
4. **알림**: 완료 시 Slack/이메일 알림

## 📞 지원

문제가 발생하면 다음 정보와 함께 문의하세요:
- 실행 로그 (`batch_conversion_*.log`)
- 통계 파일 (`conversion_stats.json`)
- 에러 메시지
- 시스템 환경 (OS, Python 버전 등)
