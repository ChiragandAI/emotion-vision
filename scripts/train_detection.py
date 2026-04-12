from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starter entrypoint for YOLO11 face detector fine-tuning.")
    parser.add_argument("--data", required=True, help="Path to YOLO dataset YAML.")
    parser.add_argument("--model", default="yolo11n.pt", help="Base YOLO11 checkpoint.")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("ultralytics is required for detection training.") from exc

    if not Path(args.data).exists():
        raise SystemExit(f"Dataset config not found: {args.data}")

    model = YOLO(args.model)
    model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz)


if __name__ == "__main__":
    main()
