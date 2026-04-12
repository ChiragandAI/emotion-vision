from __future__ import annotations

from src.detection.face_detector import FaceDetector
from src.emotion.classifier import EmotionClassifier
from src.inference.pipeline import EmotionPipeline
from src.utils.config import load_yaml


def build_pipeline(
    detection_config_path: str = "configs/detection/base.yaml",
    emotion_config_path: str = "configs/emotion/base.yaml",
    inference_config_path: str = "configs/inference/base.yaml",
) -> EmotionPipeline:
    detection_cfg = load_yaml(detection_config_path)
    emotion_cfg = load_yaml(emotion_config_path)
    inference_cfg = load_yaml(inference_config_path)

    detector = FaceDetector(
        weights_path=detection_cfg["weights_path"],
        confidence_threshold=detection_cfg["confidence_threshold"],
        iou_threshold=detection_cfg["iou_threshold"],
        padding=detection_cfg["padding"],
    )
    classifier = EmotionClassifier(
        model_name=emotion_cfg["model_name"],
        weights_path=emotion_cfg["weights_path"],
        class_names=emotion_cfg["class_names"],
        image_size=emotion_cfg["image_size"],
        dropout=emotion_cfg["dropout"],
        device=emotion_cfg["device"],
    )
    return EmotionPipeline(
        detector=detector,
        classifier=classifier,
        uncertain_threshold=inference_cfg["uncertain_threshold"],
        smoothing_alpha=inference_cfg["smoothing_alpha"],
        track_max_missing=inference_cfg["track_max_missing"],
    )

