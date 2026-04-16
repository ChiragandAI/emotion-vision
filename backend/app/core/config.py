from dataclasses import dataclass, field
import os


def default_allowed_origins() -> list[str]:
    configured = os.getenv("ALLOWED_ORIGINS")
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]
    return [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "https://emotion-vision.vercel.app",
    ]


@dataclass
class Settings:
    app_name: str = "emotion-vision-api"
    project_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    allowed_origins: list[str] = field(default_factory=default_allowed_origins)
    inference_mode: str = os.getenv("INFERENCE_MODE", "mock")
    provider_name: str = os.getenv("INFERENCE_PROVIDER", "none")
    provider_api_url: str = os.getenv("INFERENCE_PROVIDER_URL", "")
    provider_api_key: str = os.getenv("INFERENCE_PROVIDER_API_KEY", "")
    max_image_upload_bytes: int = int(os.getenv("MAX_IMAGE_UPLOAD_BYTES", str(8 * 1024 * 1024)))
    max_video_upload_bytes: int = int(os.getenv("MAX_VIDEO_UPLOAD_BYTES", str(120 * 1024 * 1024)))
    generated_video_ttl_seconds: int = int(os.getenv("GENERATED_VIDEO_TTL_SECONDS", str(20 * 60)))


settings = Settings()
