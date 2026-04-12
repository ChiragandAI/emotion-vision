from __future__ import annotations

import argparse
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

    model.train()
    for epoch in range(args.epochs):
        total_loss = 0.0
        correct = 0
        total = 0
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            total_loss += float(loss.item()) * images.size(0)
            correct += int((logits.argmax(dim=1) == labels).sum().item())
            total += int(labels.size(0))
        avg_loss = total_loss / max(total, 1)
        accuracy = correct / max(total, 1)
        print(f"epoch={epoch + 1} loss={avg_loss:.4f} acc={accuracy:.4f}")

    weights_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), weights_path)
    print(f"Saved weights to {weights_path}")


if __name__ == "__main__":
    main()
