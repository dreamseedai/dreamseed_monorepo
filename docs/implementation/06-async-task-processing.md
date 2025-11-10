# Async Task Processing with Celery

## Table of Contents

- [Overview](#overview)
- [Celery vs Alternatives](#celery-vs-alternatives)
- [Architecture](#architecture)
- [Quarto Report Generation](#quarto-report-generation)
- [IRT Calibration](#irt-calibration)
- [Task Prioritization](#task-prioritization)
- [Monitoring & Debugging](#monitoring--debugging)
- [Implementation](#implementation)
- [Testing Strategy](#testing-strategy)

## Overview

Async task processing handles long-running operations outside the request-response cycle:

- **Report generation**: Quarto rendering (5-30 minutes) with R/Python statistical analysis
- **IRT calibration**: ML model training (hours to days) for item difficulty estimation
- **Email notifications**: Bulk email delivery
- **Data exports**: Large dataset CSV/Excel generation
- **Batch processing**: Nightly analytics aggregation

**Technology Stack**: Celery 5.3+ with Redis as broker/backend

## Celery vs Alternatives

### Decision Matrix

| Factor          | Celery           | RQ           | Dramatiq    | Cloud Tasks      |
| --------------- | ---------------- | ------------ | ----------- | ---------------- |
| Maturity        | Excellent (2009) | Good         | Good        | Excellent        |
| Priority queues | ✅ Yes           | ❌ No        | ✅ Yes      | ✅ Yes           |
| Scheduled tasks | ✅ Beat          | ❌ Scheduler | ✅ Yes      | ✅ Yes           |
| Result backend  | ✅ Redis/DB      | ✅ Redis     | ✅ Redis/DB | ✅ Built-in      |
| Retries         | ✅ Advanced      | ✅ Basic     | ✅ Advanced | ✅ Advanced      |
| Monitoring      | ✅ Flower        | ✅ Dashboard | ❌ Limited  | ✅ Cloud Console |
| Learning curve  | Steep            | Gentle       | Moderate    | Moderate         |
| Kubernetes      | Good             | Excellent    | Good        | N/A (managed)    |
| Cost            | Free             | Free         | Free        | Pay per task     |

**Decision**: Celery for feature completeness and ecosystem maturity

## Architecture

### Celery Configuration

```python
# app/core/celery_app.py
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "dreamseed",
    broker=settings.CELERY_BROKER_URL,  # redis://redis:6379/0
    backend=settings.CELERY_RESULT_BACKEND  # redis://redis:6379/1
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task routing
    task_routes={
        "app.tasks.reports.*": {"queue": "reports"},
        "app.tasks.irt.*": {"queue": "irt"},
        "app.tasks.email.*": {"queue": "emails"},
        "app.tasks.exports.*": {"queue": "exports"}
    },

    # Task priorities (0-9, higher = more urgent)
    task_default_priority=5,

    # Result expiration
    result_expires=86400,  # 24 hours

    # Worker configuration
    worker_prefetch_multiplier=1,  # Disable prefetching for long tasks
    worker_max_tasks_per_child=100,  # Restart worker after 100 tasks

    # Retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Beat schedule (periodic tasks)
    beat_schedule={
        "nightly-analytics": {
            "task": "app.tasks.analytics.aggregate_daily_stats",
            "schedule": crontab(hour=2, minute=0),  # 2 AM UTC
        },
        "weekly-irt-calibration": {
            "task": "app.tasks.irt.calibrate_item_bank",
            "schedule": crontab(day_of_week=0, hour=3, minute=0),  # Sunday 3 AM
        },
        "cleanup-old-sessions": {
            "task": "app.tasks.cleanup.remove_expired_sessions",
            "schedule": crontab(hour=1, minute=0),  # 1 AM daily
        }
    }
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["app.tasks"])
```

### Task Base Class

```python
# app/tasks/base.py
from celery import Task
from celery.utils.log import get_task_logger
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

logger = get_task_logger(__name__)

class DatabaseTask(Task):
    """Base task with database session."""

    _db_session = None

    @property
    def db_session(self) -> AsyncSession:
        if self._db_session is None:
            engine = create_async_engine(settings.DATABASE_URL)
            self._db_session = AsyncSession(engine)
        return self._db_session

    def after_return(self, *args, **kwargs):
        """Clean up after task completion."""
        if self._db_session is not None:
            self._db_session.close()
            self._db_session = None

class RetryableTask(DatabaseTask):
    """Task with automatic retry on failure."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True  # Exponential backoff
    retry_backoff_max = 600  # Max 10 minutes
    retry_jitter = True  # Add randomness to backoff
```

## Quarto Report Generation

### Report Task

```python
# app/tasks/reports.py
import subprocess
import tempfile
import os
from pathlib import Path
from uuid import UUID
from celery import shared_task
from celery.utils.log import get_task_logger
from app.tasks.base import RetryableTask
from app.core.storage import upload_to_storage

logger = get_task_logger(__name__)

@shared_task(base=RetryableTask, bind=True, time_limit=1800)  # 30 min timeout
async def generate_student_report(
    self,
    student_id: str,
    assessment_id: str,
    report_type: str = "comprehensive"
):
    """Generate Quarto PDF report for student assessment."""
    logger.info(f"Generating {report_type} report for student {student_id}")

    try:
        # Update task state
        self.update_state(state="PROGRESS", meta={"step": "fetching_data", "progress": 10})

        # 1. Fetch data from database
        data = await fetch_assessment_data(
            self.db_session,
            UUID(student_id),
            UUID(assessment_id)
        )

        self.update_state(state="PROGRESS", meta={"step": "preparing_template", "progress": 30})

        # 2. Prepare Quarto template
        template_path = Path(f"templates/reports/{report_type}.qmd")

        with tempfile.TemporaryDirectory() as tmpdir:
            # 3. Write data files
            data_file = Path(tmpdir) / "data.json"
            with open(data_file, "w") as f:
                import json
                json.dump(data, f)

            # Copy template
            report_file = Path(tmpdir) / "report.qmd"
            import shutil
            shutil.copy(template_path, report_file)

            self.update_state(state="PROGRESS", meta={"step": "rendering_quarto", "progress": 50})

            # 4. Render with Quarto
            result = subprocess.run(
                [
                    "quarto", "render", str(report_file),
                    "--to", "pdf",
                    "--execute-params", str(data_file)
                ],
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=1500  # 25 min for R/Python execution
            )

            if result.returncode != 0:
                logger.error(f"Quarto render failed: {result.stderr}")
                raise Exception(f"Quarto render failed: {result.stderr}")

            self.update_state(state="PROGRESS", meta={"step": "uploading", "progress": 90})

            # 5. Upload to storage
            pdf_path = Path(tmpdir) / "report.pdf"
            storage_url = await upload_to_storage(
                pdf_path,
                f"reports/{student_id}/{assessment_id}.pdf"
            )

            # 6. Update database
            await save_report_metadata(
                self.db_session,
                UUID(student_id),
                UUID(assessment_id),
                storage_url
            )

            logger.info(f"Report generated successfully: {storage_url}")

            return {
                "status": "success",
                "student_id": student_id,
                "assessment_id": assessment_id,
                "storage_url": storage_url
            }

    except subprocess.TimeoutExpired:
        logger.error("Quarto rendering timed out")
        raise
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}")
        raise

async def fetch_assessment_data(db, student_id: UUID, assessment_id: UUID):
    """Fetch all data needed for report."""
    # Fetch student info, responses, IRT estimates, growth trajectory, etc.
    # This is a simplified example
    return {
        "student": {"id": str(student_id), "name": "John Doe"},
        "assessment": {"id": str(assessment_id), "title": "Math Assessment"},
        "ability_estimate": 0.75,
        "items_answered": 25,
        "accuracy": 0.84
    }

async def save_report_metadata(db, student_id, assessment_id, storage_url):
    """Save report metadata to database."""
    from sqlalchemy import text

    query = text("""
        INSERT INTO reports (student_id, assessment_id, storage_url, generated_at)
        VALUES (:student_id, :assessment_id, :storage_url, CURRENT_TIMESTAMP)
    """)

    await db.execute(query, {
        "student_id": str(student_id),
        "assessment_id": str(assessment_id),
        "storage_url": storage_url
    })
    await db.commit()
```

### Quarto Template Example

````markdown
---
title: "Student Assessment Report"
format:
  pdf:
    toc: true
    number-sections: true
params:
  data_file: "data.json"
---

```{python}
#| echo: false
import json
import pandas as pd
import matplotlib.pyplot as plt

with open(params['data_file']) as f:
    data = json.load(f)

student = data['student']
assessment = data['assessment']
```
````

# Assessment Summary

**Student**: `{python} student['name']`  
**Assessment**: `{python} assessment['title']`  
**Date**: `{python} pd.Timestamp.now().strftime('%Y-%m-%d')`

## Performance Overview

- **Ability Estimate**: `{python} f"{data['ability_estimate']:.2f}"`
- **Items Answered**: `{python} data['items_answered']`
- **Accuracy**: `{python} f"{data['accuracy']*100:.1f}%"`

## Ability Trajectory

```{python}
#| echo: false
#| fig-cap: "Ability estimation over time"

# Plot ability trajectory (placeholder)
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot([0.5, 0.6, 0.7, 0.75], marker='o')
ax.set_xlabel("Item Number")
ax.set_ylabel("Ability Estimate (θ)")
ax.set_title("CAT Ability Estimation Progress")
ax.grid(True, alpha=0.3)
plt.show()
```

## Recommendations

Based on the assessment results, we recommend:

1. Focus on skills where performance was below 70%
2. Review prerequisite concepts for items answered incorrectly
3. Practice with similar difficulty items (θ = `{python} f"{data['ability_estimate']:.2f}"`)

````

## IRT Calibration

### Calibration Task

```python
# app/tasks/irt.py
import numpy as np
from scipy.optimize import minimize
from celery import shared_task
from celery.utils.log import get_task_logger
from app.tasks.base import RetryableTask

logger = get_task_logger(__name__)

@shared_task(base=RetryableTask, bind=True, time_limit=86400)  # 24 hour timeout
async def calibrate_item_bank(self, organization_id: str):
    """Calibrate IRT parameters for entire item bank."""
    logger.info(f"Starting IRT calibration for organization {organization_id}")

    try:
        # 1. Fetch response data
        self.update_state(state="PROGRESS", meta={"step": "fetching_responses", "progress": 5})

        responses = await fetch_response_matrix(self.db_session, organization_id)
        logger.info(f"Fetched {len(responses)} response records")

        # 2. Prepare data matrix
        self.update_state(state="PROGRESS", meta={"step": "preparing_matrix", "progress": 10})

        item_ids, student_ids, response_matrix = prepare_matrix(responses)
        n_students, n_items = response_matrix.shape
        logger.info(f"Matrix shape: {n_students} students × {n_items} items")

        # 3. Joint Maximum Likelihood Estimation (JMLE)
        self.update_state(state="PROGRESS", meta={"step": "estimating_parameters", "progress": 20})

        item_params, ability_params = await jmle_estimation(
            response_matrix,
            callback=lambda progress: self.update_state(
                state="PROGRESS",
                meta={"step": "estimating_parameters", "progress": 20 + int(progress * 60)}
            )
        )

        # 4. Save to database
        self.update_state(state="PROGRESS", meta={"step": "saving_results", "progress": 90})

        await save_item_parameters(self.db_session, item_ids, item_params)
        await save_ability_estimates(self.db_session, student_ids, ability_params)

        logger.info("IRT calibration completed successfully")

        return {
            "status": "success",
            "organization_id": organization_id,
            "n_items": n_items,
            "n_students": n_students,
            "mean_difficulty": float(np.mean(item_params[:, 1])),  # b parameters
            "mean_ability": float(np.mean(ability_params))
        }

    except Exception as e:
        logger.error(f"IRT calibration failed: {str(e)}")
        raise

async def jmle_estimation(response_matrix, callback=None, max_iter=100):
    """Joint Maximum Likelihood Estimation for 2PL model."""
    n_students, n_items = response_matrix.shape

    # Initialize parameters
    a_params = np.ones(n_items)  # Discrimination
    b_params = np.zeros(n_items)  # Difficulty
    theta = np.zeros(n_students)  # Ability

    for iteration in range(max_iter):
        if callback:
            callback(iteration / max_iter)

        # E-step: Estimate abilities given item parameters
        for i in range(n_students):
            responses = response_matrix[i, :]
            theta[i] = estimate_ability_mle(responses, a_params, b_params)

        # M-step: Estimate item parameters given abilities
        for j in range(n_items):
            responses = response_matrix[:, j]
            a_params[j], b_params[j] = estimate_item_params(responses, theta)

        # Check convergence (simplified)
        if iteration > 10:
            break

    item_params = np.column_stack([a_params, b_params, np.zeros(n_items)])  # c=0 for 2PL
    return item_params, theta

def estimate_ability_mle(responses, a_params, b_params):
    """MLE for single student ability."""
    def neg_log_likelihood(theta):
        p = 1 / (1 + np.exp(-a_params * (theta - b_params)))
        p = np.clip(p, 1e-10, 1 - 1e-10)
        ll = np.sum(responses * np.log(p) + (1 - responses) * np.log(1 - p))
        return -ll

    result = minimize(neg_log_likelihood, x0=0.0, bounds=[(-4, 4)])
    return result.x[0]

def estimate_item_params(responses, theta):
    """MLE for single item parameters."""
    def neg_log_likelihood(params):
        a, b = params
        p = 1 / (1 + np.exp(-a * (theta - b)))
        p = np.clip(p, 1e-10, 1 - 1e-10)
        ll = np.sum(responses * np.log(p) + (1 - responses) * np.log(1 - p))
        return -ll

    result = minimize(
        neg_log_likelihood,
        x0=[1.0, 0.0],
        bounds=[(0.1, 3.0), (-4, 4)]
    )
    return result.x
````

## Task Prioritization

### Priority Queue Configuration

```python
# app/api/endpoints/tasks.py
from fastapi import APIRouter, Depends
from celery import group, chain, chord
from app.tasks.reports import generate_student_report
from app.tasks.email import send_report_notification

router = APIRouter()

@router.post("/reports/generate")
async def create_report_task(
    student_id: str,
    assessment_id: str,
    priority: int = 5,
    notify_email: bool = True
):
    """Submit report generation task with priority."""

    # High priority for individual student reports (teachers waiting)
    # Low priority for bulk batch reports (nightly processing)

    if notify_email:
        # Chain: generate report → send email
        workflow = chain(
            generate_student_report.si(student_id, assessment_id).set(priority=priority),
            send_report_notification.s(student_id)  # Receives previous result
        )
        result = workflow.apply_async()
    else:
        result = generate_student_report.apply_async(
            args=[student_id, assessment_id],
            priority=priority
        )

    return {
        "task_id": result.id,
        "status": "submitted",
        "priority": priority
    }

@router.post("/reports/batch")
async def create_batch_reports(student_ids: list[str], assessment_id: str):
    """Generate reports for multiple students in parallel."""

    # Group: run tasks in parallel
    job = group(
        generate_student_report.si(student_id, assessment_id).set(priority=3)
        for student_id in student_ids
    )
    result = job.apply_async()

    return {
        "group_id": result.id,
        "status": "submitted",
        "count": len(student_ids)
    }

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get task status and result."""
    from celery.result import AsyncResult

    result = AsyncResult(task_id)

    response = {
        "task_id": task_id,
        "status": result.state,
        "result": result.result if result.successful() else None
    }

    # Include progress for running tasks
    if result.state == "PROGRESS":
        response["meta"] = result.info

    return response
```

## Monitoring & Debugging

### Flower Dashboard

```dockerfile
# docker-compose.yml
services:
  flower:
    image: mher/flower:2.0
    command: celery --broker=redis://redis:6379/0 flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/1
    depends_on:
      - redis
```

### Custom Monitoring

```python
# app/tasks/monitoring.py
from celery import shared_task
from celery.utils.log import get_task_logger
from prometheus_client import Counter, Histogram, Gauge

logger = get_task_logger(__name__)

# Metrics
task_started = Counter("celery_task_started_total", "Tasks started", ["task_name"])
task_succeeded = Counter("celery_task_succeeded_total", "Tasks succeeded", ["task_name"])
task_failed = Counter("celery_task_failed_total", "Tasks failed", ["task_name"])
task_duration = Histogram("celery_task_duration_seconds", "Task duration", ["task_name"])
queue_length = Gauge("celery_queue_length", "Queue length", ["queue_name"])

@shared_task(bind=True)
def monitored_task(self):
    """Example task with monitoring."""
    task_name = self.name

    task_started.labels(task_name=task_name).inc()

    import time
    start_time = time.time()

    try:
        # Do work
        time.sleep(2)

        task_succeeded.labels(task_name=task_name).inc()
    except Exception as e:
        task_failed.labels(task_name=task_name).inc()
        raise
    finally:
        duration = time.time() - start_time
        task_duration.labels(task_name=task_name).observe(duration)
```

## Testing Strategy

```python
# tests/test_tasks.py
import pytest
from unittest.mock import patch, MagicMock
from app.tasks.reports import generate_student_report

@pytest.mark.asyncio
async def test_report_generation(db_session):
    """Test report generation task."""

    # Mock Quarto subprocess
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)

        # Mock storage upload
        with patch("app.core.storage.upload_to_storage") as mock_upload:
            mock_upload.return_value = "https://storage.example.com/report.pdf"

            result = await generate_student_report(
                student_id="123",
                assessment_id="456"
            )

            assert result["status"] == "success"
            assert "storage_url" in result
            mock_run.assert_called_once()

def test_celery_task_routing():
    """Test that tasks are routed to correct queues."""
    from app.core.celery_app import celery_app

    routes = celery_app.conf.task_routes

    assert routes["app.tasks.reports.*"]["queue"] == "reports"
    assert routes["app.tasks.irt.*"]["queue"] == "irt"

@pytest.mark.asyncio
async def test_task_retry_on_failure():
    """Test automatic retry on transient failures."""

    with patch("subprocess.run") as mock_run:
        # First call fails, second succeeds
        mock_run.side_effect = [
            MagicMock(returncode=1, stderr="Timeout"),
            MagicMock(returncode=0)
        ]

        # Task should retry and eventually succeed
        result = await generate_student_report.apply_async(
            args=["123", "456"]
        ).get()

        assert result["status"] == "success"
        assert mock_run.call_count == 2
```

## Summary

Async task processing provides:

1. **Long-running operations**: Quarto reports (30 min), IRT calibration (hours)
2. **Task queues**: Separate queues for reports, IRT, emails, exports
3. **Priority system**: Urgent tasks (0-9 priority levels)
4. **Monitoring**: Flower dashboard, Prometheus metrics
5. **Reliability**: Automatic retries, dead letter queues, idempotency

**Key Metrics**:

- Report generation: 5-30 minutes
- IRT calibration: 2-24 hours (depending on data size)
- Task throughput: 100+ tasks/second
- Retry backoff: Exponential with jitter

**Next Steps**:

- Implement task result webhooks for real-time notifications
- Add dead letter queue handling
- Optimize Quarto rendering with caching
- Implement distributed task coordination for multi-organization calibration
