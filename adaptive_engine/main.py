from fastapi import FastAPI
from contextlib import asynccontextmanager

from adaptive_engine.routers import exam_session
from adaptive_engine.routers import settings as settings_router
from adaptive_engine.routers import health as health_router
from adaptive_engine.routers import reports as reports_router
from adaptive_engine.config import get_settings
from adaptive_engine.services.scheduler import RepeatingTimer
from adaptive_engine.services.irt_updater import run_irt_update_once, fetch_stats_from_db, persist_update_to_db
from adaptive_engine.services.session_repo import set_backend_override, get_session_repo


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: check backend connectivity and fallback
    s = get_settings()
    scheduler: RepeatingTimer | None = None
    if s.session_backend == "redis":
        try:
            repo = get_session_repo()
            if getattr(repo, "backend", "memory") != "redis":
                set_backend_override("memory")
                print("[adaptive_engine] Redis unavailable; falling back to memory session backend.")
            else:
                print("[adaptive_engine] Redis session backend connected.")
        except Exception as e:
            set_backend_override("memory")
            print(f"[adaptive_engine] Redis check error: {e}; using memory backend.")
    # Start background IRT updater if enabled
    if s.irt_update_enabled:
        def _job():
            # Use DB-backed functions when database_url is set; otherwise no-op
            fetch = fetch_stats_from_db if s.database_url else (lambda: iter(()))
            persist = persist_update_to_db if s.database_url else None
            updated = run_irt_update_once(fetch_stats=fetch, persist_update=persist)
            if updated:
                print(f"[adaptive_engine] IRT updater: updated {updated} items")
        scheduler = RepeatingTimer(s.irt_update_interval_sec, _job)
        scheduler.start()

    yield
    # Shutdown: nothing for now
    if scheduler is not None:
        scheduler.stop()


app = FastAPI(title="Adaptive Testing Engine", lifespan=lifespan)
app.include_router(exam_session.router)
app.include_router(settings_router.router)
app.include_router(health_router.router)
app.include_router(reports_router.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8008)
