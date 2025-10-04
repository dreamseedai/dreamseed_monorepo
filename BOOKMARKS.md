# 🔖 DreamSeed AI 북마크

## 🧪 **실시간 라우팅 히트맵 (간단)**

### **바로 실행**
```bash
./routing-heatmap.sh
```

### **북마크용 한 줄 명령어**
```bash
awk -v since="$(date -d '1 hour ago' +%Y-%m-%dT%H:)" '
  $1 ~ "^ts=" && $1 >= "ts="since { 
    for (i=1;i<=NF;i++) if ($i ~ /^lane=/) lane=$i;
    for (i=1;i<=NF;i++) if ($i ~ /^hint=/) hint=$i;
    gsub(/lane=|hint=|\"/,"",lane); gsub(/hint=|\"/,"",hint);
    split(hint,a,"\\|"); kw=a[1];
    c[lane":"kw]++
  }
  END { for (k in c) print c[k], k | "sort -nr" }' /tmp/router.log | head
```

### **실시간 모니터링**
```bash
# 30초마다 히트맵 업데이트
watch -n 30 './routing-heatmap.sh'

# 실시간 로그
tail -f /tmp/router.log
```

---

## 📌 **운영 한 줄 메모 (주간)**

### **바로 실행**
```bash
./weekly-one-liner.sh
```

### **북마크용 템플릿**
```
[W{week}] P95=<ms> Err=<%> VRAMmax=<%> Fast=<%> Code=<%> ΔP95=<ms> ΔErr=<%> ΔVRAM=<%> → action: <한줄>
```

### **예시**
```
[W40] P95=180ms Err=0.5% VRAMmax=78% Fast=12% Code=8% ΔP95=-20ms ΔErr=-0.2% ΔVRAM=-5% → action: 현재 설정 유지
```

### **회의용 요약**
- **이번 주 핵심 지표**: P95, 에러율, GPU VRAM, 레인 비율
- **변화량**: 전주 대비 Δ 값
- **권장 액션**: 한 줄 처방

---

## 🚀 **가장 자주 쓰는 명령어 TOP 5**

### **1. 6줄 요약**
```bash
./6line-summary.sh
```

### **2. 자동 처방**
```bash
./auto-tuning-prompt.sh "6줄_데이터"
```

### **3. 실시간 히트맵**
```bash
./routing-heatmap.sh
```

### **4. 주간 한 줄 메모**
```bash
./weekly-one-liner.sh
```

### **5. 부하 테스트**
```bash
./load-test-10.sh
```

---

## 📊 **운영 워크플로우**

### **일일 (5분)**
1. `./6line-summary.sh` - 지표 확인
2. `./auto-tuning-prompt.sh` - 문제 시 처방
3. `./load-test-10.sh` - 성능 검증

### **주간 (15분)**
1. `./weekly-one-liner.sh` - 한 줄 메모
2. `./routing-heatmap.sh` - 라우팅 분석
3. `./weekly-comparison.sh` - 주간 비교

### **월간 (30분)**
1. 성과 리뷰
2. 로드맵 업데이트
3. 확장 계획

---

## 🎯 **핵심 원칙**

### **데이터가 말하게 하기**
- 숫자로 판단
- 감정 배제
- 객관적 분석

### **한 줄만 움직이기**
- 작은 변화
- 점진적 개선
- 안정성 우선

### **자동화 활용**
- cron 설정
- Slack 알림
- 스냅샷 저장

---

**💡 이 북마크만 있으면 언제든 운영할 수 있습니다!** 🚀
