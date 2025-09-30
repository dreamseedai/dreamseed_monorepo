from fastapi import APIRouter, Depends, HTTPException, Response, Request, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Content
from app.deps import get_current_user
from app.export.html import build_html
from app.core.ratelimit import check_rate_limit
from app.core.config import get_settings
import os, json, time, asyncio
from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

router = APIRouter(prefix="/export", tags=["export"])


@router.get("/content/{content_id}.html")
async def export_html(content_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = db.get(Content, content_id)
    if not row or row.deleted_at is not None:
        raise HTTPException(404, "Not found")
    ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    allowed = await check_rate_limit(f"export:{ip}", get_settings().export_rate_limit_per_min, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many export requests")
    author = getattr(user, "email", None)
    created_iso = row.created_at.isoformat() if row.created_at else None
    s = get_settings()
    html = build_html(
        row.doc,
        title=row.title,
        author=author,
        created_at_iso=created_iso,
        logo_url=os.getenv("PDF_LOGO_URL") or None,
        size=os.getenv("PDF_PAGE_SIZE", "A4"),
        brand=os.getenv("PDF_BRAND", "DreamSeed"),
    )
    return Response(content=html, media_type="text/html; charset=utf-8")


@router.get("/content/{content_id}.pdf")
async def export_pdf(content_id: int, request: Request, db: Session = Depends(get_db), user=Depends(get_current_user)):
    row = db.get(Content, content_id)
    if not row or row.deleted_at is not None:
        raise HTTPException(404, "Not found")
    ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    allowed = await check_rate_limit(f"export:{ip}", get_settings().export_rate_limit_per_min, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many export requests")
    author = getattr(user, "email", None)
    created_iso = row.created_at.isoformat() if row.created_at else None
    s = get_settings()
    html = build_html(
        row.doc,
        title=row.title,
        author=author,
        created_at_iso=created_iso,
        logo_url=os.getenv("PDF_LOGO_URL") or None,
        size=os.getenv("PDF_PAGE_SIZE", "A4"),
        brand=os.getenv("PDF_BRAND", "DreamSeed"),
    )
    from weasyprint import HTML
    pdf_bytes = HTML(string=html).write_pdf()
    headers = {"Content-Disposition": f'attachment; filename="content_{content_id}.pdf"'}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/zip")
async def export_zip(
    ids: str,
    request: Request,
    fmt: str = "pdf",
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    id_list = [int(x) for x in ids.split(",") if x.strip().isdigit()]
    if not id_list:
        raise HTTPException(400, "No ids")
    ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
    allowed = await check_rate_limit(f"export:{ip}", get_settings().export_rate_limit_per_min, 60)
    if not allowed:
        raise HTTPException(status_code=429, detail="Too many export requests")
    is_admin = getattr(user, "role", "user") == "admin"

    job_id = f"{user.id}-{int(time.time())}"
    _progress_set(job_id, 0)
    buf = BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as z:
        total = len(id_list)
        done = 0
        for cid in id_list:
            row = db.get(Content, cid)
            if not row or row.deleted_at is not None:
                done += 1
                _progress_set(job_id, int(done * 100 / max(1, total)))
                continue
            if not is_admin and row.author_id != user.id:
                done += 1
                _progress_set(job_id, int(done * 100 / max(1, total)))
                continue
            author = getattr(user, "email", None)
            created_iso = row.created_at.isoformat() if row.created_at else None
            html = build_html(
                row.doc,
                title=row.title,
                author=author,
                created_at_iso=created_iso,
                logo_url=os.getenv("PDF_LOGO_URL") or None,
                size=os.getenv("PDF_PAGE_SIZE", "A4"),
                brand=os.getenv("PDF_BRAND", "DreamSeed"),
            )
            if fmt == "html":
                z.writestr(f"content_{cid}.html", html.encode("utf-8"))
            else:
                from weasyprint import HTML
                pdf_bytes = HTML(string=html).write_pdf() or b""
                z.writestr(f"content_{cid}.pdf", pdf_bytes)
            done += 1
            _progress_set(job_id, int(done * 100 / max(1, total)))
    buf.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="export_{fmt}.zip"', "X-Export-Job": job_id}
    return Response(content=buf.read(), media_type="application/zip", headers=headers)


# --- Progress tracking (memory/redis) ---
_progress_mem: dict[str, int] = {}

def _progress_set(job_id: str, val: int) -> None:
    s = get_settings()
    if s.redis_url:
        import redis.asyncio as redis  # type: ignore
        r = redis.from_url(s.redis_url, decode_responses=True)
        async def _set():
            await r.setex(f"export:prog:{job_id}", int(os.getenv("EXPORT_PROGRESS_TTL", "600")), str(val))
        asyncio.get_event_loop().create_task(_set())
    else:
        _progress_mem[job_id] = val

async def _progress_get(job_id: str) -> int:
    s = get_settings()
    if s.redis_url:
        import redis.asyncio as redis  # type: ignore
        r = redis.from_url(s.redis_url, decode_responses=True)
        v = await r.get(f"export:prog:{job_id}")
        return int(v) if v and v.isdigit() else 0
    return _progress_mem.get(job_id, 0)

@router.websocket("/export/ws/{job_id}")
async def export_progress_ws(ws: WebSocket, job_id: str):
    await ws.accept()
    try:
        while True:
            p = await _progress_get(job_id)
            await ws.send_text(json.dumps({"progress": p}))
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return


