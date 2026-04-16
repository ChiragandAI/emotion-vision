# Emotion Vision

A production-grade facial emotion recognition system built by [Chirag Dahiya](https://github.com/ChiragandAI) ([LinkedIn](https://www.linkedin.com/in/chiragdahiya)).

Detects faces in images, videos, and live webcam streams, then classifies the emotion of every detected face in real time. Built as a full-stack portfolio project demonstrating end-to-end ML engineering — from fine-tuning to deployed product.

**Live demo:** [emotion-vision.vercel.app](https://emotion-vision.vercel.app)

---

## What it does

- Detects all faces in an image, video, or webcam stream using a YOLO-based face detector
- Classifies the emotion of each detected face: happy, sad, angry, surprised, fearful, disgusted, neutral
- Overlays bounding boxes, emotion labels, and confidence scores on the output
- Applies temporal smoothing and per-track ID on video/stream input to prevent flickering predictions
- Streams per-frame video processing progress to the browser over Server-Sent Events
- Applies post-hoc logit calibration to suppress a known false-positive class on webcam captures
- Serves results through a React frontend and a rate-limited FastAPI backend

---

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite |
| Backend | FastAPI (Python) |
| Face detection | YOLO11 |
| Emotion classification | ResNet18 (fine-tuned) with post-hoc logit calibration |
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
Emotion classifier (ResNet18, fine-tuned)
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

- **Emotion classifier**: ResNet18 fine-tuned on RAF-DB and FER2013, with post-hoc per-class logit bias to correct production drift on neutral webcam faces
- **Face detector**: YOLO11 validated out of the box, fine-tuned on WiderFace where domain performance required it
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

Infrastructure is defined in Terraform (Artifact Registry, Cloud Run, GCS, Secret Manager) and deployed to GCP Cloud Run in `us-central1`. CI/CD runs on GitHub Actions — every push to `main` builds the backend Docker image, pushes it to Artifact Registry, and rolls a new Cloud Run revision. The frontend is built with Vite and deployed to Vercel. The API is CORS-restricted and rate-limited via slowapi at the application edge.

---

## Author

**Chirag Dahiya** — [GitHub](https://github.com/ChiragandAI) · [LinkedIn](https://www.linkedin.com/in/chiragdahiya)
