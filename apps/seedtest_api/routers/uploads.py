from __future__ import annotations

import os
import uuid
from typing import Any

import logging
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..deps import User, get_current_user
from ..settings import settings

router = APIRouter(prefix=f"{settings.API_PREFIX}", tags=["uploads"])


def _ensure_dir(path: str):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception as e:  # pragma: no cover
        raise HTTPException(500, f"cannot_create_upload_dir: {e}")


def _safe_ext(filename: str) -> str:
    base, ext = os.path.splitext(filename)
    ext = (ext or '').lower()
    if ext and all(c.isalnum() or c in ('.',) for c in ext):
        return ext
    return ''


def _org_subdir(user: User) -> str:
    try:
        if user.org_id is not None:
            return str(int(user.org_id))
    except Exception:
        pass
    return ""


def _scan_virus(path: str) -> None:
    # Placeholder for AV scan hook (e.g., clamav). Implement as needed.
    try:
        _ = path  # avoid linter warnings
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).warning("virus scan hook error: %s", e)


def _maybe_optimize_image(path: str, content_type: str) -> None:
    # Optional optimization hook (resize/compress). No-op by default.
    try:
        _ = (path, content_type)
    except Exception as e:  # pragma: no cover
        logging.getLogger(__name__).warning("optimize hook error: %s", e)


@router.post("/uploads/images")
async def upload_image(request: Request, file: UploadFile = File(...), current_user: User = Depends(get_current_user)) -> Any:
    # Require teacher/admin for uploads
    if not (current_user.is_teacher() or current_user.is_admin()):
        raise HTTPException(403, "forbidden")

    # Validate mime
    allowed = settings.ALLOWED_IMAGE_MIME or [
        "image/png", "image/jpeg", "image/webp", "image/gif", "image/jpg", "image/svg+xml"
    ]
    ctype = (file.content_type or '').lower()
    if ctype not in allowed:
        raise HTTPException(400, "unsupported_media_type")

    # Limit file size
    max_bytes = int(settings.UPLOAD_MAX_MB) * 1024 * 1024
    # Org-scoped directory if available
    sub = _org_subdir(current_user)
    base_dir = settings.UPLOAD_DIR
    dest_dir = os.path.join(base_dir, sub) if sub else base_dir
    _ensure_dir(dest_dir)

    # Generate destination path
    ext = _safe_ext(file.filename or '')
    fname = f"{uuid.uuid4().hex}{ext}"
    dest = os.path.join(dest_dir, fname)

    size = 0
    try:
        with open(dest, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_bytes:
                    out.close()
                    try:
                        os.remove(dest)
                    except Exception:
                        pass
                    raise HTTPException(413, "file_too_large")
                out.write(chunk)
    finally:
        try:
            await file.close()
        except Exception:
            pass

    # Optional hooks
    try:
        _scan_virus(dest)
        _maybe_optimize_image(dest, ctype)
    except Exception as e:
        logging.getLogger(__name__).warning("post-upload hooks failed: %s", e)

    # Build public URL (served via /uploads mount)
    # Respect X-Forwarded-* when behind proxy if available
    base_scheme = request.headers.get("x-forwarded-proto") or request.url.scheme
    base_host = request.headers.get("x-forwarded-host") or request.headers.get("host") or request.url.netloc
    if sub:
        public_url = f"{base_scheme}://{base_host}/uploads/{sub}/{fname}"
    else:
        public_url = f"{base_scheme}://{base_host}/uploads/{fname}"

    return JSONResponse({"url": public_url, "filename": fname, "content_type": ctype, "size": size})


class PresignRequest(BaseModel):
    filename: str
    content_type: str


@router.post("/uploads/images/presign")
async def presign_image_upload(request: Request, body: PresignRequest, current_user: User = Depends(get_current_user)) -> Any:
    """Generate a presigned POST for S3 to allow direct browser upload.

    Returns { url, fields, method: "POST", public_url, key }.
    Requires AWS_S3_BUCKET and AWS_S3_REGION.
    """
    if not (current_user.is_teacher() or current_user.is_admin()):
        raise HTTPException(403, "forbidden")

    allowed = settings.ALLOWED_IMAGE_MIME or [
        "image/png", "image/jpeg", "image/webp", "image/gif", "image/jpg", "image/svg+xml"
    ]
    ctype = (body.content_type or '').lower()
    if ctype not in allowed:
        raise HTTPException(400, "unsupported_media_type")

    if not (settings.AWS_S3_BUCKET and settings.AWS_S3_REGION):
        raise HTTPException(503, "s3_not_configured")

    ext = _safe_ext(body.filename)
    sub = _org_subdir(current_user)
    key_parts = [p for p in (settings.AWS_S3_PREFIX.strip('/'), sub, f"{uuid.uuid4().hex}{ext}") if p]
    key = "/".join(key_parts)

    try:
        import boto3  # type: ignore
        s3 = boto3.client("s3", region_name=settings.AWS_S3_REGION)
    except Exception as e:  # pragma: no cover
        raise HTTPException(503, f"s3_client_error: {e}")

    max_bytes = int(settings.UPLOAD_MAX_MB) * 1024 * 1024
    conditions = [
        ["content-length-range", 0, max_bytes],
        {"Content-Type": ctype},
    ]
    fields = {
        "Content-Type": ctype,
    }
    try:
        presigned = s3.generate_presigned_post(
            Bucket=settings.AWS_S3_BUCKET,
            Key=key,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=int(settings.UPLOAD_PRESIGN_EXP_SECS),
        )
    except Exception as e:  # pragma: no cover
        raise HTTPException(500, f"s3_presign_error: {e}")

    if settings.AWS_S3_PUBLIC_BASE:
        public_url = f"{settings.AWS_S3_PUBLIC_BASE.rstrip('/')}/{key}"
    else:
        public_url = f"https://{settings.AWS_S3_BUCKET}.s3.{settings.AWS_S3_REGION}.amazonaws.com/{key}"

    return JSONResponse({
        "method": "POST",
        "url": presigned.get("url"),
        "fields": presigned.get("fields"),
        "public_url": public_url,
        "key": key,
    })
