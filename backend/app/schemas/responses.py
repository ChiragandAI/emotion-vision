from pydantic import BaseModel


class HealthInfo(BaseModel):
    status: str


class FacePrediction(BaseModel):
    track_id: int | None
    box: list[int]
    detection_confidence: float
    emotion_label: str
    emotion_confidence: float
    probabilities: list[float]


class ImageInferenceResponse(BaseModel):
    filename: str
    mode: str
    faces: list[FacePrediction]


class VideoFramePrediction(BaseModel):
    frame_index: int
    image_data_url: str
    faces: list[FacePrediction]


class VideoInferenceResponse(BaseModel):
    filename: str
    mode: str
    frames_processed: int
    annotated_video_url: str | None
    sample_frames: list[VideoFramePrediction]


class VideoJobResponse(BaseModel):
    job_id: str


class ProjectInfo(BaseModel):
    name: str
    summary: str
    training_targets: list[str]


class DemoInfo(BaseModel):
    mode: str
    provider: str
    prototype_ready: bool
    capabilities: list[str]
