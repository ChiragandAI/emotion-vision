# YOLO Face Emotion Recognition

Baseline scaffold for a face detection plus emotion classification system that supports images, videos, and live streams.

## What is included

- YOLO-oriented face detector wrapper
- PyTorch emotion classifier baseline
- end-to-end inference pipeline
- temporal smoothing for video and stream mode
- starter configs for training and inference
- CLI scripts for image, video, webcam, and training workflows

## Suggested setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick start

### Prototype mode

Use this mode if you want the frontend and backend to work right now before real model weights are available.

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

The frontend will call the backend in `mock` mode and return stable demo predictions from the API.

## Docker quick start

```bash
docker compose up --build
```

Then open:

- frontend: `http://localhost:8080`
- backend: `http://localhost:8000`

### Image inference

```bash
python scripts/infer_image.py \
  --input path/to/image.jpg \
  --output outputs/image_result.jpg
```

### Video inference

```bash
python scripts/infer_video.py \
  --input path/to/video.mp4 \
  --output outputs/video_result.mp4
```

### Webcam inference

```bash
python scripts/infer_stream.py \
  --source 0
```

## Notes

- Detection defaults to a lightweight OpenCV face detector if YOLO weights are not available yet.
- Emotion classification defaults to an untrained PyTorch baseline unless you provide trained weights.
- This repo is scaffolded for fast iteration and later fine-tuning, not as a finished model release.
