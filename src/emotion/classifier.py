from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

import cv2
import numpy as np
import torch
from torch import nn
from torchvision import models, transforms


@dataclass
class EmotionPrediction:
    label: str
    confidence: float
    probabilities: list[float]


class EmotionClassifier:
    def __init__(
        self,
        model_name: str,
        weights_path: str,
        class_names: Sequence[str],
        image_size: int = 224,
        dropout: float = 0.2,
        device: str = "cpu",
        class_bias: dict[str, float] | None = None,
    ) -> None:
        self.class_names = list(class_names)
        self.device = torch.device(device)
        bias = torch.zeros(len(self.class_names), dtype=torch.float32)
        for name, value in (class_bias or {}).items():
            if name in self.class_names:
                bias[self.class_names.index(name)] = float(value)
        self.class_bias = bias.to(self.device)
        weights = Path(weights_path)
        self.model = self._build_model(
            model_name,
            len(self.class_names),
            dropout,
            use_pretrained=not weights.exists(),
        ).to(self.device)
        self.transform = transforms.Compose(
            [
                transforms.ToPILImage(),
                transforms.Resize((image_size, image_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
            ]
        )
        if weights.exists():
            state = torch.load(weights, map_location=self.device)
            self.model.load_state_dict(state)
        self.model.eval()

    def _build_model(self, model_name: str, num_classes: int, dropout: float, use_pretrained: bool) -> nn.Module:
        if model_name == "efficientnet_b2":
            weights = models.EfficientNet_B2_Weights.DEFAULT if use_pretrained else None
            model = models.efficientnet_b2(weights=weights)
            in_features = model.classifier[1].in_features
            model.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
            return model

        weights = models.ResNet18_Weights.DEFAULT if use_pretrained else None
        model = models.resnet18(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
        return model

    @torch.inference_mode()
    def predict(self, face_bgr: np.ndarray, apply_bias: bool = True) -> EmotionPrediction:
        return self.predict_batch([face_bgr], apply_bias=apply_bias)[0]

    @torch.inference_mode()
    def predict_batch(self, faces_bgr: list[np.ndarray], apply_bias: bool = True) -> list[EmotionPrediction]:
        if not faces_bgr:
            return []
        tensors = [self.transform(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in faces_bgr]
        batch = torch.stack(tensors).to(self.device)
        logits = self.model(batch)
        if apply_bias:
            logits = logits + self.class_bias
        probs = torch.softmax(logits, dim=1).detach().cpu().numpy()
        results: list[EmotionPrediction] = []
        for row in probs:
            index = int(np.argmax(row))
            results.append(
                EmotionPrediction(
                    label=self.class_names[index],
                    confidence=float(row[index]),
                    probabilities=[float(p) for p in row.tolist()],
                )
            )
        return results
