from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
from torch import nn
from torch.optim import AdamW
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

import _bootstrap  # noqa: F401
from src.utils.config import load_yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the baseline emotion classifier.")
    parser.add_argument("--data-dir", required=True, help="Dataset root arranged by class folders.")
    parser.add_argument("--config", default="configs/emotion/base.yaml")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--wandb", action="store_true", help="Log run to Weights & Biases.")
    parser.add_argument("--wandb-project", default="emotion-vision")
    parser.add_argument("--wandb-run-name", default=None)
    return parser.parse_args()


def build_model(model_name: str, num_classes: int, dropout: float) -> nn.Module:
    if model_name == "efficientnet_b2":
        model = models.efficientnet_b2(weights=models.EfficientNet_B2_Weights.DEFAULT)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
        return model
    model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
    return model


def _init_wandb(args: argparse.Namespace, config: dict, num_classes: int):
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
            "model_name": config.get("model_name"),
            "image_size": config.get("image_size"),
            "dropout": config.get("dropout"),
            "epochs": args.epochs,
            "batch_size": args.batch_size,
            "lr": args.lr,
            "num_classes": num_classes,
            "optimizer": "AdamW",
        },
    )


def main() -> None:
    args = parse_args()
    config = load_yaml(args.config)
    device = torch.device(config.get("device", "cpu"))
    image_size = int(config.get("image_size", 224))
    weights_path = Path(config["weights_path"])
    class_names = list(config["class_names"])

    transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    dataset = datasets.ImageFolder(args.data_dir, transform=transform)
    if dataset.classes != class_names:
        print(f"Warning: dataset classes {dataset.classes} do not match config classes {class_names}")
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=2)

    model = build_model(config["model_name"], num_classes=len(dataset.classes), dropout=float(config.get("dropout", 0.2)))
    model.to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = AdamW(model.parameters(), lr=args.lr)

    run = _init_wandb(args, config, num_classes=len(dataset.classes))

    model.train()
    for epoch in range(args.epochs):
        total_loss = 0.0
        correct = 0
        total = 0
        all_preds: list[int] = []
        all_labels: list[int] = []
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * images.size(0)
            preds = logits.argmax(dim=1)
            correct += int((preds == labels).sum().item())
            total += int(labels.size(0))
            all_preds.extend(preds.detach().cpu().tolist())
            all_labels.extend(labels.detach().cpu().tolist())
        avg_loss = total_loss / max(total, 1)
        accuracy = correct / max(total, 1)
        f1 = None
        try:
            from sklearn.metrics import f1_score

            f1 = float(f1_score(all_labels, all_preds, average="macro", zero_division=0))
        except ImportError:
            pass
        log_line = f"epoch={epoch + 1} loss={avg_loss:.4f} acc={accuracy:.4f}"
        if f1 is not None:
            log_line += f" f1={f1:.4f}"
        print(log_line)
        if run is not None:
            metrics = {"epoch": epoch + 1, "train/loss": avg_loss, "train/accuracy": accuracy}
            if f1 is not None:
                metrics["train/f1_macro"] = f1
            run.log(metrics)

    weights_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), weights_path)
    print(f"Saved weights to {weights_path}")

    if run is not None:
        import wandb

        artifact = wandb.Artifact(
            name=f"emotion-{config.get('model_name', 'model')}",
            type="model",
            metadata={"class_names": class_names, "image_size": image_size},
        )
        artifact.add_file(str(weights_path))
        run.log_artifact(artifact)
        run.finish()


if __name__ == "__main__":
    main()
