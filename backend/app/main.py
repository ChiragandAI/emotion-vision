from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import router as api_router
from app.core.config import settings
from pathlib import Path

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}


generated_dir = Path(settings.project_root) / "outputs"
generated_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=generated_dir), name="outputs")

app.include_router(api_router, prefix="/api/v1")
