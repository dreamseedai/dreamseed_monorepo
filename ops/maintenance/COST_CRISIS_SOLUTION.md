# 💸 클라우드 비용 폭탄 방지 가이드

> **실전 경험 기반**: GCP $1,600/월 청구 사태 → $200~$300/월로 전환  
> **작성일**: 2025년 11월 10일  
> **대상**: DreamSeedAI 스타트업 런웨이 전략

---

## 📌 Executive Summary

### 비용 폭탄 사례
- **GCP 청구**: $1,600/월 (Kubernetes 24/7이 80% 차지)
- **Lambda 비용**: $400/주 (급하게 RTX 5090 구입)
- **원인**: "항상 켜진 리소스" + 자동 확장 제한 없음

### 해결책 요약
- **목표**: 월 $200~$300으로 초기 서비스 운영
- **전략**: Scale-to-zero + 로컬 GPU + 예산 상한
- **결과**: 수익 전환 전까지 6~12개월 런웨이 확보

---

## 🚨 A) 즉시 체크리스트 (오늘 바로 적용)

### 1️⃣ 예산/알림/자동차단

```bash
# GCP Budget 설정
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="DreamSeedAI Monthly Budget" \
  --budget-amount=300USD \
  --threshold-rule=percent=50 \
  --threshold-rule=percent=80 \
  --threshold-rule=percent=100

# 알림 채널 설정 (Slack/Email)
gcloud alpha monitoring channels create \
  --display-name="Budget Alert" \
  --type=slack \
  --channel-labels=url=SLACK_WEBHOOK_URL
```

**3단계 알림**:
- 50% ($150): ⚠️ Warning (검토 필요)
- 80% ($240): 🔴 Critical (즉시 점검)
- 100% ($300): 🚫 Emergency (수동 승인 필요)

### 2️⃣ 항상 켜진 리소스 제거

#### GKE 자동 확장 설정
```yaml
# cluster-autoscaler.yaml
apiVersion: autoscaling/v1
kind: HorizontalPodAutoscaler
metadata:
  name: api-server-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api-server
  minReplicas: 0  # 요청 없으면 0으로
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
```

#### Cloud Run으로 전환 (권장)
```bash
# 기존 GKE 서비스를 Cloud Run으로 마이그레이션
gcloud run deploy api-server \
  --image gcr.io/PROJECT_ID/api-server \
  --platform managed \
  --region asia-northeast3 \
  --allow-unauthenticated \
  --min-instances 0 \  # Scale to zero
  --max-instances 10 \
  --cpu 2 \
  --memory 4Gi \
  --timeout 300
```

**비용 비교**:
- GKE 24/7: e2-medium 3대 = **$73/월**
- Cloud Run: 유휴 시 $0, 피크 시 **$20~50/월**

### 3️⃣ 스팟/선점형 VM 사용

```bash
# Spot VM 생성 (70% 할인)
gcloud compute instances create gpu-worker-spot \
  --zone=asia-northeast3-a \
  --machine-type=n1-standard-4 \
  --preemptible \  # 70% 할인
  --maintenance-policy=TERMINATE
```

**언제 사용**:
- ✅ 배치 작업 (AI 모델 학습, 데이터 전처리)
- ✅ 비필수 워크로드 (로그 분석, 백업)
- ❌ 실시간 API 서버 (중단 위험)

### 4️⃣ 라벨링 & 비용 추적

```bash
# 모든 리소스에 라벨 추가
gcloud compute instances add-labels INSTANCE_NAME \
  --labels=env=production,app=dreamseed,owner=platform,cost-center=ai-inference

# 비용 리포트 내보내기
gcloud billing export to-bigquery \
  --billing-account=BILLING_ACCOUNT_ID \
  --dataset=billing_export
```

**라벨 전략**:
- `env`: production, staging, dev
- `app`: dreamseed, admin, analytics
- `owner`: platform, data, ml
- `cost-center`: ai-inference, storage, network

### 5️⃣ 네트워크 비용 차단

#### Cloudflare 앞단 배치
```nginx
# Cloudflare를 통한 트래픽 캐싱
# 정적 자산 캐시율 95% 이상 유지
# GCP Egress 비용 거의 0
```

**네트워크 비용 최적화**:
- ✅ Cloudflare CDN: 무제한 트래픽 (Pro $20/월)
- ✅ 같은 리전 내 통신: VPC 내부 통신 무료
- ❌ Cross-region 트래픽: GB당 $0.12 (피할 것)
- ❌ 외부 Egress: GB당 $0.12~$0.23 (CDN으로 차단)

---

## 💡 B) Scale-to-Zero 전략

### 개념
> **"사용하지 않으면 0원"**  
> 요청이 없을 때 자동으로 인스턴스 수를 0으로 줄이는 구조

### 적용 가능한 서비스

| 서비스 | Scale-to-Zero | 비용 |
|--------|---------------|------|
| **Cloud Run** | ✅ 기본 지원 | 요청당 과금 |
| **Cloud Functions** | ✅ 기본 지원 | 호출당 과금 |
| **GKE Autopilot** | ✅ HPA로 가능 | Pod 실행 시간 과금 |
| **Compute Engine** | ❌ 불가능 | 24/7 과금 |
| **Fly.io** | ✅ 기본 지원 | 유휴 시 무료 |
| **Render** | ✅ 기본 지원 | 유휴 시 슬립 |

### Cloud Run 설정 예시

```yaml
# service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: dreamseed-api
spec:
  template:
    metadata:
      annotations:
        autoscaling.knative.dev/minScale: "0"  # 유휴 시 0
        autoscaling.knative.dev/maxScale: "10"  # 최대 10
        autoscaling.knative.dev/target: "80"  # CPU 80% 이상 시 확장
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/api
        resources:
          limits:
            cpu: "2"
            memory: "4Gi"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
```

**Cold Start 대응**:
- API 응답 시간: 첫 요청 ~2초 (이후 <100ms)
- 사용자 경험: "로딩 중..." 표시로 커버
- 비용 절감: 야간/주말 유휴 시 **$0**

---

## 📊 C) 비용 구조 분석

### GCP $1,600/월 청구 내역 (추정)

| 항목 | 비용 | 비율 | 최적화 후 |
|------|------|------|-----------|
| **GKE Kubernetes** | $1,280 | 80% | **$0** (Cloud Run 전환) |
| Compute Engine VM | $200 | 12.5% | **$30** (Spot VM) |
| Cloud Storage | $50 | 3.1% | **$20** (R2 전환) |
| Network Egress | $40 | 2.5% | **$5** (Cloudflare CDN) |
| Cloud SQL | $30 | 1.9% | **$0** (로컬 Postgres) |
| **합계** | **$1,600** | **100%** | **$55** |

### 최적화 전략별 절감액

```
1️⃣ GKE → Cloud Run 전환:        -$1,260/월 (79% 절감)
2️⃣ VM → Spot Instance:          -$170/월 (85% 절감)
3️⃣ Storage → R2/Cloudflare:     -$30/월 (60% 절감)
4️⃣ Egress → CDN:                -$35/월 (88% 절감)
5️⃣ Cloud SQL → 로컬 Postgres:   -$30/월 (100% 절감)
───────────────────────────────────────────────
총 절감액:                       -$1,525/월 (95% 절감)
최종 비용:                       $75/월
```

---

## 🎯 D) "Always Off" 원칙

### 핵심 철학
> **"기본은 꺼져 있고, 필요할 때만 켜진다"**

### 체크리스트

**클라우드 리소스 감사**:
```bash
# 모든 VM 확인
gcloud compute instances list --format="table(name,zone,status,machineType)"

# 24/7 실행 중인 인스턴스 식별
gcloud compute instances list --filter="status=RUNNING" \
  --format="table(name,creationTimestamp)"

# 7일 이상 실행 중인 VM (삭제 대상)
gcloud compute instances list \
  --filter="status=RUNNING AND creationTimestamp<-P7D" \
  --format="value(name)"
```

**자동 정리 스크립트**:
```bash
#!/bin/bash
# auto-cleanup.sh - 야간 리소스 정리

# 개발/스테이징 환경 자동 정지 (평일 자정~오전 7시)
if [ $(date +%H) -ge 0 ] && [ $(date +%H) -lt 7 ]; then
  gcloud compute instances stop $(gcloud compute instances list \
    --filter="labels.env=dev OR labels.env=staging" \
    --format="value(name)")
fi

# 7일 이상 된 스냅샷 삭제
gcloud compute snapshots list \
  --filter="creationTimestamp<-P7D" \
  --format="value(name)" | xargs -I {} gcloud compute snapshots delete {} --quiet
```

**Cron 설정**:
```cron
# 매일 자정 실행
0 0 * * * /home/scripts/auto-cleanup.sh

# 매주 일요일 리소스 감사
0 9 * * 0 /home/scripts/resource-audit.sh
```

---

## 🛡️ E) 비상 차단 시스템

### Cloud Function으로 자동 차단

```python
# budget_enforcer.py
import os
from google.cloud import compute_v1

def enforce_budget(event, context):
    """예산 100% 초과 시 자동으로 모든 VM 정지"""
    
    budget_amount = float(event['attributes']['budgetAmount'])
    cost_amount = float(event['attributes']['costAmount'])
    
    if cost_amount >= budget_amount:
        # 모든 non-production VM 정지
        client = compute_v1.InstancesClient()
        project = os.getenv('PROJECT_ID')
        
        for zone in ['asia-northeast3-a', 'asia-northeast3-b']:
            instances = client.list(project=project, zone=zone)
            
            for instance in instances:
                # production 라벨 없으면 정지
                if 'production' not in instance.labels:
                    client.stop(project=project, zone=zone, instance=instance.name)
                    print(f"Stopped: {instance.name}")
```

**배포**:
```bash
gcloud functions deploy budget-enforcer \
  --runtime python39 \
  --trigger-topic budget-alerts \
  --entry-point enforce_budget
```

---

## 📈 F) 비용 모니터링 대시보드

### Grafana 대시보드 구성

```yaml
# grafana-dashboard.json (샘플)
{
  "dashboard": {
    "title": "DreamSeedAI Cost Monitoring",
    "panels": [
      {
        "title": "Daily Cost Trend",
        "targets": [
          {
            "expr": "sum(gcp_billing_cost) by (service)"
          }
        ]
      },
      {
        "title": "Budget vs Actual",
        "gauge": {
          "maxValue": 300,
          "thresholds": [150, 240, 300]
        }
      },
      {
        "title": "Top 5 Cost Centers",
        "type": "bar"
      }
    ]
  }
}
```

### 주간 비용 리포트 자동화

```python
# weekly_cost_report.py
import pandas as pd
from google.cloud import bigquery

def generate_weekly_report():
    client = bigquery.Client()
    
    query = """
    SELECT 
      service.description AS service,
      SUM(cost) AS total_cost,
      DATE_TRUNC(usage_start_time, WEEK) AS week
    FROM `PROJECT_ID.billing_export.gcp_billing_export`
    WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    GROUP BY service, week
    ORDER BY total_cost DESC
    """
    
    df = client.query(query).to_dataframe()
    
    # Slack으로 전송
    import requests
    slack_webhook = os.getenv('SLACK_WEBHOOK')
    
    message = f"""
    📊 **주간 비용 리포트** (지난 7일)
    
    총 비용: ${df['total_cost'].sum():.2f}
    
    Top 5 서비스:
    {df.head(5).to_string(index=False)}
    """
    
    requests.post(slack_webhook, json={"text": message})
```

---

## ⚡ G) 즉시 적용 액션 플랜 (Day 1~3)

### Day 1: 긴급 차단 (2시간)

```bash
# 1. 모든 GKE 클러스터 확인
gcloud container clusters list

# 2. 사용하지 않는 클러스터 삭제
gcloud container clusters delete CLUSTER_NAME --zone=ZONE

# 3. 남은 클러스터는 Autopilot으로 전환 (또는 삭제)
gcloud container clusters update CLUSTER_NAME \
  --enable-autoscaling \
  --min-nodes=0 \
  --max-nodes=5

# 4. Cloud Run으로 API 서버 마이그레이션
gcloud run deploy api-server \
  --image gcr.io/PROJECT_ID/api-server \
  --min-instances=0 \
  --max-instances=10
```

### Day 2: 예산 설정 (1시간)

```bash
# 1. 예산 생성
gcloud billing budgets create \
  --billing-account=BILLING_ACCOUNT_ID \
  --display-name="Monthly Budget" \
  --budget-amount=300USD

# 2. Slack 알림 설정
# (Slack Webhook URL 필요)

# 3. 비용 내보내기 활성화
gcloud billing export to-bigquery \
  --billing-account=BILLING_ACCOUNT_ID \
  --dataset=billing_export
```

### Day 3: 리소스 정리 (3시간)

```bash
# 1. 오래된 스냅샷 삭제
gcloud compute snapshots list --filter="creationTimestamp<-P30D" \
  --format="value(name)" | xargs gcloud compute snapshots delete --quiet

# 2. 사용하지 않는 디스크 삭제
gcloud compute disks list --filter="NOT users:*" \
  --format="value(name,zone)" | while read name zone; do
    gcloud compute disks delete $name --zone=$zone --quiet
  done

# 3. 라벨 일괄 추가 (비용 추적용)
for instance in $(gcloud compute instances list --format="value(name,zone)"); do
  gcloud compute instances add-labels $instance --labels=cost-tracking=enabled
done
```

---

## 📋 H) 체크리스트

### ✅ 즉시 적용 (Day 1)
- [ ] GCP Budget 설정 ($300 상한)
- [ ] GKE 클러스터 삭제 또는 Autopilot 전환
- [ ] Cloud Run으로 API 서버 마이그레이션
- [ ] 비용 알림 채널 설정 (Slack/Email)

### ✅ 단기 (Week 1)
- [ ] 모든 리소스에 라벨 추가 (env, app, owner)
- [ ] Scale-to-zero 정책 적용
- [ ] Spot/Preemptible VM으로 전환
- [ ] 네트워크 Egress 비용 확인 (Cloudflare CDN 적용)

### ✅ 중기 (Month 1)
- [ ] 주간 비용 리포트 자동화
- [ ] Grafana 비용 대시보드 구축
- [ ] 자동 정리 스크립트 Cron 설정
- [ ] 비상 차단 시스템 구축 (Cloud Function)

### ✅ 장기 (Quarter 1)
- [ ] 월별 비용 추세 분석
- [ ] RI (Reserved Instances) 검토 (안정적 워크로드만)
- [ ] 멀티 클라우드 전략 (GCP + 로컬 GPU)
- [ ] 비용 최적화 KPI 설정 (Cost per User)

---

## 🎓 I) 교훈

### 비용 폭탄의 3대 원인
1. **"항상 켜진" 리소스**: GKE, Compute Engine 24/7 실행
2. **자동 확장 제한 없음**: 무제한 스케일링
3. **비용 가시성 부족**: 청구서 받기 전까지 모름

### 스타트업 생존 원칙
1. **"기본은 OFF"**: Scale-to-zero가 기본
2. **"예산이 법"**: 예산 상한 절대 지키기
3. **"주간 리뷰"**: 매주 비용 추세 확인
4. **"라벨링 필수"**: 누가 얼마 쓰는지 즉시 파악

### DreamSeedAI 적용
- **현재**: GCP $1,600/월 + Lambda $400/주 = 재앙
- **최적화 후**: Cloud Run + 로컬 GPU = **$200~$300/월**
- **런웨이**: $20,000 / $250/월 = **80개월** (6.6년 생존 가능)

---

## 🚀 J) 다음 단계

이제 비용 폭탄은 막았습니다. 다음은:

1. **HYBRID_ARCHITECTURE.md**: 로컬 RTX 5090 + 최소 클라우드 설계
2. **ELASTIC_SCALING_PLAN.md**: 유저 수 기반 단계별 확장 전략

이 3개 문서를 합치면 **"스타트업 생존 전략 완결판"**이 됩니다.

---

**작성**: GitHub Copilot  
**날짜**: 2025년 11월 10일  
**버전**: 1.0  
**다음 문서**: [HYBRID_ARCHITECTURE.md](./HYBRID_ARCHITECTURE.md)
