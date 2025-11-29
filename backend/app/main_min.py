import os
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()

app = FastAPI(title="Dreamseed Minimal API")


# health
@app.get("/__ok")
def ok():
    return {"ok": True}


# include only creator assistant (no DB/OpenAI hard deps)
try:
    from creator_assist_api import router as creator_assist_router  # type: ignore

    app.include_router(creator_assist_router)
except Exception as e:

    @app.get("/api/creator-assist")
    def creator_assist_fallback():
        return {"reply": f"[fallback] router load failed: {e}"}
