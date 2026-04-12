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
    ) -> None:
        self.class_names = list(class_names)
        self.device = torch.device(device)
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
    def predict(self, face_bgr: np.ndarray) -> EmotionPrediction:
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        tensor = self.transform(rgb).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)[0].detach().cpu().numpy()
        index = int(np.argmax(probs))
        return EmotionPrediction(
            label=self.class_names[index],
            confidence=float(probs[index]),
            probabilities=[float(p) for p in probs.tolist()],
        )
