# 🗄️ DreamSeedAI MegaCity – Data Lake & Warehouse Architecture (2027–2028)

## Data Lakehouse · Feature Store · Streaming Pipeline · AI Dataset Lifecycle · Global Replication

**버전:** 1.0  
**작성일:** 2025-11-23  
**작성자:** DreamSeedAI Data Engineering · AI Systems Team

---

# 📌 0. 개요 (Overview)

MegaCity의 데이터 규모는 2027–2028년 기준:

```
일일 이벤트: 25M+ events/day
Whisper 음성 데이터: 300k/day
Pose/Motion 데이터: 120k/day
Exam/Attempt 기록: 1.2M/day
Creator Studio 영상: 40k/day
```

이 문서는 DreamSeedAI MegaCity가 운영하는 **차세대 Data Lakehouse 아키텍처**의 공식 기준 문서입니다.

포함 내용:

```
1. Data Lake / Warehouse / Lakehouse 구조
2. Raw → Clean → Curated → Feature Store
3. Batch · Streaming Pipeline
4. AI Dataset Lifecycle
5. GDPR/PIPA 규정 준수형 데이터 관리
6. Multi-region Data Sync
7. BI/Analytics Dashboard
8. Data Governance & Quality 정책
```

---

# 🏛️ 1. Lakehouse Architecture Overview

MegaCity의 데이터 플랫폼은 다음과 같은 **Lakehouse** 구조입니다:

```
Data Producers → Kafka → Data Lake (Raw Zone)
Raw Zone → ETL/ELT → Clean Zone (Parquet)
Clean Zone → Warehouse (BigQuery/Snowflake)
Warehouse → Feature Store (AI/ML)
Feature Store → LLM Fine-tuning / Tutor Engine
```

---

# 🌊 2. Data Lake Zones (3계층)

## 2.1 Raw Zone (변형 금지)

* Whisper 원본 음성
* PoseNet 원본 keypoints
* Exam/Attempt 이벤트 로그
* User interactions

포맷:

```
/audio/raw/
/motion/raw/
/exams/raw/
/events/raw/
```

규칙:

* Immutable
* Expire: 7~30일 (PII 있는 경우 7일)

---

## 2.2 Clean Zone (정제된 구조)

* Parquet 기반
* Partition by date
* PII 제거 or pseudonymized

예:

```
/exams/clean/dt=2025-11-23/exam.parquet
/kzone/clean/dt=2025-11-23/voice.parquet
```

---

## 2.3 Curated Zone (BI/ML 최적화)

* Aggregated tables
* Fact & Dimension 모델

예:

```
fact_attempts
fact_kzone_voice
fact_motion_scores
fact_user_engagement
```

---

# 🧮 3. Warehouse Architecture

Warehouse는 Snowflake/BigQuery 중 선택 (2027 기준 BigQuery 권장).

### 구성 요소:

```
Fact tables
Dimension tables
Materialized views
BI tables (Grafana/Metabase)
```

### 주요 Fact 모델

```
fact_attempts (exam_id, user_id, score, time_spent)
fact_voice_analysis (user_id, accuracy, prosody)
fact_motion_analysis (user_id, similarity_score)
fact_ai_usage (tokens, cost)
```

---

# 🔥 4. Streaming Architecture (실시간 분석)

MegaCity는 Kafka 기반 Streaming Pipeline을 사용.

### 주 스트림

```
exam.events
kzone.voice.events
kzone.motion.events
ai.usage.events
auth.login.events
```

### Streaming 처리

```
Kafka → Flink/Spark Streaming → Clean Zone → Warehouse
```

### 사용 사례

* 실시간 Dashboard (Teacher/Parent)
* AI Tutor 실시간 피드백
* Creator Studio 처리 파이프라인

---

# 🧠 5. AI Dataset Lifecycle (LLM Fine-tuning)

AI Training을 위한 Dataset은 다음 단계를 거칩니다:

```
Raw → Clean → Labeled → Feature Store → Training Set → Archive
```

## 5.1 Whisper Dataset

* 발음/억양/감정 분석용 라벨 생성

## 5.2 Motion Dataset

* Pose keypoints → DTW alignment → 정규화

## 5.3 Essay/Explanation Dataset

* Student essays → GPT-assisted labeling

## 5.4 안전 규칙

* 얼굴/음성 PII 제거
* 지역 규제 (GDPR/PIPA) 준수

---

# 📦 6. Feature Store (AI/ML)

### 목적

* Tutor Engine의 실시간 피드백을 위한 모델 입력 준비

### 주요 Feature 그룹

```
student_skill_vector
voice_accuracy_vector
motion_similarity_vector
engagement_vector
learning_path_vector
```

Feature Store는 Redis + Parquet + BigQuery 조합 사용.

---

# 🌍 7. Multi-Region Data Replication

MegaCity V2/V3의 Multi-Region 구조와 일치.

### 원칙

```
1) PII는 지역 내 저장 (Locality)
2) 모델 학습용 Feature는 pseudonymized 후 global sync
3) Warehouse는 Multi-Region Read
```

### 구성

```
Seoul → Primary
Tokyo → APAC Copy
Virginia → US Copy
Frankfurt → EU Copy
```

---

# 🔐 8. Privacy & Compliance

### GDPR/PIPA 준수 전략

```
PII Minimization
PII Early Drop (Raw → Clean)
7일 retention on sensitive data
User deletion (Right to be forgotten)
DPIA for AI datasets
```

### 민감한 데이터

* 얼굴, 음성, Motion raw data → 7일 후 삭제

---

# 📊 9. BI & Analytics

### Dashboard 구성 (Metabase/Grafana)

```
Learning Progress Dashboard
K-Zone Voice Dashboard
K-Zone Motion Dashboard
AI Usage Dashboard
Exam Performance Trends
Revenue/ARPU Dashboard
```

---

# 📏 10. Data Quality Standards

### DQ 지표

```
Freshness (D+1)
Completeness (> 98%)
Consistency (> 99%)
Accuracy (domain rules)
Validity (schema checks)
```

### Data Contract

* Schema versioning 필수
* Backward compatibility 유지

---

# 🔄 11. ETL/ELT Orchestration

## 11.1 Orchestration Tools

```
Primary: Apache Airflow
Alternative: Prefect / Dagster
Scheduling: Cron + Event-driven
```

## 11.2 주요 DAGs

```
daily_exam_processing
hourly_kzone_aggregation
weekly_ai_dataset_preparation
monthly_warehouse_optimization
user_deletion_pipeline (GDPR)
```

## 11.3 Job Monitoring

```
Success Rate > 99%
Job Duration SLO
Data Quality Checks per stage
Alert on failure → Slack/PagerDuty
```

---

# 💾 12. Storage Strategy

## 12.1 Storage Tiers

```
Hot Storage (0-30 days): SSD/Premium
Warm Storage (31-365 days): Standard
Cold Storage (1+ years): Archive/Glacier
```

## 12.2 Cost Optimization

```
Automatic tiering
Compression (Parquet + Snappy)
Partitioning by date/zone
Lifecycle policies
```

## 12.3 Storage Locations

```
Raw Zone: Cloudflare R2 / AWS S3
Clean Zone: BigQuery / Snowflake
Feature Store: Redis + S3
Archive: Glacier Deep Archive
```

---

# 🔍 13. Data Catalog & Discovery

## 13.1 Metadata Management

```
Tool: DataHub / Amundsen
Metadata: Schema, Lineage, Owners
Documentation: Description, SLA
Tags: PII, Sensitive, Public
```

## 13.2 Data Lineage

```
Source → Raw → Clean → Curated → BI
Auto-discovery via Airflow integration
Impact analysis for changes
```

## 13.3 Search & Discovery

```
Natural language search
Tag-based filtering
Owner-based access
Usage analytics
```

---

# 🛡️ 14. Data Security & Access Control

## 14.1 Access Levels

```
L1: Public (aggregated, anonymized)
L2: Internal (pseudonymized)
L3: Restricted (PII, sensitive)
L4: Admin (full access)
```

## 14.2 Authentication & Authorization

```
SSO integration
Role-based access (RBAC)
Attribute-based access (ABAC)
Audit logging for all access
```

## 14.3 Encryption

```
At Rest: AES-256
In Transit: TLS 1.3
Column-level encryption for PII
Key rotation every 90 days
```

---

# 🏁 15. 결론

MegaCity Data Lake & Warehouse Architecture는 DreamSeedAI의 글로벌 AI 도시를 지탱하는  
**데이터 중심 플랫폼 전략의 핵심 기반**입니다.

AI Tutor, K-Zone, Analytics, Multi-region 서비스 모두 이 데이터 플랫폼 위에서 안전하고 일관되게 작동합니다.

이 아키텍처는 확장성, 보안성, 규제 준수를 모두 충족하며,  
2027-2028년 글로벌 확장을 위한 데이터 인프라의 청사진입니다.
