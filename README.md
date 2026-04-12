# Emotion Vision

A production-grade facial emotion recognition system built by [Chirag Dahiya](https://github.com/ChiragandAI).

Detects faces in images, videos, and live webcam streams, then classifies the emotion of every detected face in real time. Built as a full-stack portfolio project demonstrating end-to-end ML engineering — from fine-tuning to deployed product.

**Live demo:** coming soon

---

## What it does

- Detects all faces in an image, video, or webcam stream using a YOLO-based face detector
- Classifies the emotion of each detected face: happy, sad, angry, surprised, fearful, disgusted, neutral
- Overlays bounding boxes, emotion labels, and confidence scores on the output
- Applies temporal smoothing on video and stream input to prevent flickering predictions
- Serves results through a React frontend and FastAPI backend

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Face detection | YOLO11 |
| Emotion classification | ResNet18 (baseline) → EfficientNet-B2 (fine-tuned) |
| Inference modes | Mock / Local / External provider |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Infrastructure | GCP Cloud Run + Terraform |
| Experiment tracking | Weights & Biases |
| Frontend hosting | Vercel |

---

## ML Pipeline

```
Input (image / video / webcam)
    │
    ▼
YOLO face detector
    │  bounding boxes + confidence
    ▼
Face crop + padding + resize (224x224)
    │
    ▼
Emotion classifier (EfficientNet-B2)
    │  class probabilities
    ▼
Temporal smoothing (video/stream only)
    │
    ▼
Annotated output + structured JSON response
```

---

## Fine-tuning

This project explicitly demonstrates fine-tuning, not just model consumption.

- **Emotion classifier**: fine-tuned on RAF-DB and FER2013 datasets
- **Face detector**: YOLO11 validated out of the box, fine-tuned on WiderFace if domain performance requires it
- Training done in Kaggle and Google Colab notebooks (see `notebooks/`)
- Baseline vs fine-tuned comparisons documented with metrics

---

## Local development

### Prerequisites

- Python 3.11
- Node.js 20
- Docker (optional)

### Run in mock mode (no model weights needed)

Backend:

```bash
python3.11 -m venv .venv311
source .venv311/bin/activate
pip install -r backend/requirements.txt
INFERENCE_MODE=mock uvicorn app.main:app --reload --app-dir backend
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` — the frontend connects to the backend in mock mode and returns stable demo predictions.

### Run with Docker

```bash
docker compose up --build
```

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000`

---

## CLI inference scripts

```bash
# Image
python scripts/infer_image.py --input path/to/image.jpg --output outputs/result.jpg

# Video
python scripts/infer_video.py --input path/to/video.mp4 --output outputs/result.mp4

# Webcam
python scripts/infer_stream.py --source 0
```

---

## Project structure

```
emotion-vision/
  frontend/        React + Vite app
  backend/         FastAPI inference API
  src/             Core ML pipeline (detection, emotion, tracking, inference)
  notebooks/       Fine-tuning and evaluation notebooks
  configs/         Training and inference configuration
  scripts/         CLI scripts for inference and training
  infra/           Terraform infrastructure as code
  docker/          Dockerfiles for frontend and backend
  tests/           Unit and integration tests
```

---

## Deployment

Infrastructure is defined in Terraform and deployed to GCP Cloud Run. CI/CD runs on GitHub Actions — every push triggers lint, tests, Docker build, and staging deployment. Production uses canary rollouts via Cloud Run traffic splitting.

See [DEPLOYMENT_PLAN.md](DEPLOYMENT_PLAN.md) for the full architecture.

---

## Author

**Chirag Dahiya** — [github.com/ChiragandAI](https://github.com/ChiragandAI)
