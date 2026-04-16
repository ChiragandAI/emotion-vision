from __future__ import annotations

import argparse
import os
from pathlib import Path

import _bootstrap  # noqa: F401


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Starter entrypoint for YOLO11 face detector fine-tuning.")
    parser.add_argument("--data", required=True, help="Path to YOLO dataset YAML.")
    parser.add_argument("--model", default="yolo11n.pt", help="Base YOLO11 checkpoint.")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--wandb", action="store_true", help="Log run to Weights & Biases.")
    parser.add_argument("--wandb-project", default="emotion-vision")
    parser.add_argument("--wandb-run-name", default=None)
    return parser.parse_args()


def _init_wandb(args: argparse.Namespace):
    if not args.wandb:
        return None
    try:
        import wandb
    except ImportError:
        print("wandb not installed; skipping experiment logging.")
        return None
    if not os.environ.get("WANDB_API_KEY"):
        print("WANDB_API_KEY not set; skipping experiment logging.")
        return None
    return wandb.init(
        project=args.wandb_project,
        name=args.wandb_run_name,
        config={
            "base_model": args.model,
            "epochs": args.epochs,
            "imgsz": args.imgsz,
            "task": "face_detection",
        },
    )


def main() -> None:
    args = parse_args()
    try:
        from ultralytics import YOLO
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("ultralytics is required for detection training.") from exc

    if not Path(args.data).exists():
        raise SystemExit(f"Dataset config not found: {args.data}")

    run = _init_wandb(args)

    model = YOLO(args.model)
    results = model.train(data=args.data, epochs=args.epochs, imgsz=args.imgsz)

    if run is not None:
        import wandb

        save_dir = Path(getattr(results, "save_dir", "runs/detect/train"))
        best = save_dir / "weights" / "best.pt"
        if best.exists():
            artifact = wandb.Artifact(name="yolo-face-detector", type="model")
            artifact.add_file(str(best))
            run.log_artifact(artifact)
        run.finish()


if __name__ == "__main__":
    main()
