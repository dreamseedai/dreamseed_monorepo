# r-irt-plumber Anchors 처리 가이드

**작성일**: 2025-11-02  
**상태**: 📋 R 서비스 측 구현 필요

---

## 개요

Python 측에서는 anchors를 로드하고 페이로드에 포함시켜 `/irt/calibrate` 엔드포인트로 전송합니다.  
R 서비스 측에서 anchors를 처리하여 linking constants를 계산하고 반환해야 합니다.

---

## Python 측 구현 (완료)

**파일**: `apps/seedtest_api/jobs/mirt_calibrate.py`

### Anchors 로드

```python
# _load_anchors() 함수에서:
# - question.meta->'tags'에 'anchor' 포함된 아이템 로드
# - question.meta->'irt'에서 파라미터 (a, b, c) 추출
# - anchors 배열 생성
```

### 페이로드 구조

```json
{
  "observations": [
    {
      "user_id": "uuid",
      "item_id": "item-id",
      "is_correct": true,
      "responded_at": "2025-11-02T12:00:00Z"
    }
  ],
  "model": "2PL",
  "anchors": [
    {
      "item_id": "anchor-item-id",
      "params": {
        "a": 1.0,
        "b": 0.0,
        "c": 0.2  // 3PL만
      },
      "fixed": true
    }
  ]
}
```

### 응답 기대 구조

```json
{
  "item_params": [
    {
      "item_id": "item-id",
      "params": {"a": 1.2, "b": -0.6, "c": 0.2},
      "model": "2PL",
      "version": "v1"
    }
  ],
  "abilities": [
    {
      "user_id": "uuid",
      "theta": 0.85,
      "se": 0.15,
      "model": "2PL",
      "version": "v1"
    }
  ],
  "fit_meta": {
    "run_id": "fit-2025-11-02T03:00:00Z",
    "linking_constants": {
      "A": 1.0,  // Slope constant
      "B": 0.0   // Intercept constant
    },
    "metrics": {
      "aic": 12345.67,
      "bic": 12456.78,
      "loglik": -6123.45
    }
  }
}
```

---

## R 서비스 측 구현 (필요)

### 1. Plumber 엔드포인트 수정

**파일**: `r-irt-plumber/api.R` (또는 해당 플러머 파일)

```r
#* @post /irt/calibrate
#* @param observations:list
#* @param model:character
#* @param anchors:list (optional)
function(req, res) {
  observations <- req$body$observations
  model <- req$body$model %||% "2PL"
  anchors <- req$body$anchors
  
  # 1. 데이터 변환
  obs_df <- data.frame(
    user_id = sapply(observations, function(x) x$user_id),
    item_id = sapply(observations, function(x) x$item_id),
    is_correct = sapply(observations, function(x) as.integer(x$is_correct)),
    responded_at = sapply(observations, function(x) x$responded_at)
  )
  
  # 2. Anchors 처리 (있는 경우)
  linking_constants <- NULL
  
  if (!is.null(anchors) && length(anchors) > 0) {
    # Anchor 파라미터 추출
    anchor_items <- sapply(anchors, function(a) a$item_id)
    anchor_params <- lapply(anchors, function(a) {
      list(
        item_id = a$item_id,
        a = a$params$a,
        b = a$params$b,
        c = a$params$c %||% 0,
        fixed = a$fixed %||% FALSE
      )
    })
    
    # 3. IRT 모델 적합 (anchors 고정)
    # 예: mirt 패키지 사용
    library(mirt)
    
    # Anchor 아이템을 고정 파라미터로 설정
    # 모델 specification에 anchors 포함
    # ... (mirt 모델 적합 코드)
    
    # 4. Linking constants 계산
    # 예: Stocking-Lord 또는 Mean/Mean 방법
    linking_constants <- calculate_linking_constants(
      anchor_items = anchor_items,
      anchor_params = anchor_params,
      calibrated_params = item_params  # 캘리브레이션 결과
    )
  } else {
    # Anchors 없이 일반 캘리브레이션
    # ... (기존 캘리브레이션 코드)
  }
  
  # 5. 결과 반환
  list(
    item_params = item_params_list,
    abilities = abilities_list,
    fit_meta = list(
      run_id = generate_run_id(),
      linking_constants = linking_constants,  # NULL 또는 constants
      metrics = list(
        aic = model_fit$aic,
        bic = model_fit$bic,
        loglik = model_fit$loglik
      )
    )
  )
}
```

### 2. Linking Constants 계산 함수

```r
calculate_linking_constants <- function(anchor_items, anchor_params, calibrated_params) {
  # Stocking-Lord 방법 예시
  # 또는 Mean/Mean 방법
  
  # Anchor 아이템의 원래 파라미터
  anchor_b_original <- sapply(anchor_params, function(p) p$b)
  
  # 캘리브레이션된 파라미터
  calibrated_b <- sapply(
    calibrated_params[calibrated_params$item_id %in% anchor_items],
    function(p) p$b
  )
  
  # Slope (A) 계산: Mean/Mean 방법
  # A = mean(calibrated_b) / mean(anchor_b_original)
  A <- mean(calibrated_b) / mean(anchor_b_original)
  
  # Intercept (B) 계산
  # B = mean(calibrated_b) - A * mean(anchor_b_original)
  B <- mean(calibrated_b) - A * mean(anchor_b_original)
  
  list(
    A = A,
    B = B,
    method = "mean_mean"  # 또는 "stocking_lord"
  )
}
```

### 3. 예시: mirt 패키지 사용

```r
library(mirt)

# Anchors가 있는 경우
if (!is.null(anchors) && length(anchors) > 0) {
  # 모델 specification에 고정 파라미터 설정
  model_spec <- mirt.model('F1 = 1-20')
  
  # Anchor 아이템의 파라미터 고정
  sv <- mirt(data, model_spec, pars = 'values')
  for (anchor in anchors) {
    item_idx <- which(items == anchor$item_id)
    if (length(item_idx) > 0) {
      sv[sv$item == item_idx & sv$name == 'a1', 'value'] <- anchor$params$a
      sv[sv$item == item_idx & sv$name == 'd', 'value'] <- -anchor$params$a * anchor$params$b
      sv[sv$item == item_idx & sv$name == 'g', 'value'] <- anchor$params$c
      sv[sv$item == item_idx & sv$name == 'u', 'value'] <- 1
      sv[sv$item == item_idx & sv$name %in% c('a1', 'd', 'g', 'u'), 'est'] <- FALSE
    }
  }
  
  # 모델 적합
  model <- mirt(data, model_spec, pars = sv, verbose = FALSE)
  
  # Linking constants 계산
  linking_constants <- calculate_linking_constants(...)
} else {
  # 일반 캘리브레이션
  model <- mirt(data, model_spec, verbose = FALSE)
}
```

---

## 테스트 절차

### 1. Python 측 테스트

```bash
# Dry-run으로 anchors 로드 확인
DRY_RUN=true python -m apps.seedtest_api.jobs.mirt_calibrate

# 실제 실행
python -m apps.seedtest_api.jobs.mirt_calibrate
```

**로그에서 확인**:
```
[INFO] Loaded 5 anchors/seeds from question.meta
[INFO] Model: 2PL, Anchors: 5
```

### 2. R 서비스 테스트

```bash
# r-irt-plumber Pod에서 직접 테스트
kubectl -n seedtest exec deploy/r-irt-plumber -c api -- \
  curl -X POST http://localhost:8000/irt/calibrate \
    -H "Content-Type: application/json" \
    -d '{
      "observations": [...],
      "model": "2PL",
      "anchors": [...]
    }'
```

### 3. 통합 테스트

```sql
-- Linking constants 저장 확인
SELECT 
    run_id,
    model_spec->'linking_constants' AS linking_constants,
    fitted_at
FROM mirt_fit_meta
WHERE model_spec ? 'linking_constants'
ORDER BY fitted_at DESC
LIMIT 1;
```

---

## 문제 해결

### Anchors가 로드되지 않음

**원인**: `question.meta.tags`에 "anchor" 태그 없음

**해결**:
```bash
# Anchor 아이템 태깅
python -m apps.seedtest_api.jobs.tag_anchor_items
```

### Linking constants가 반환되지 않음

**원인**: R 서비스 측 anchors 처리 미구현

**해결**: 위의 R 코드 예시를 참고하여 `/irt/calibrate` 엔드포인트 수정

### Linking constants 계산 오류

**원인**: Anchor 파라미터 불일치 또는 데이터 문제

**해결**:
- Anchor 아이템의 파라미터 확인
- 충분한 anchor 아이템 수 확보 (최소 3-5개 권장)

---

## 참고 자료

- **mirt 패키지 문서**: https://cran.r-project.org/web/packages/mirt/
- **IRT Linking/Equating**: Stocking-Lord, Mean/Mean 방법
- **Python 측 구현**: `apps/seedtest_api/jobs/mirt_calibrate.py`

---

## 다음 단계

1. **R 서비스 측 구현**: 위의 예시 코드를 기반으로 `/irt/calibrate` 엔드포인트 수정
2. **테스트**: Anchors 포함 캘리브레이션 실행 및 linking constants 확인
3. **검증**: 리포트 템플릿에서 linking constants 표시 확인

**Python 측 준비 완료! R 서비스 측 구현 필요** 🔧

