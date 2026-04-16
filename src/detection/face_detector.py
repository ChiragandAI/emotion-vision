from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

try:
    from ultralytics import YOLO
except ImportError:  # pragma: no cover
    YOLO = None


@dataclass
class Detection:
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float

    @property
    def box(self) -> tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2


class FaceDetector:
    def __init__(
        self,
        weights_path: str,
        confidence_threshold: float = 0.35,
        iou_threshold: float = 0.45,
        padding: float = 0.1,
        fallback_cascade: Optional[str] = None,
        input_size: int = 640,
    ) -> None:
        self.weights_path = Path(weights_path)
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.padding = padding
        self.input_size = input_size
        self.model = self._load_yolo_model()
        cascade_path = fallback_cascade or cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.cascade = cv2.CascadeClassifier(cascade_path)

    def _load_yolo_model(self):
        if YOLO is None or not self.weights_path.exists():
            return None
        return YOLO(str(self.weights_path))

    def detect(self, image: np.ndarray) -> List[Detection]:
        detections = self._detect_with_yolo(image)
        if detections:
            return detections
        return self._detect_with_opencv(image)

    def _detect_with_yolo(self, image: np.ndarray) -> List[Detection]:
        if self.model is None:
            return []

        results = self.model.predict(
            source=image,
            conf=self.confidence_threshold,
            iou=self.iou_threshold,
            imgsz=self.input_size,
            verbose=False,
        )
        if not results:
            return []

        output: List[Detection] = []
        for box in results[0].boxes:
            conf = float(box.conf[0].item())
            x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
            output.append(Detection(x1=x1, y1=y1, x2=x2, y2=y2, confidence=conf))
        return output

    def _detect_with_opencv(self, image: np.ndarray) -> List[Detection]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        boxes = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
        output = []
        for x, y, w, h in boxes:
            output.append(Detection(x1=int(x), y1=int(y), x2=int(x + w), y2=int(y + h), confidence=0.5))
        return output

    def crop_face(self, image: np.ndarray, detection: Detection) -> np.ndarray:
        h, w = image.shape[:2]
        pad_x = int((detection.x2 - detection.x1) * self.padding)
        pad_y = int((detection.y2 - detection.y1) * self.padding)
        x1 = max(detection.x1 - pad_x, 0)
        y1 = max(detection.y1 - pad_y, 0)
        x2 = min(detection.x2 + pad_x, w)
        y2 = min(detection.y2 + pad_y, h)
        return image[y1:y2, x1:x2].copy()

