from __future__ import annotations

import argparse

import cv2

import _bootstrap  # noqa: F401
from src.utils.modeling import build_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run webcam or stream emotion inference.")
    parser.add_argument("--source", default="0", help="Camera index or stream URL.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    source = int(args.source) if args.source.isdigit() else args.source
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise SystemExit(f"Could not open source: {args.source}")

    pipeline = build_pipeline()
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        results = pipeline.predict_frame(frame, use_tracking=True)
        annotated = pipeline.annotate_frame(frame, results)
        cv2.imshow("emotion-stream", annotated)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            break

    capture.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
