from __future__ import annotations

import logging
import os
from pathlib import Path

log = logging.getLogger(__name__)

WEIGHTS = [
    ("detection/yolo_face.pt", "models/detection/yolo_face.pt"),
    ("emotion/emotion_resnet18.pt", "models/emotion/emotion_resnet18.pt"),
]


def ensure_weights(project_root: Path) -> None:
    bucket_name = os.getenv("MODEL_BUCKET")
    if not bucket_name:
        log.info("MODEL_BUCKET unset; skipping GCS download")
        return

    from google.cloud import storage

    client = storage.Client()
    bucket = client.bucket(bucket_name)

    for blob_name, rel_path in WEIGHTS:
        dest = project_root / rel_path
        if dest.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        log.info("Downloading gs://%s/%s -> %s", bucket_name, blob_name, dest)
        bucket.blob(blob_name).download_to_filename(str(dest))
