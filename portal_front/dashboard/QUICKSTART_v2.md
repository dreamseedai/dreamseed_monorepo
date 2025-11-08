# Teacher Dashboard v2.0 - Quick Start Guide

## 🎯 새로운 기능 4가지 (2025-11-06)

### 1️⃣ 개별 학생 즉시 과제 배정 ✅
**위치**: 학생 목록 테이블 → "과제 배정" 버튼  
**사용법**: 
- 학생 행의 "과제 배정" 버튼 클릭
- 학생의 θ 수준에 맞는 과제 자동 선택
- 성공/실패 알림 즉시 표시

**예시**:
```
학생: 김철수 (θ = -1.8)
버튼 클릭 → "remedial_basics" 자동 배정
알림: "✓ 김철수 학생에게 'remedial_basics' 과제를 배정했습니다."
```

---

### 2️⃣ 출석 요일별 분산 분석 ✅
**위치**: 학생 목록 테이블 → 새로운 컬럼  
- `abs_variance`: 요일별 결석률 분산
- `worst_day`: 결석이 가장 많은 요일

**해석**:
- **분산 < 0.01**: 규칙적인 출석 패턴
- **분산 0.01~0.05**: 특정 요일 문제
- **분산 > 0.05**: 매우 불규칙 (예: 매주 금요일 결석)

**활용 예시**:
```
학생: 이영희
abs_variance: 0.08
worst_day: "Fri"
worst_day_abs_rate: 40%

→ 매주 금요일 40% 결석 → 학부모 상담 필요
```

---

### 3️⃣ 문항 반응 이상 모달 (빠른 접근) ✅
**위치**: "문항 반응 이상 패턴 세부 분석" 박스 → 4개 버튼  
1. "Pure Guessing 학생 보기"
2. "Strategic Omit 학생 보기"
3. "Rapid-Fire 학생 보기"
4. "복합 패턴 학생 보기"

**사용법**:
- 버튼 클릭 → 모달 팝업
- 해당 패턴 학생 목록 자동 필터링
- 정렬 가능 (추측률, 무응답률 등)
- 학생 ID로 추가 조사 가능

**예시**:
```
"Pure Guessing 학생 보기" 클릭
→ 모달: "Pure Guessing 패턴 학생 목록 (7명)"
→ 테이블: student_id, name, guess_rate, omit_rate, ...
→ guess_rate 내림차순 정렬 → 최악 학생 파악
```

---

### 4️⃣ YAML 핫리로드 (재시작 불필요) ✅
**자동 감지**: 30초마다 `config/assignment_templates.yaml` 변경 체크  
**제로 다운타임**: 대시보드 재시작 없이 설정 적용

**사용법**:
```bash
# 1. 설정 파일 수정
vim config/assignment_templates.yaml

# 2. 변경사항 저장
# templates:
#   very_low:
#     template_id: "new_template_v2"  # 변경

# 3. 최대 30초 대기
# 4. 알림 자동 표시: "⚡ 설정 파일이 업데이트되었습니다"
# 5. 다음 과제 배정부터 new_template_v2 사용
```

**이전 (v1.0)**:
```bash
vim config/...
sudo systemctl restart portal-teacher-dashboard  # 30초+ 다운타임
```

**현재 (v2.0)**:
```bash
vim config/...
# 자동 재로드 (30초 이내, 다운타임 0초)
```

---

## 🚀 즉시 테스트하기

### Test 1: 개별 과제 배정
```r
# Shiny 앱 실행
Rscript app_teacher.R --port 8081

# 브라우저: http://localhost:8081
# 1. 학생 목록에서 임의 학생 선택
# 2. "과제 배정" 버튼 클릭
# 3. 알림 확인: "✓ [학생명] 학생에게 '[template_id]' 과제를 배정했습니다."
```

### Test 2: 요일별 분산
```r
# 1. 학생 테이블에서 abs_variance 컬럼 확인
# 2. 높은 값(>0.05) 학생 클릭
# 3. worst_day 확인 (예: "Mon", "Fri")
# 4. 드릴다운 모달에서 "출석 타임라인" 차트로 패턴 시각화
```

### Test 3: 이상 패턴 모달
```r
# 1. "문항 반응 이상 패턴 세부 분석" 박스 펼치기
# 2. "Pure Guessing 학생 보기" 클릭
# 3. 모달에서 guess_rate 컬럼 클릭 → 내림차순 정렬
# 4. 최상위 학생 ID 복사
# 5. 닫기 → 학생 테이블에서 해당 ID 검색
```

### Test 4: 핫리로드
```bash
# Terminal 1: 대시보드 실행 (로그 확인)
Rscript app_teacher.R --port 8081 2>&1 | tee dashboard.log

# Terminal 2: 설정 파일 수정
cd config
vim assignment_templates.yaml
# very_low.template_id 를 "test_hot_reload" 로 변경
# :wq

# Terminal 1: 30초 이내 로그 확인
# [hot-reload] Config file changed, reloading...
# [load_config] Successfully loaded config from: config/assignment_templates.yaml

# 브라우저: 알림 확인
# "⚡ 설정 파일이 업데이트되었습니다 (템플릿/권한 재로드 완료)"

# "매우낮음" CTA 클릭 → API 로그에서 "test_hot_reload" 확인
```

---

## 📊 성능 영향

| 기능 | 추가 연산 | 영향도 |
|------|----------|--------|
| 개별 배정 | 단일 API 호출 | 무시 가능 |
| 요일별 분산 | +20% (attn_metrics_tbl) | 낮음 |
| 이상 모달 | 온디맨드 (버튼 클릭 시) | 없음 (유휴 시) |
| 핫리로드 | 30초마다 파일 I/O | 무시 가능 |

**최적화 팁**:
- 요일별 분산은 세션당 1회 계산 후 캐시 가능
- 모달 렌더링을 lazy loading으로 변경 가능

---

## 🔧 트러블슈팅

### 문제: 과제 배정 버튼이 보이지 않음
```r
# 브라우저 콘솔 (F12)
$('.assign-btn').length
# 0이면 → 캐시 클리어 후 Ctrl+Shift+R
```

### 문제: abs_variance가 모두 NA
```bash
# 출석 데이터 확인
Rscript -e "
library(arrow)
df <- open_dataset('data/attendance') %>% collect()
table(lubridate::wday(df\$date))  # 요일별 데이터 분포 확인
"
# 최소 2개 이상 요일 필요
```

### 문제: 핫리로드 작동 안 함
```bash
# 파일 권한 확인
ls -l config/assignment_templates.yaml
# -rw-r--r-- 필요

# 강제 타임스탬프 갱신
touch config/assignment_templates.yaml

# 30초 대기 후 확인
```

---

## 📚 관련 문서

- **사용법**: [README_teacher.md](./README_teacher.md)
- **v1.0 구현**: [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)
- **v2.0 상세**: [ENHANCEMENTS_v2.md](./ENHANCEMENTS_v2.md)
- **YAML 통합**: [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)

---

## 🎓 다음 단계

### 즉시 활용 가능
1. 개별 학생 배정으로 맞춤형 개입
2. 요일별 분산으로 출석 패턴 파악
3. 이상 모달로 빠른 학생 그룹화
4. 핫리로드로 운영 중 템플릿 조정

### 권장 워크플로우
```
1. 대시보드 접속
2. 리스크 value box 확인
3. "문항 반응 이상 패턴" 펼치기
4. "Pure Guessing 학생 보기" 클릭
5. 상위 5명 파악
6. 각 학생 테이블에서 "과제 배정" 클릭
7. 출석 분산 높은 학생 → 학부모 상담 메모
8. 주간 리뷰 후 템플릿 수정 (핫리로드로 즉시 반영)
```

---

**Version**: 2.0  
**Date**: 2025-11-06  
**Status**: Production Ready ✅
