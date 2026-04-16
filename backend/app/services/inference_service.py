from __future__ import annotations

import base64
import os
from pathlib import Path
import sys
import tempfile
import time
from uuid import uuid4

import cv2
import numpy as np

from app.core.config import settings
from app.services.provider_client import ProviderInferenceClient

ROOT = Path(settings.project_root)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class InferenceService:
    def __init__(self) -> None:
        self.mode = settings.inference_mode
        self.provider = ProviderInferenceClient(
            provider_name=settings.provider_name,
            api_url=settings.provider_api_url,
            api_key=settings.provider_api_key,
        )
        self._pipeline = None
        self._video_output_dir = ROOT / "outputs" / "videos"
        self._video_output_dir.mkdir(parents=True, exist_ok=True)
        self._generated_video_ttl_seconds = settings.generated_video_ttl_seconds

    def warmup(self) -> None:
        """Eagerly load weights and run one inference so readiness reflects real capability."""
        if self.mode == "local":
            pipeline = self._get_pipeline()
            dummy = np.zeros((64, 64, 3), dtype=np.uint8)
            pipeline.predict_frame(dummy, use_tracking=False)

    def infer_image_bytes(self, content: bytes, filename: str) -> dict:
        self._cleanup_generated_videos()
        if self.mode == "provider":
            return self.provider.infer_image_bytes(content, filename)

        frame = self._decode_image(content)
        if self.mode == "mock":
            return self._mock_infer_image(frame, filename)

        pipeline = self._get_pipeline()
        results = pipeline.predict_frame(frame, use_tracking=False)
        return {
            "filename": filename,
            "mode": self.mode,
            "faces": pipeline.frame_to_dict(results),
        }

    def infer_video_bytes(self, content: bytes, filename: str) -> dict:
        self._cleanup_generated_videos()
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix or ".mp4") as tmp:
            tmp.write(content)
            tmp_path = tmp.name

        try:
            capture = cv2.VideoCapture(tmp_path)
            if not capture.isOpened():
                raise ValueError("Could not open uploaded video.")

            sample_frames = []
            frames_processed = 0
            frame_index = 0
            sample_stride = 15
            max_samples = 8
            fps = capture.get(cv2.CAP_PROP_FPS) or 24.0
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
            output_path = self._video_output_dir / f"{Path(filename).stem}-{uuid4().hex[:8]}.mp4"
            writer = None

            if width > 0 and height > 0:
                writer = cv2.VideoWriter(
                    str(output_path),
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    fps,
                    (width, height),
                )

            while True:
                ok, frame = capture.read()
                if not ok:
                    break

                results = self._predict_faces_for_frame(frame, filename, use_tracking=True)
                annotated = self._annotate_frame(frame, results)

                if writer is not None:
                    writer.write(annotated)

                if frame_index % sample_stride == 0 and len(sample_frames) < max_samples:
                    sample_frames.append(
                        {
                            "frame_index": frame_index,
                            "image_data_url": self._encode_frame_data_url(annotated),
                            "faces": results,
                        }
                    )
                    frames_processed += 1
                frame_index += 1

            capture.release()
            if writer is not None:
                writer.release()

            annotated_video_url = f"/outputs/videos/{output_path.name}" if output_path.exists() else None
            return {
                "filename": filename,
                "mode": self.mode,
                "frames_processed": frames_processed,
                "annotated_video_url": annotated_video_url,
                "sample_frames": sample_frames,
            }
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def _get_pipeline(self):
        if self._pipeline is None:
            from app.services.model_loader import ensure_weights
            from src.utils.modeling import build_pipeline

            ensure_weights(ROOT)
            self._pipeline = build_pipeline()
        return self._pipeline

    def _decode_image(self, content: bytes) -> np.ndarray:
        array = np.frombuffer(content, dtype=np.uint8)
        image = cv2.imdecode(array, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Could not decode image bytes.")
        return image

    def _mock_infer_image(self, frame: np.ndarray, filename: str) -> dict:
        return {
            "filename": filename,
            "mode": "mock",
            "faces": self._mock_faces(frame),
        }

    def _encode_frame_data_url(self, frame: np.ndarray) -> str:
        ok, encoded = cv2.imencode(".jpg", frame)
        if not ok:
            raise ValueError("Could not encode video frame.")
        payload = base64.b64encode(encoded.tobytes()).decode("ascii")
        return f"data:image/jpeg;base64,{payload}"

    def _mock_faces(self, frame: np.ndarray) -> list[dict]:
        height, width = frame.shape[:2]
        x1 = max(width // 4, 0)
        y1 = max(height // 5, 0)
        x2 = min((width * 3) // 4, width)
        y2 = min((height * 4) // 5, height)
        return [
            {
                "track_id": None,
                "box": [x1, y1, x2, y2],
                "detection_confidence": 0.93,
                "emotion_label": "happy",
                "emotion_confidence": 0.81,
                "probabilities": [0.04, 0.03, 0.02, 0.81, 0.05, 0.03, 0.02],
            }
        ]

    def _predict_faces_for_frame(self, frame: np.ndarray, filename: str, use_tracking: bool) -> list[dict]:
        if self.mode == "mock":
            return self._mock_faces(frame)

        pipeline = self._get_pipeline()
        results = pipeline.predict_frame(frame, use_tracking=use_tracking)
        return pipeline.frame_to_dict(results)

    def _annotate_frame(self, frame: np.ndarray, faces: list[dict]) -> np.ndarray:
        canvas = frame.copy()
        for face in faces:
            x1, y1, x2, y2 = face["box"]
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (40, 40, 220), 2)
            text = face["emotion_label"]
            if face["track_id"] is not None:
                text = f"id={face['track_id']} {text}"
            text = f"{text} {face['emotion_confidence']:.2f}"
            cv2.putText(canvas, text, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 220), 2)
        return canvas

    def _cleanup_generated_videos(self) -> None:
        if self._generated_video_ttl_seconds <= 0:
            return

        cutoff = time.time() - self._generated_video_ttl_seconds
        for path in self._video_output_dir.glob("*.mp4"):
            try:
                if path.stat().st_mtime < cutoff:
                    path.unlink(missing_ok=True)
            except OSError:
                continue
