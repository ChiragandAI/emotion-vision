from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import router as api_router, service
from app.core.config import settings
from app.core.rate_limit import limiter


@asynccontextmanager
async def lifespan(_app: FastAPI):
    service.warmup()
    _app.state.ready = True
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

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


@app.get("/health/ready")
def ready() -> dict[str, str]:
    if not getattr(app.state, "ready", False):
        raise HTTPException(status_code=503, detail="not ready")
    return {"status": "ready", "mode": service.mode, "environment": settings.environment}


generated_dir = Path(settings.project_root) / "outputs"
generated_dir.mkdir(parents=True, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=generated_dir), name="outputs")

app.include_router(api_router, prefix="/api/v1")
