from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def ensure_parent(path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def read_image(path: str) -> np.ndarray:
    image = cv2.imread(path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {path}")
    return image


def write_image(path: str, image: np.ndarray) -> None:
    ensure_parent(path)
    if not cv2.imwrite(path, image):
        raise RuntimeError(f"Could not write image: {path}")

