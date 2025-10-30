from __future__ import annotations

import json
import os
import time
from typing import Any, Dict, Optional

import boto3
from botocore.config import Config as BotoConfig
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter(prefix="/api/pdf", tags=["pdf-jobs"])

# Env vars to integrate with deployed Lambda/DynamoDB/S3
AWS_REGION = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1"
LAMBDA_NAME = os.getenv("LAMBDA_NAME", "")
DDB_TABLE = os.getenv("DDB_TABLE", "")
S3_BUCKET = os.getenv("S3_BUCKET", "")
RETURN_PRESIGNED_URL = os.getenv("RETURN_PRESIGNED_URL", "true").lower() == "true"

boto_cfg = BotoConfig(retries={"max_attempts": 3, "mode": "standard"}, read_timeout=10, connect_timeout=3)
_lambda = boto3.client("lambda", region_name=AWS_REGION, config=boto_cfg)
ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
ddb_table = ddb.Table(DDB_TABLE) if DDB_TABLE else None  # type: ignore
s3 = boto3.client("s3", region_name=AWS_REGION, config=boto_cfg)


class CreateJobBody(BaseModel):
    title: str = "Report"
    chart_data: Dict[str, Any] = {}
    job_id: Optional[str] = None


@router.post("/jobs")
def create_job(body: CreateJobBody):
    if not LAMBDA_NAME:
        raise HTTPException(status_code=500, detail="lambda_not_configured")

    job_id = body.job_id or str(uuid4())

    # Optimistic: initialize state in DDB if available
    if ddb_table is not None:
        try:
            ddb_table.put_item(Item={"job_id": job_id, "status": "pending", "created_at": int(time.time())})
        except Exception:
            # Non-fatal: continue without DDB init
            pass

    payload = {"job_id": job_id, "title": body.title, "chart_data": body.chart_data}

    # Async invoke (Event) — returns immediately
    try:
        _lambda.invoke(FunctionName=LAMBDA_NAME, InvocationType="Event", Payload=json.dumps(payload).encode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"lambda_invoke_failed: {e}")

    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_job(job_id: str):
    if ddb_table is None:
        raise HTTPException(status_code=500, detail="ddb_not_configured")

    try:
        item = ddb_table.get_item(Key={"job_id": job_id}).get("Item")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"ddb_error: {e}")

    if not item:
        raise HTTPException(status_code=404, detail="job_not_found")

    status = item.get("status")
    resp: Dict[str, Any] = {"job_id": job_id, "status": status}

    if status == "done":
        s3_key = item.get("s3_key")
        if not s3_key:
            return resp
        if S3_BUCKET and RETURN_PRESIGNED_URL:
            try:
                url = s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": S3_BUCKET, "Key": s3_key},
                    ExpiresIn=3600,
                )
                resp["download_url"] = url
            except Exception:
                # Non-fatal: omit URL
                pass
    if status == "failed":
        resp["error"] = item.get("error")

    return resp
