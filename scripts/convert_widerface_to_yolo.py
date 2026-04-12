from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml
from PIL import Image


def resolve_image_root(raw_root: Path, split: str) -> Path:
    candidates = [
        raw_root / f"WIDER_{split}" / "images",
        raw_root / f"WIDER_{split}" / f"WIDER_{split}" / "images",
        raw_root / f"WIDER_{split.upper()}" / "images",
        raw_root / f"WIDER_{split.upper()}" / f"WIDER_{split.upper()}" / "images",
        raw_root / f"wider_{split}" / "images",
        raw_root / f"wider_{split}",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve image root for split={split}: {candidates}")


def resolve_annotation_root(raw_root: Path) -> Path:
    candidates = [
        raw_root / "wider_face_split",
        raw_root / "wider_face_split" / "wider_face_split",
    ]
    for candidate in candidates:
        if (candidate / "wider_face_train_bbx_gt.txt").exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve annotation root under {raw_root}")


def ensure_dirs(yolo_root: Path) -> None:
    for rel in ("images/train", "images/val", "labels/train", "labels/val"):
        (yolo_root / rel).mkdir(parents=True, exist_ok=True)


def parse_annotations(annotation_path: Path) -> list[tuple[str, list[tuple[int, int, int, int]]]]:
    lines = annotation_path.read_text().splitlines()
    idx = 0
    records: list[tuple[str, list[tuple[int, int, int, int]]]] = []
    while idx < len(lines):
        image_rel = lines[idx].strip()
        idx += 1
        face_count = int(lines[idx].strip())
        idx += 1
        boxes: list[tuple[int, int, int, int]] = []
        for _ in range(face_count):
            parts = [int(v) for v in lines[idx].strip().split()]
            idx += 1
            x, y, w, h = parts[:4]
            if w > 0 and h > 0:
                boxes.append((x, y, w, h))
        records.append((image_rel, boxes))
    return records


def box_to_yolo(box: tuple[int, int, int, int], image_width: int, image_height: int) -> tuple[float, float, float, float]:
    x, y, w, h = box
    x_center = (x + w / 2.0) / image_width
    y_center = (y + h / 2.0) / image_height
    width = w / image_width
    height = h / image_height
    return x_center, y_center, width, height


def convert_split(split_name: str, annotation_file: Path, image_root: Path, yolo_root: Path) -> tuple[int, int]:
    records = parse_annotations(annotation_file)
    converted_images = 0
    converted_boxes = 0

    for idx, (image_rel, boxes) in enumerate(records, start=1):
        source_image = image_root / image_rel
        if not source_image.exists():
            continue

        event_name = Path(image_rel).parent.name
        image_name = Path(image_rel).name
        target_image_dir = yolo_root / "images" / split_name / event_name
        target_label_dir = yolo_root / "labels" / split_name / event_name
        target_image_dir.mkdir(parents=True, exist_ok=True)
        target_label_dir.mkdir(parents=True, exist_ok=True)

        target_image = target_image_dir / image_name
        target_label = target_label_dir / f"{Path(image_name).stem}.txt"

        if not target_image.exists():
            shutil.copy2(source_image, target_image)

        with Image.open(source_image) as img:
            image_width, image_height = img.size

        yolo_lines = []
        for box in boxes:
            x_center, y_center, width, height = box_to_yolo(box, image_width, image_height)
            yolo_lines.append(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}")

        target_label.write_text("\n".join(yolo_lines))
        converted_images += 1
        converted_boxes += len(yolo_lines)

        if idx % 1000 == 0:
            print(f"[{split_name}] processed {idx}/{len(records)} records, converted {converted_images} images")

    return converted_images, converted_boxes


def write_data_yaml(yolo_root: Path) -> Path:
    data = {
        "path": str(yolo_root.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {0: "face"},
    }
    yaml_path = yolo_root / "data.yaml"
    yaml_path.write_text(yaml.safe_dump(data, sort_keys=False))
    return yaml_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert WIDERFace annotations to YOLO format.")
    parser.add_argument("--raw-root", required=True, help="Path to extracted WIDERFace root.")
    parser.add_argument("--output-root", required=True, help="Where to write YOLO images/labels/data.yaml.")
    args = parser.parse_args()

    raw_root = Path(args.raw_root).expanduser().resolve()
    yolo_root = Path(args.output_root).expanduser().resolve()

    ensure_dirs(yolo_root)

    annotation_root = resolve_annotation_root(raw_root)
    train_annotations = annotation_root / "wider_face_train_bbx_gt.txt"
    val_annotations = annotation_root / "wider_face_val_bbx_gt.txt"
    train_images = resolve_image_root(raw_root, "train")
    val_images = resolve_image_root(raw_root, "val")

    print("raw_root:", raw_root)
    print("annotation_root:", annotation_root)
    print("train_annotations:", train_annotations, train_annotations.exists())
    print("val_annotations:", val_annotations, val_annotations.exists())
    print("train_images:", train_images, train_images.exists())
    print("val_images:", val_images, val_images.exists())
    print("output_root:", yolo_root)

    train_images_count, train_boxes_count = convert_split("train", train_annotations, train_images, yolo_root)
    val_images_count, val_boxes_count = convert_split("val", val_annotations, val_images, yolo_root)
    yaml_path = write_data_yaml(yolo_root)

    print("converted train images:", train_images_count)
    print("converted val images:", val_images_count)
    print("train boxes:", train_boxes_count)
    print("val boxes:", val_boxes_count)
    print("data.yaml:", yaml_path)


if __name__ == "__main__":
    main()
