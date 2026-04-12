from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

from src.detection.face_detector import FaceDetector
from src.emotion.classifier import EmotionClassifier
from src.tracking.smoother import SimpleTracker


@dataclass
class FaceResult:
    track_id: Optional[int]
    box: tuple[int, int, int, int]
    detection_confidence: float
    emotion_label: str
    emotion_confidence: float
    probabilities: list[float]


class EmotionPipeline:
    def __init__(
        self,
        detector: FaceDetector,
        classifier: EmotionClassifier,
        uncertain_threshold: float = 0.45,
        smoothing_alpha: float = 0.65,
        track_max_missing: int = 10,
    ) -> None:
        self.detector = detector
        self.classifier = classifier
        self.uncertain_threshold = uncertain_threshold
        self.tracker = SimpleTracker(alpha=smoothing_alpha, max_missing=track_max_missing)

    def predict_frame(self, frame: np.ndarray, use_tracking: bool = False) -> List[FaceResult]:
        detections = self.detector.detect(frame)
        raw_results: List[FaceResult] = []
        boxes: List[tuple[int, int, int, int]] = []
        probabilities: List[list[float]] = []

        for detection in detections:
            face = self.detector.crop_face(frame, detection)
            if face.size == 0:
                continue
            prediction = self.classifier.predict(face)
            label = prediction.label if prediction.confidence >= self.uncertain_threshold else "uncertain"
            result = FaceResult(
                track_id=None,
                box=detection.box,
                detection_confidence=detection.confidence,
                emotion_label=label,
                emotion_confidence=prediction.confidence,
                probabilities=prediction.probabilities,
            )
            raw_results.append(result)
            boxes.append(detection.box)
            probabilities.append(prediction.probabilities)

        if not use_tracking or not raw_results:
            return raw_results

        smoothed = self.tracker.update(boxes, probabilities)
        result_by_index: List[FaceResult] = []
        for index, (track_id, smoothed_probs) in enumerate(smoothed):
            top_index = int(np.argmax(smoothed_probs))
            confidence = float(smoothed_probs[top_index])
            label = self.classifier.class_names[top_index] if confidence >= self.uncertain_threshold else "uncertain"
            current = raw_results[index]
            result_by_index.append(
                FaceResult(
                    track_id=track_id,
                    box=current.box,
                    detection_confidence=current.detection_confidence,
                    emotion_label=label,
                    emotion_confidence=confidence,
                    probabilities=[float(v) for v in smoothed_probs],
                )
            )
        return result_by_index

    def annotate_frame(self, frame: np.ndarray, results: List[FaceResult], show_confidence: bool = True) -> np.ndarray:
        canvas = frame.copy()
        for result in results:
            x1, y1, x2, y2 = result.box
            cv2.rectangle(canvas, (x1, y1), (x2, y2), (70, 220, 70), 2)
            text = result.emotion_label
            if result.track_id is not None:
                text = f"id={result.track_id} {text}"
            if show_confidence:
                text = f"{text} {result.emotion_confidence:.2f}"
            cv2.putText(canvas, text, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 240, 40), 2)
        return canvas

    def frame_to_dict(self, results: List[FaceResult]) -> List[Dict[str, Any]]:
        return [
            {
                "track_id": result.track_id,
                "box": list(result.box),
                "detection_confidence": result.detection_confidence,
                "emotion_label": result.emotion_label,
                "emotion_confidence": result.emotion_confidence,
                "probabilities": result.probabilities,
            }
            for result in results
        ]

