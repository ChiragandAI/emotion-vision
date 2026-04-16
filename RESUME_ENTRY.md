# Resume Entry — Emotion Vision

**Emotion Vision** — Real-time Multi-Face Emotion Recognition System
Live: https://emotion-vision.vercel.app | Code: https://github.com/ChiragandAI/emotion-vision

---

## Short (3 bullets)

- Built and deployed a real-time multi-face emotion recognition system by fine-tuning **YOLO** (WiderFace) for face detection and **ResNet-18** (FER) for 7-class emotion classification, served through a **FastAPI** backend and **React/Vite** frontend.
- Productionized full **MLOps pipeline** on **GCP Cloud Run** with **Terraform** IaC, **GitHub Actions CI/CD**, **Artifact Registry**, **Secret Manager** (version-pinned), versioned **GCS** model artifacts, and readiness/liveness probes enabling zero-downtime rollouts.
- Engineered IoU-tracking with exponential probability smoothing for stable per-track emotion inference; implemented image/video/webcam endpoints, fail-fast prod-config guard, and automated lint/type/test gates (ruff, mypy, pytest).

---

## Ultra-compact (1 line, for tight resumes)

**Emotion Vision** — Fine-tuned YOLO + ResNet-18 emotion recognition pipeline; deployed on GCP Cloud Run via Terraform IaC and GitHub Actions CI/CD, with versioned GCS model artifacts, Secret Manager, and zero-downtime readiness probes. *React/Vite + FastAPI + Docker.* [github.com/ChiragandAI/emotion-vision]

---

## Tech keywords (ATS)

Python, PyTorch, YOLO, ResNet-18, Fine-tuning, Transfer Learning, Computer Vision, OpenCV, FastAPI, React, Vite, Docker, GCP, Cloud Run, Artifact Registry, Cloud Storage (GCS), Secret Manager, Terraform, Infrastructure as Code, GitHub Actions, CI/CD, MLOps, Model Versioning, Workload Identity Federation, Pytest, Ruff, Mypy, REST API, Vercel.
