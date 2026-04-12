from __future__ import annotations

import argparse
from pathlib import Path

import cv2

import _bootstrap  # noqa: F401
from src.utils.io import ensure_parent
from src.utils.modeling import build_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run video emotion inference.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not Path(args.input).exists():
        raise SystemExit(f"Input video not found: {args.input}")

    pipeline = build_pipeline()
    capture = cv2.VideoCapture(args.input)
    if not capture.isOpened():
        raise SystemExit(f"Could not open video: {args.input}")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0

    ensure_parent(args.output)
    writer = cv2.VideoWriter(
        args.output,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        results = pipeline.predict_frame(frame, use_tracking=True)
        annotated = pipeline.annotate_frame(frame, results)
        writer.write(annotated)

    capture.release()
    writer.release()
    print(f"Saved annotated video to {args.output}")


if __name__ == "__main__":
    main()
