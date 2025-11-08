# IRT 드리프트 제어 시스템 - 완전 구현 가이드

## 개요

문항 파라미터(a, b, c)의 시간적 드리프트를 감지하여 적응형 테스트 엔진의 정확도와 공정성을 유지하는 시스템입니다.

### 핵심 기능
1. **3PL/MIRT 재보정**: 최근 응답 데이터로 주기적 파라미터 업데이트
2. **베이지안 드리프트 감지**: 기준 대비 파라미터 변화의 사후분포 계산
3. **자동 플래그**: 임계치 초과 문항 자동 감지 및 알림
4. **노출 제어 연동**: 플래그 문항의 노출 확률 자동 조정

---

## 1. 시스템 아키텍처

```
┌─────────────────┐
│ 응답 로그 DB    │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────┐
│ Celery 배치 (주 1회)        │
│ - 이동창 샘플링 (8주)       │
│ - mirt 재보정               │
│ - Stan 베이지안 업데이트    │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ R Plumber API               │
│ - /drift/run                │
│ - /drift/items              │
│ - /params/latest            │
└────────┬────────────────────┘
         │
         ├──────────────┬──────────────┐
         ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ FastAPI      │ │ 교사 대시보드│ │ 노출 제어    │
│ (Python)     │ │ (Shiny)      │ │ 엔진         │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 2. 데이터베이스 스키마

### 2.1 기준 파라미터 테이블

```sql
CREATE TABLE IF NOT EXISTS irt_item_params_baseline(
  item_id TEXT PRIMARY KEY,
  model   TEXT NOT NULL,          -- '3PL-1D', '2PL-MD[K=2]' 등
  a       DOUBLE PRECISION,       -- 변별도
  b       DOUBLE PRECISION,       -- 난이도
  c       DOUBLE PRECISION,       -- 추측도
  se_a    DOUBLE PRECISION,       -- 표준오차
  se_b    DOUBLE PRECISION,
  se_c    DOUBLE PRECISION,
  k       INT DEFAULT 1,          -- 차원 수
  a_vec   JSONB,                  -- 다차원 a 벡터
  taken_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_baseline_model ON irt_item_params_baseline(model);
```

### 2.2 최신 파라미터 테이블

```sql
CREATE TABLE IF NOT EXISTS irt_item_params_latest(
  item_id TEXT PRIMARY KEY,
  model   TEXT NOT NULL,
  a       DOUBLE PRECISION,
  b       DOUBLE PRECISION,
  c       DOUBLE PRECISION,
  se_a    DOUBLE PRECISION,
  se_b    DOUBLE PRECISION,
  se_c    DOUBLE PRECISION,
  k       INT DEFAULT 1,
  a_vec   JSONB,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_latest_updated ON irt_item_params_latest(updated_at DESC);
```

### 2.3 드리프트 로그 테이블

```sql
CREATE TABLE IF NOT EXISTS item_drift_log(
  id BIGSERIAL PRIMARY KEY,
  t_window_d TEXT NOT NULL,        -- '2025-09-01..2025-10-27'
  item_id TEXT NOT NULL,
  model TEXT NOT NULL,
  k INT DEFAULT 1,
  
  -- 파라미터 변화량
  delta_a DOUBLE PRECISION,
  delta_b DOUBLE PRECISION,
  delta_c DOUBLE PRECISION,
  
  -- 신뢰구간
  ci_a_low DOUBLE PRECISION,
  ci_a_high DOUBLE PRECISION,
  ci_b_low DOUBLE PRECISION,
  ci_b_high DOUBLE PRECISION,
  ci_c_low DOUBLE PRECISION,
  ci_c_high DOUBLE PRECISION,
  
  -- 사후확률 P(|Δ|>τ)
  p_abs_a DOUBLE PRECISION,
  p_abs_b DOUBLE PRECISION,
  p_abs_c DOUBLE PRECISION,
  
  -- 플래그
  flag_a BOOLEAN DEFAULT FALSE,
  flag_b BOOLEAN DEFAULT FALSE,
  flag_c BOOLEAN DEFAULT FALSE,
  
  n_resp INT,                      -- 응답 수
  raw JSONB,                       -- 원본 데이터
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_drift_created ON item_drift_log(created_at DESC);
CREATE INDEX idx_drift_flags ON item_drift_log(flag_a, flag_b, flag_c) 
  WHERE flag_a OR flag_b OR flag_c;
CREATE INDEX idx_drift_item ON item_drift_log(item_id, created_at DESC);
```

### 2.4 응답 데이터 뷰

```sql
CREATE OR REPLACE VIEW view_item_responses_recent AS
SELECT 
  user_id,
  item_id,
  CASE WHEN score >= 0.5 THEN 1 ELSE 0 END AS correct,
  created_at AS ts
FROM responses
WHERE created_at >= NOW() - INTERVAL '56 days'  -- 8주
  AND status = 'completed';
```

---

## 3. R 파이프라인 구현

파일 위치: `/portal_front/r-irt-plumber/irt_drift_pipeline.R`

### 3.1 설정

```r
DRIFT_CONF <- list(
  window_days     = 56,          # 8주
  min_resp_per_it = 200,         # 문항당 최소 응답수
  tau_b           = 0.20,        # |Δb| 임계
  tau_a           = 0.15,        # |Δa| 임계
  tau_c           = 0.05,        # |Δc| 임계
  prob_thresh     = 0.95,        # P(|Δ|>τ) >= 0.95
  use_multidim    = TRUE,
  multidim_K      = 2,
  use_3pl         = TRUE
)
```

### 3.2 주요 함수

- `run_drift()`: 메인 파이프라인 실행
- `fit_mirt()`: mirt 재보정
- `prep_stan_data()`: Stan 데이터 준비
- `post_delta_summaries()`: 사후분포 요약
- `get_latest_params()`: 최신 파라미터 조회
- `get_drift_items()`: 드리프트 문항 조회

---

## 4. Plumber API 구현

파일 위치: `/portal_front/r-irt-plumber/plumber_drift.R`

### 4.1 엔드포인트

#### POST /drift/run
드리프트 감지 파이프라인 실행

**Request:**
```json
{
  "use_3pl": true,
  "multidim": true,
  "K": 2,
  "iter": 1000,
  "chains": 2
}
```

**Response:**
```json
{
  "window": "2025-09-01..2025-10-27",
  "n_resp": 15234,
  "n_items": 450,
  "flags": 23,
  "drift": [...]
}
```

#### GET /drift/items
플래그된 문항 조회

**Parameters:**
- `since_days`: 조회 기간 (기본 30일)
- `only_flagged`: 플래그만 조회 (기본 true)
- `limit`: 최대 결과 수 (기본 500)

#### POST /params/latest
최신 파라미터 조회

**Request:**
```json
{
  "item_ids": ["MATH_1023", "PHYS_2212"]
}
```

---

## 5. FastAPI 통합

파일 위치: `/apps/seedtest_api/routers/irt_drift.py`

```python
"""IRT 드리프트 감지 API 라우터

R Plumber 백엔드와 통합하여 드리프트 감지 기능을 제공합니다.
"""

from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
import httpx

from apps.seedtest_api.auth.unified import (
    UserContext,
    get_current_user,
    require_admin,
    require_teacher_or_admin,
)

router = APIRouter(prefix="/api/irt/drift", tags=["irt-drift"])

# R Plumber 서비스 URL
R_IRT_BASE_URL = os.getenv("R_IRT_BASE_URL", "http://r-irt-plumber:80")
R_IRT_TIMEOUT = float(os.getenv("R_IRT_TIMEOUT", "3600.0"))  # 1시간


# ============================================================================
# Pydantic Models
# ============================================================================

class DriftRunRequest(BaseModel):
    """드리프트 감지 실행 요청"""
    use_3pl: bool = Field(True, description="3PL 모델 사용 여부")
    multidim: bool = Field(True, description="다차원 모델 사용 여부")
    K: int = Field(2, ge=1, le=5, description="차원 수 (MIRT)")
    iter: int = Field(1000, ge=500, le=5000, description="MCMC 반복 횟수")
    chains: int = Field(2, ge=1, le=4, description="MCMC 체인 수")


class DriftRunResponse(BaseModel):
    """드리프트 감지 실행 결과"""
    success: bool
    window: Optional[str] = None
    n_resp: Optional[int] = None
    n_items: Optional[int] = None
    flags: Optional[int] = None
    error: Optional[str] = None


class DriftItem(BaseModel):
    """드리프트 문항 정보"""
    item_id: str
    model: str
    delta_a: Optional[float] = None
    delta_b: Optional[float] = None
    delta_c: Optional[float] = None
    flag_a: bool = False
    flag_b: bool = False
    flag_c: bool = False
    p_abs_a: Optional[float] = None
    p_abs_b: Optional[float] = None
    p_abs_c: Optional[float] = None
    created_at: str


class ItemParameter(BaseModel):
    """문항 파라미터"""
    item_id: str
    model: str
    a: float
    b: float
    c: Optional[float] = None
    se_a: Optional[float] = None
    se_b: Optional[float] = None
    se_c: Optional[float] = None
    k: int = 1
    updated_at: str


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/run", response_model=DriftRunResponse, dependencies=[Depends(require_admin)])
async def trigger_drift_detection(
    request: DriftRunRequest,
    user: UserContext = Depends(get_current_user)
):
    """드리프트 감지 파이프라인 실행 (관리자 전용)
    
    - 최근 8주 응답 데이터로 IRT 재보정
    - 베이지안 업데이트로 파라미터 드리프트 감지
    - 임계치 초과 문항 자동 플래그
    
    **주의**: 실행 시간이 길 수 있습니다 (10-60분)
    """
    try:
        async with httpx.AsyncClient(timeout=R_IRT_TIMEOUT) as client:
            resp = await client.post(
                f"{R_IRT_BASE_URL}/drift/run",
                json=request.dict()
            )
            resp.raise_for_status()
            result = resp.json()
            
            # 슬랙 알림 (플래그 많을 경우)
            if result.get("data", {}).get("flags", 0) > 10:
                # TODO: 슬랙 알림 통합
                pass
            
            return DriftRunResponse(
                success=result.get("success", False),
                window=result.get("data", {}).get("window"),
                n_resp=result.get("data", {}).get("n_resp"),
                n_items=result.get("data", {}).get("n_items"),
                flags=result.get("data", {}).get("flags"),
                error=result.get("error")
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Drift detection timed out. Check R service logs."
        )
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R service error: {str(e)}"
        )


@router.get("/items", response_model=List[DriftItem])
async def get_drift_items(
    user: UserContext = Depends(get_current_user),
    since_days: int = 30,
    only_flagged: bool = True,
    limit: int = 500
):
    """드리프트 문항 조회
    
    - 최근 N일간 감지된 드리프트 문항 목록
    - 플래그 여부로 필터링 가능
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{R_IRT_BASE_URL}/drift/items",
                params={
                    "since_days": since_days,
                    "only_flagged": only_flagged,
                    "limit": limit
                }
            )
            resp.raise_for_status()
            result = resp.json()
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Unknown error")
                )
            
            return result.get("data", [])
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R service error: {str(e)}"
        )


@router.post("/params/latest", response_model=List[ItemParameter])
async def get_latest_params(
    item_ids: Optional[List[str]] = None,
    limit: int = 200,
    user: UserContext = Depends(get_current_user)
):
    """최신 문항 파라미터 조회
    
    - 특정 문항 ID 목록 또는 최근 N개 조회
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{R_IRT_BASE_URL}/params/latest",
                json={"item_ids": item_ids, "limit": limit}
            )
            resp.raise_for_status()
            result = resp.json()
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Unknown error")
                )
            
            return result.get("data", [])
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R service error: {str(e)}"
        )


@router.get("/stats")
async def get_drift_stats(
    since_days: int = 30,
    user: UserContext = Depends(require_teacher_or_admin)
):
    """드리프트 통계 요약
    
    - 전체 문항 수, 플래그 수, 평균 변화량 등
    """
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(
                f"{R_IRT_BASE_URL}/drift/stats",
                params={"since_days": since_days}
            )
            resp.raise_for_status()
            result = resp.json()
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result.get("error", "Unknown error")
                )
            
            return result.get("data", {})
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R service error: {str(e)}"
        )


@router.get("/config", dependencies=[Depends(require_admin)])
async def get_drift_config(user: UserContext = Depends(get_current_user)):
    """드리프트 감지 설정 조회 (관리자 전용)"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{R_IRT_BASE_URL}/config")
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"R service error: {str(e)}"
        )
```

### FastAPI 앱에 라우터 등록

`/apps/seedtest_api/main.py`에 추가:

```python
from apps.seedtest_api.routers import irt_drift

app.include_router(irt_drift.router)
```

---

## 6. 교사 대시보드 연동

파일 위치: `/portal_front/dashboard/app_teacher.R`

### 6.1 문항 품질 모니터링 탭 추가

```r
# ============================================================================
# UI 섹션
# ============================================================================

tabPanel(
  "문항 품질",
  
  # 상단 요약 박스
  fluidRow(
    valueBoxOutput("drift_count_box", width = 3),
    valueBoxOutput("recent_calibration_box", width = 3),
    valueBoxOutput("avg_delta_b_box", width = 3),
    valueBoxOutput("last_run_box", width = 3)
  ),
  
  # 필터 및 새로고침
  fluidRow(
    box(
      title = "필터 설정",
      width = 12,
      collapsible = TRUE,
      fluidRow(
        column(3, 
          selectInput("drift_period", "조회 기간",
            choices = c("최근 7일" = 7, "최근 30일" = 30, "최근 90일" = 90),
            selected = 30
          )
        ),
        column(3,
          selectInput("drift_flag_filter", "플래그 유형",
            choices = c("전체" = "all", "난이도(b)" = "b", "변별도(a)" = "a", "추측도(c)" = "c"),
            selected = "all"
          )
        ),
        column(3,
          checkboxInput("drift_only_flagged", "플래그만 표시", value = TRUE)
        ),
        column(3,
          actionButton("refresh_drift", "새로고침", icon = icon("refresh"),
            class = "btn-primary", width = "100%")
        )
      )
    )
  ),
  
  # 드리프트 문항 테이블
  fluidRow(
    box(
      title = "드리프트 감지 문항",
      width = 12,
      DTOutput("drift_items_table"),
      downloadButton("download_drift", "CSV 다운로드")
    )
  ),
  
  # 드리프트 트렌드 차트
  fluidRow(
    box(
      title = "드리프트 트렌드 (최근 90일)",
      width = 12,
      plotlyOutput("drift_trend_plot", height = "400px")
    )
  )
)

# ============================================================================
# Server 섹션
# ============================================================================

# 드리프트 통계 조회 (반응형)
drift_stats <- reactive({
  req(input$refresh_drift)
  
  tryCatch({
    resp <- httr::GET(
      paste0(Sys.getenv("R_IRT_BASE_URL", "http://localhost:8000"), "/drift/stats"),
      query = list(since_days = as.integer(input$drift_period))
    )
    
    if (httr::status_code(resp) != 200) {
      showNotification("드리프트 통계 조회 실패", type = "error")
      return(NULL)
    }
    
    result <- httr::content(resp, as = "parsed")
    if (!result$success) {
      showNotification(paste("오류:", result$error), type = "error")
      return(NULL)
    }
    
    result$data
  }, error = function(e) {
    showNotification(paste("API 오류:", e$message), type = "error")
    NULL
  })
})

# 드리프트 문항 조회 (반응형)
drift_items <- reactive({
  req(input$refresh_drift)
  
  tryCatch({
    resp <- httr::GET(
      paste0(Sys.getenv("R_IRT_BASE_URL", "http://localhost:8000"), "/drift/items"),
      query = list(
        since_days = as.integer(input$drift_period),
        only_flagged = input$drift_only_flagged,
        limit = 500
      )
    )
    
    if (httr::status_code(resp) != 200) {
      showNotification("드리프트 문항 조회 실패", type = "error")
      return(NULL)
    }
    
    result <- httr::content(resp, as = "parsed")
    if (!result$success) {
      showNotification(paste("오류:", result$error), type = "error")
      return(NULL)
    }
    
    data <- result$data
    
    # 플래그 필터 적용
    if (input$drift_flag_filter != "all") {
      flag_col <- paste0("flag_", input$drift_flag_filter)
      data <- data %>% filter(!!sym(flag_col) == TRUE)
    }
    
    data
  }, error = function(e) {
    showNotification(paste("API 오류:", e$message), type = "error")
    NULL
  })
})

# ValueBox: 플래그 문항 수
output$drift_count_box <- renderValueBox({
  stats <- drift_stats()
  
  if (is.null(stats)) {
    valueBox(
      value = "N/A",
      subtitle = "플래그 문항 수",
      icon = icon("flag"),
      color = "gray"
    )
  } else {
    total_flags <- sum(stats$flagged_a, stats$flagged_b, stats$flagged_c, na.rm = TRUE)
    color <- if (total_flags > 20) "red" else if (total_flags > 10) "yellow" else "green"
    
    valueBox(
      value = total_flags,
      subtitle = "플래그 문항 수",
      icon = icon("flag"),
      color = color
    )
  }
})

# ValueBox: 최근 재보정 시간
output$recent_calibration_box <- renderValueBox({
  stats <- drift_stats()
  
  if (is.null(stats) || is.null(stats$last_run)) {
    valueBox(
      value = "미실행",
      subtitle = "최근 재보정",
      icon = icon("clock"),
      color = "gray"
    )
  } else {
    last_run <- as.POSIXct(stats$last_run)
    days_ago <- as.numeric(difftime(Sys.time(), last_run, units = "days"))
    
    color <- if (days_ago > 14) "red" else if (days_ago > 7) "yellow" else "green"
    
    valueBox(
      value = format(last_run, "%m/%d"),
      subtitle = paste0("최근 재보정 (", round(days_ago), "일 전)"),
      icon = icon("clock"),
      color = color
    )
  }
})

# ValueBox: 평균 난이도 변화
output$avg_delta_b_box <- renderValueBox({
  stats <- drift_stats()
  
  if (is.null(stats)) {
    valueBox(
      value = "N/A",
      subtitle = "평균 Δb",
      icon = icon("chart-line"),
      color = "gray"
    )
  } else {
    avg_delta <- round(stats$avg_abs_delta_b, 3)
    color <- if (avg_delta > 0.3) "red" else if (avg_delta > 0.15) "yellow" else "green"
    
    valueBox(
      value = avg_delta,
      subtitle = "평균 난이도 변화 (|Δb|)",
      icon = icon("chart-line"),
      color = color
    )
  }
})

# ValueBox: 분석 문항 수
output$last_run_box <- renderValueBox({
  stats <- drift_stats()
  
  if (is.null(stats)) {
    valueBox(
      value = "N/A",
      subtitle = "분석 문항 수",
      icon = icon("list"),
      color = "gray"
    )
  } else {
    valueBox(
      value = stats$total_items,
      subtitle = "분석 문항 수",
      icon = icon("list"),
      color = "blue"
    )
  }
})

# 드리프트 문항 테이블
output$drift_items_table <- renderDT({
  data <- drift_items()
  
  if (is.null(data) || nrow(data) == 0) {
    return(datatable(data.frame(메시지 = "데이터 없음")))
  }
  
  # 테이블 표시용 데이터 가공
  display_data <- data %>%
    select(
      문항ID = item_id,
      모델 = model,
      `Δb` = delta_b,
      `Δa` = delta_a,
      `Δc` = delta_c,
      `P(|Δb|>τ)` = p_abs_b,
      `난이도 플래그` = flag_b,
      `변별도 플래그` = flag_a,
      `추측도 플래그` = flag_c,
      생성일 = created_at
    ) %>%
    mutate(
      `Δb` = round(`Δb`, 3),
      `Δa` = round(`Δa`, 3),
      `Δc` = round(`Δc`, 3),
      `P(|Δb|>τ)` = round(`P(|Δb|>τ)`, 3),
      생성일 = substr(생성일, 1, 10)
    )
  
  datatable(
    display_data,
    options = list(
      pageLength = 25,
      order = list(list(6, 'desc')),  # P(|Δb|>τ) 내림차순
      dom = 'Bfrtip',
      buttons = c('copy', 'csv', 'excel')
    ),
    rownames = FALSE
  ) %>%
    formatStyle(
      '난이도 플래그',
      backgroundColor = styleEqual(c(TRUE, FALSE), c("#ffcccc", "white"))
    ) %>%
    formatStyle(
      '변별도 플래그',
      backgroundColor = styleEqual(c(TRUE, FALSE), c("#fff3cd", "white"))
    ) %>%
    formatStyle(
      '추측도 플래그',
      backgroundColor = styleEqual(c(TRUE, FALSE), c("#d1ecf1", "white"))
    ) %>%
    formatStyle(
      'Δb',
      color = styleInterval(c(-0.2, 0.2), c("red", "black", "red"))
    )
})

# CSV 다운로드
output$download_drift <- downloadHandler(
  filename = function() {
    paste0("drift_items_", Sys.Date(), ".csv")
  },
  content = function(file) {
    data <- drift_items()
    if (!is.null(data)) {
      write.csv(data, file, row.names = FALSE)
    }
  }
)

# 드리프트 트렌드 차트
output$drift_trend_plot <- renderPlotly({
  # TODO: 시계열 데이터 조회 API 추가 필요
  # 현재는 임시 플레이스홀더
  
  plot_ly() %>%
    add_trace(
      type = "scatter",
      mode = "lines+markers",
      x = seq(Sys.Date() - 90, Sys.Date(), by = "week"),
      y = rnorm(14, mean = 5, sd = 2),
      name = "플래그 문항 수",
      line = list(color = "rgb(255, 127, 14)")
    ) %>%
    layout(
      title = "주간 플래그 문항 수 추이",
      xaxis = list(title = "날짜"),
      yaxis = list(title = "플래그 문항 수"),
      hovermode = "x unified"
    )
})
```

### 6.2 환경 변수 설정

```bash
# .env 또는 .Renviron
R_IRT_BASE_URL=http://r-irt-plumber:80
```

---

## 7. Celery 배치 작업

파일 위치: `/shared/tasks/irt_drift.py`

```python
"""IRT 드리프트 감지 배치 작업

주기적으로 드리프트 감지를 실행하고 결과를 알림합니다.
"""

from __future__ import annotations

import os
import logging
from typing import Dict, Any

from celery import shared_task
import httpx

logger = logging.getLogger(__name__)

# R Plumber 서비스 URL
R_IRT_BASE_URL = os.getenv("R_IRT_BASE_URL", "http://r-irt-plumber:80")


@shared_task(
    name="irt.weekly_drift_detection",
    bind=True,
    max_retries=3,
    default_retry_delay=300  # 5분 후 재시도
)
def weekly_drift_detection(self) -> Dict[str, Any]:
    """주간 드리프트 감지 (매주 일요일 03:00)
    
    - 최근 8주 응답 데이터로 IRT 재보정
    - 베이지안 드리프트 감지
    - 플래그 문항 슬랙 알림
    
    Returns:
        드리프트 감지 결과 딕셔너리
    """
    try:
        logger.info("Starting weekly IRT drift detection...")
        
        with httpx.Client(timeout=3600.0) as client:
            resp = client.post(
                f"{R_IRT_BASE_URL}/drift/run",
                json={
                    "use_3pl": True,
                    "multidim": True,
                    "K": 2,
                    "iter": 1000,
                    "chains": 2
                }
            )
            resp.raise_for_status()
            result = resp.json()
        
        if not result.get("success"):
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Drift detection failed: {error_msg}")
            raise Exception(error_msg)
        
        data = result.get("data", {})
        flags = data.get("flags", 0)
        n_items = data.get("n_items", 0)
        window = data.get("window", "unknown")
        
        logger.info(
            f"Drift detection completed: {flags}/{n_items} items flagged "
            f"(window: {window})"
        )
        
        # 슬랙 알림 (플래그 많을 경우)
        if flags > 10:
            send_slack_alert(
                channel="#irt-alerts",
                message=f"⚠️ **IRT 드리프트 감지 경고**\n"
                        f"• 플래그된 문항: {flags}개 / {n_items}개\n"
                        f"• 분석 기간: {window}\n"
                        f"• 조치 필요: 문항 재검토 또는 노출 제한"
            )
        elif flags > 0:
            send_slack_alert(
                channel="#irt-monitoring",
                message=f"ℹ️ IRT 드리프트 감지 완료: {flags}개 문항 플래그됨 (기간: {window})"
            )
        
        return {
            "success": True,
            "flags": flags,
            "n_items": n_items,
            "window": window
        }
        
    except httpx.TimeoutException as e:
        logger.error(f"Drift detection timeout: {str(e)}")
        # 재시도
        raise self.retry(exc=e)
        
    except httpx.HTTPError as e:
        logger.error(f"R service HTTP error: {str(e)}")
        # 재시도
        raise self.retry(exc=e)
        
    except Exception as e:
        logger.error(f"Unexpected error in drift detection: {str(e)}")
        send_slack_alert(
            channel="#irt-alerts",
            message=f"🚨 **IRT 드리프트 감지 실패**\n"
                    f"• 오류: {str(e)}\n"
                    f"• 작업 ID: {self.request.id}"
        )
        raise


@shared_task(name="irt.daily_drift_stats")
def daily_drift_stats() -> Dict[str, Any]:
    """일일 드리프트 통계 수집 (매일 06:00)
    
    - 최근 30일 드리프트 통계 조회
    - 대시보드용 메트릭 업데이트
    """
    try:
        logger.info("Collecting daily drift statistics...")
        
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                f"{R_IRT_BASE_URL}/drift/stats",
                params={"since_days": 30}
            )
            resp.raise_for_status()
            result = resp.json()
        
        if not result.get("success"):
            raise Exception(result.get("error", "Unknown error"))
        
        stats = result.get("data", {})
        logger.info(f"Drift stats collected: {stats}")
        
        # TODO: 메트릭 저장 (Prometheus, DB 등)
        
        return {"success": True, "stats": stats}
        
    except Exception as e:
        logger.error(f"Failed to collect drift stats: {str(e)}")
        raise


def send_slack_alert(channel: str, message: str):
    """슬랙 알림 전송
    
    Args:
        channel: 슬랙 채널 (#irt-alerts 등)
        message: 메시지 내용
    """
    slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
    if not slack_webhook:
        logger.warning("SLACK_WEBHOOK_URL not configured, skipping alert")
        return
    
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(
                slack_webhook,
                json={
                    "channel": channel,
                    "text": message,
                    "username": "IRT Drift Monitor",
                    "icon_emoji": ":chart_with_upwards_trend:"
                }
            )
            resp.raise_for_status()
            logger.info(f"Slack alert sent to {channel}")
    except Exception as e:
        logger.error(f"Failed to send Slack alert: {str(e)}")
```

### Celery Beat 스케줄

파일 위치: `/shared/celery_config.py`

```python
from celery.schedules import crontab

beat_schedule = {
    # 주간 드리프트 감지 (일요일 03:00)
    "weekly-irt-drift": {
        "task": "irt.weekly_drift_detection",
        "schedule": crontab(day_of_week=0, hour=3, minute=0),
        "options": {
            "expires": 7200,  # 2시간 내 실행
        }
    },
    
    # 일일 통계 수집 (매일 06:00)
    "daily-irt-drift-stats": {
        "task": "irt.daily_drift_stats",
        "schedule": crontab(hour=6, minute=0),
        "options": {
            "expires": 3600,  # 1시간 내 실행
        }
    },
}
```

### 환경 변수

```bash
# .env 또는 Kubernetes ConfigMap
R_IRT_BASE_URL=http://r-irt-plumber.seedtest.svc.cluster.local:80
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

---

## 8. 운영 가이드

### 8.1 초기 설정

```bash
# 1. 환경 변수
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=***
export PGDATABASE=dreamseed
export R_IRT_BASE_URL=http://r-irt-plumber:80

# 2. DB 스키마 적용
psql -f docs/IRT_DRIFT_CONTROL_GUIDE.md  # SQL 섹션 추출 후 실행

# 3. R 패키지 설치
Rscript -e 'install.packages(c("DBI","RPostgres","dplyr","tidyr","mirt","rstan","plumber"))'

# 4. Plumber 실행
cd /portal_front/r-irt-plumber
Rscript -e 'plumber::plumb("plumber_drift.R")$run(host="0.0.0.0", port=8000)'
```

### 8.2 수동 실행

```bash
# 드리프트 감지 실행
curl -X POST http://localhost:8000/drift/run \
  -H "Content-Type: application/json" \
  -d '{"use_3pl": true, "multidim": true, "K": 2}'

# 플래그 문항 조회
curl "http://localhost:8000/drift/items?since_days=60&only_flagged=true"
```

### 8.3 모니터링

```sql
-- 최근 드리프트 감지 결과
SELECT 
  t_window_d,
  COUNT(*) AS total_items,
  SUM(CASE WHEN flag_b THEN 1 ELSE 0 END) AS flagged_b,
  AVG(ABS(delta_b)) AS avg_abs_delta_b
FROM item_drift_log
WHERE created_at >= NOW() - INTERVAL '30 days'
GROUP BY t_window_d
ORDER BY t_window_d DESC;

-- 플래그 빈도 높은 문항
SELECT 
  item_id,
  COUNT(*) AS flag_count,
  AVG(delta_b) AS avg_delta_b
FROM item_drift_log
WHERE flag_b = TRUE
  AND created_at >= NOW() - INTERVAL '90 days'
GROUP BY item_id
HAVING COUNT(*) >= 3
ORDER BY flag_count DESC;
```

---

## 9. 파라미터 튜닝

### 9.1 임계값 조정

| 파라미터 | 초기값 | 조정 기준 |
|---------|--------|----------|
| `tau_b` | 0.20 | 플래그 과다 시 0.25로 상향 |
| `tau_a` | 0.15 | 변별도 민감도 조정 |
| `tau_c` | 0.05 | 추측도 변화 허용 범위 |
| `prob_thresh` | 0.95 | 신뢰수준 (0.90~0.99) |
| `window_days` | 56 | 응답 수에 따라 42~70일 |

### 9.2 워밍업 필터

```sql
-- 신규 문항 제외 (14일)
CREATE OR REPLACE VIEW view_item_responses_recent AS
SELECT 
  user_id,
  item_id,
  CASE WHEN score >= 0.5 THEN 1 ELSE 0 END AS correct,
  created_at AS ts
FROM responses r
JOIN items i ON r.item_id = i.id
WHERE r.created_at >= NOW() - INTERVAL '56 days'
  AND r.status = 'completed'
  AND i.created_at <= NOW() - INTERVAL '14 days';  -- 워밍업 필터
```

---

## 10. 문제 해결

### 10.1 Stan 수렴 실패

**증상**: `Rhat > 1.1` 경고

**해결**:
```r
# iter 증가
run_drift(iter = 2000, chains = 4)

# 사전분포 완화
# stan_3pl_unidim 모델에서:
# a_raw ~ normal(log(a0), se_a0 + 0.5);  # 0.5로 증가
```

### 10.2 메모리 부족

**증상**: R 프로세스 OOM

**해결**:
```r
# 샘플링 줄이기
DRIFT_CONF$window_days <- 42  # 8주 → 6주

# 또는 배치 처리
items_batch <- split(items, ceiling(seq_along(items)/50))
for (batch in items_batch) {
  run_drift_batch(batch)
}
```

### 10.3 API 타임아웃

**증상**: FastAPI → R Plumber 타임아웃

**해결**:
```python
# httpx 타임아웃 증가
async with httpx.AsyncClient(timeout=3600.0) as client:
    ...
```

---

## 11. 다음 단계

1. **UI 개선**: 교사 대시보드에 드리프트 시각화 추가
2. **자동 노출 제어**: 플래그 문항의 노출 확률 자동 감소
3. **재채점 큐**: 플래그 문항 자동 재검토 워크플로
4. **다차원 확장**: K=3, K=4 차원 지원
5. **실시간 감지**: 스트리밍 데이터로 실시간 드리프트 감지

---

## 참고 자료

- mirt 패키지: https://cran.r-project.org/web/packages/mirt/
- rstan 가이드: https://mc-stan.org/users/interfaces/rstan
- IRT 드리프트 논문: Glas & Jehangir (2014)
