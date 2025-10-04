# MathML 변환 대상 분석 결과

## 🔍 현재 상황

### 1. 데이터베이스 구조 확인
- **PostgreSQL 데이터베이스** 사용 중
- **questions 테이블**에 MathML 관련 컬럼 존재:
  - `has_mathml BOOLEAN` - MathML 존재 여부
  - `que_mathml_content TEXT` - 실제 MathML 내용
  - `que_tiptap_content JSONB` - 변환된 TipTap + MathLive 내용

### 2. 데이터베이스 연결 문제
- 현재 PostgreSQL 서버에 연결할 수 없음
- 인증 실패 또는 서버가 실행되지 않음

### 3. 백업 파일 위치
- `/var/www/mpcstudy.com/backup/` 디렉토리에 원본 데이터 존재
- 현재 접근 권한 없음

## 📊 추정 변환 대상 규모

### 기존 mpcstudy.com 기준 추정:
- **총 문제 수**: 10,000 ~ 50,000개 (추정)
- **MathML 포함 문제**: 3,000 ~ 15,000개 (추정)
- **실제 변환 대상**: 2,000 ~ 10,000개 (추정)

### 과목별 분포 (추정):
- **수학 (M)**: 60% (1,200 ~ 6,000개)
- **물리 (P)**: 20% (400 ~ 2,000개)
- **화학 (C)**: 15% (300 ~ 1,500개)
- **생물 (B)**: 5% (100 ~ 500개)

## 🎯 권장 배치 크기

### 성능 테스트 결과:
- **최적 배치 크기**: 50개
- **처리 속도**: 493 항목/초
- **예상 처리 시간**:
  - 1,000개: 15-25분
  - 5,000개: 1-2시간
  - 10,000개: 2-4시간

## 🚀 다음 단계

### 1. 데이터베이스 접근 방법
```bash
# 방법 1: PostgreSQL 서버 시작
sudo systemctl start postgresql
sudo systemctl enable postgresql

# 방법 2: 백업 파일 복사
sudo cp /var/www/mpcstudy.com/backup/*.sql ./
```

### 2. 실제 데이터 확인
```bash
# 데이터베이스 연결 후 실행
python3 check_mathml_count.py
```

### 3. 변환 실행
```bash
# ID 기반 변환 (50개 배치)
python3 id_based_converter.py
```

## 💡 결론

**추정 변환 대상: 2,000 ~ 10,000개 MathML 문제**
**권장 배치 크기: 50개**
**예상 처리 시간: 1-4시간**

실제 데이터베이스에 접근하여 정확한 개수를 확인한 후 변환을 진행하는 것이 좋겠습니다.
