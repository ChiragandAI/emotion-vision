import asyncio
import json

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings
from app.core.rate_limit import limiter
from app.schemas.responses import DemoInfo, HealthInfo, ImageInferenceResponse, ProjectInfo, VideoJobResponse
from app.services.inference_service import InferenceService

router = APIRouter()
service = InferenceService()


@router.get("/project", response_model=ProjectInfo)
def project_info() -> ProjectInfo:
    return ProjectInfo(
        name="Emotion Vision",
        summary="Fine-tuned face detection and emotion classification portfolio project.",
        training_targets=["YOLO face detector", "CNN emotion classifier"],
    )


@router.get("/backend-health", response_model=HealthInfo)
def backend_health() -> HealthInfo:
    return HealthInfo(status="ok")


@router.get("/demo", response_model=DemoInfo)
def demo_info() -> DemoInfo:
    return DemoInfo(
        mode=service.mode,
        provider=service.provider.provider_name,
        prototype_ready=True,
        capabilities=["image_upload", "mock_predictions", "frontend_backend_contract"],
    )


@router.post("/infer/image", response_model=ImageInferenceResponse)
@limiter.limit("5/second;120/minute")
async def infer_image(
    request: Request,
    file: UploadFile = File(...),
    apply_bias: bool = Form(False),
) -> ImageInferenceResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Expected an image upload.")

    content = await file.read()
    if len(content) > settings.max_image_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Image exceeds {settings.max_image_upload_bytes // (1024 * 1024)} MB limit.")
    result = service.infer_image_bytes(content, file.filename or "upload-image", apply_bias=apply_bias)
    return ImageInferenceResponse(**result)


@router.post("/infer/video", response_model=VideoJobResponse)
@limiter.limit("1/second;5/minute")
async def infer_video(request: Request, file: UploadFile = File(...)) -> VideoJobResponse:
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Expected a video upload.")

    content = await file.read()
    if len(content) > settings.max_video_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Video exceeds {settings.max_video_upload_bytes // (1024 * 1024)} MB limit.")
    job_id = service.start_video_job(content, file.filename or "upload-video")
    return VideoJobResponse(job_id=job_id)


@router.get("/infer/video/{job_id}/events")
async def infer_video_events(job_id: str, request: Request):
    if service.get_job(job_id) is None:
        raise HTTPException(status_code=404, detail="Unknown job.")

    async def event_stream():
        while True:
            if await request.is_disconnected():
                break
            job = service.get_job(job_id)
            if job is None:
                yield {"event": "error", "data": json.dumps({"error": "job missing"})}
                return
            yield {"data": json.dumps(job)}
            if job["status"] in ("done", "error"):
                return
            await asyncio.sleep(0.5)

    return EventSourceResponse(event_stream())
