"""
Health check endpoints for monitoring application health
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User
import time
import psutil
import os
from typing import Dict, Any

router = APIRouter()

@router.get("/__ok")
async def health_check_ok():
    """Simple health check endpoint for load balancers"""
    return {"status": "ok", "timestamp": time.time()}

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "checks": {}
    }

    overall_status = "healthy"

    # Database health check
    try:
        db.execute("SELECT 1")
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}"
        }
        overall_status = "unhealthy"

    # Memory health check
    try:
        memory = psutil.virtual_memory()
        memory_usage_percent = memory.percent

        if memory_usage_percent > 90:
            memory_status = "unhealthy"
            overall_status = "unhealthy"
        elif memory_usage_percent > 80:
            memory_status = "degraded"
            if overall_status == "healthy":
                overall_status = "degraded"
        else:
            memory_status = "healthy"

        health_status["checks"]["memory"] = {
            "status": memory_status,
            "usage_percent": memory_usage_percent,
            "available_mb": round(memory.available / 1024 / 1024, 2),
            "total_mb": round(memory.total / 1024 / 1024, 2)
        }
    except Exception as e:
        health_status["checks"]["memory"] = {
            "status": "unhealthy",
            "message": f"Memory check failed: {str(e)}"
        }
        overall_status = "unhealthy"

    # Disk health check
    try:
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100

        if disk_usage_percent > 95:
            disk_status = "unhealthy"
            overall_status = "unhealthy"
        elif disk_usage_percent > 85:
            disk_status = "degraded"
            if overall_status == "healthy":
                overall_status = "degraded"
        else:
            disk_status = "healthy"

        health_status["checks"]["disk"] = {
            "status": disk_status,
            "usage_percent": round(disk_usage_percent, 2),
            "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
            "total_gb": round(disk.total / 1024 / 1024 / 1024, 2)
        }
    except Exception as e:
        health_status["checks"]["disk"] = {
            "status": "unhealthy",
            "message": f"Disk check failed: {str(e)}"
        }
        overall_status = "unhealthy"

    # Environment health check
    try:
        env_vars = [
            "DATABASE_URL",
            "JWT_SECRET",
            "ENVIRONMENT"
        ]

        missing_vars = []
        for var in env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            env_status = "degraded"
            if overall_status == "healthy":
                overall_status = "degraded"
            env_message = f"Missing environment variables: {', '.join(missing_vars)}"
        else:
            env_status = "healthy"
            env_message = "All required environment variables present"

        health_status["checks"]["environment"] = {
            "status": env_status,
            "message": env_message
        }
    except Exception as e:
        health_status["checks"]["environment"] = {
            "status": "unhealthy",
            "message": f"Environment check failed: {str(e)}"
        }
        overall_status = "unhealthy"

    health_status["status"] = overall_status

    # Return appropriate HTTP status code
    if overall_status == "healthy":
        return health_status
    elif overall_status == "degraded":
        return JSONResponse(status_code=200, content=health_status)
    else:
        return JSONResponse(status_code=503, content=health_status)

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check for Kubernetes"""
    try:
        # Check if database is accessible
        db.execute("SELECT 1")
        return {"status": "ready", "timestamp": time.time()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {str(e)}")

@router.get("/health/live")
async def liveness_check():
    """Liveness check for Kubernetes"""
    return {"status": "alive", "timestamp": time.time()}

@router.get("/metrics")
async def metrics():
    """Basic application metrics"""
    try:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            "timestamp": time.time(),
            "system": {
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "available_mb": round(memory.available / 1024 / 1024, 2),
                    "usage_percent": memory.percent
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "usage_percent": round((disk.used / disk.total) * 100, 2)
                }
            },
            "application": {
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "version": os.getenv("APP_VERSION", "unknown")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
