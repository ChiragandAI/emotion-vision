from __future__ import annotations

import argparse
from pathlib import Path

import _bootstrap  # noqa: F401
from src.utils.io import read_image
from src.utils.modeling import build_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a simple qualitative evaluation on one image.")
    parser.add_argument("--input", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not Path(args.input).exists():
        raise SystemExit(f"Input not found: {args.input}")
    pipeline = build_pipeline()
    image = read_image(args.input)
    results = pipeline.predict_frame(image, use_tracking=False)
    print(pipeline.frame_to_dict(results))


if __name__ == "__main__":
    main()
