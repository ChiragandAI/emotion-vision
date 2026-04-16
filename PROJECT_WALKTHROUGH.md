# Emotion Vision — Complete Project Walkthrough

A line-by-line, section-by-section explanation of how this project works, why every piece exists, and what happens when a request hits the system. Read this top to bottom alongside the source code.

---

## 1. What this project actually is

**Emotion Vision** is a real-time multi-face emotion recognition system. You feed it an image, a video, or a webcam frame, and it returns:

- A bounding box around every face it finds
- The dominant emotion for each face (happy, sad, angry, fear, surprise, disgust, neutral)
- A confidence score per emotion
- A stable track ID per face across video frames (so "person #3" stays person #3 as they move)

Under the hood it is **two deep-learning models chained together**:

1. **YOLO (face detector)** — finds *where* faces are. Outputs a list of bounding boxes with confidence scores.
2. **ResNet-18 (emotion classifier)** — takes each cropped face and outputs a 7-way probability distribution over emotions. 

That chain is the "pipeline." Everything else in this repo — the FastAPI backend, React frontend, Docker images, Terraform infra, GitHub Actions CI/CD — exists to expose that pipeline as a deployed product.

---

## 2. Why it is structured the way it is

A common mistake is to put ML code and web code in the same folder. This repo separates them deliberately:

```
yolo/
├── src/              ← pure ML code. Models, pipeline, training. No web framework.
├── backend/          ← FastAPI server. Imports from src/. No model code of its own.
├── frontend/         ← React + Vite UI. Talks to backend over HTTP.
├── configs/          ← YAML hyperparams. Kept separate so you can change them
│                       without editing code.
├── scripts/          ← CLI entry points: train_detection.py, train_emotion.py, etc.
├── models/           ← Trained weights (yolo_face.pt, emotion_resnet18.pt).
├── docker/           ← Dockerfiles for backend + frontend.
├── infra/terraform/  ← Infra-as-code for GCP (Cloud Run, Artifact Registry, GCS,
│                       Secret Manager).
├── .github/workflows ← CI/CD pipelines.
└── tests/            ← Pytest test suite.
```

**Why this separation matters:** `src/` is importable as a library. Tomorrow you could delete the FastAPI backend and wrap the same `src/` code in a different interface (gRPC, Celery worker, batch job) without touching the models. That decoupling is what makes it an "MLOps" project rather than a one-off script.

---

## 3. The ML core — `src/`

### 3.1 `src/detection/face_detector.py`

Wraps **Ultralytics YOLO**. The key points:

- Loads `models/detection/yolo_face.pt` (weights fine-tuned on WiderFace).
- `detect(frame)` returns a list of `Detection` objects with `box=(x1,y1,x2,y2)` and `confidence`.
- `crop_face(frame, detection)` slices the numpy array to extract just that face's pixels. This crop is what gets fed into the emotion classifier downstream.
- Uses a **confidence threshold** (from `configs/detection/base.yaml`) to discard weak detections — YOLO emits hundreds of candidate boxes per frame; most are garbage.

**Why YOLO and not something else?** YOLO is single-shot (one forward pass = all faces), GPU-friendly, and has excellent pretrained checkpoints. A two-stage detector like Faster R-CNN is more accurate but 5–10× slower — wrong trade-off for real-time.

### 3.2 `src/emotion/classifier.py`

Wraps a **ResNet-18** fine-tuned on FER-style data (7 emotion classes).

- Input: a cropped face image (any size).
- Preprocessing: resize to 224×224, normalize with ImageNet mean/std, convert to a PyTorch tensor.
- Output: a `Prediction` object with `label` (string), `confidence` (float), and the full `probabilities` vector (list of 7 floats summing to 1).

**Why ResNet-18 and not a bigger model?** Emotion recognition on a 224×224 crop is a low-data, low-variance task. ResNet-18 has 11M params — big enough to learn but small enough to run on CPU in ~30ms per face. Moving to ResNet-50 would be ~2× slower for <1 point of accuracy gain.

**Why a separate model instead of making YOLO do both?** YOLO can technically be trained for joint detection+classification, but:
1. The two tasks have very different data distributions (face crops vs. full scenes).
2. You lose the ability to swap one without retraining the other.
3. Emotion datasets are tiny compared to detection datasets; joint training would overfit the emotion head.

### 3.3 `src/tracking/smoother.py` — `SimpleTracker`

Faces jitter frame-to-frame in video. Raw per-frame classification would flicker between "happy" and "neutral" even when the person's expression hasn't changed. The tracker fixes this.

- **IoU matching**: box in frame *t+1* is matched to the nearest box in frame *t* by intersection-over-union. That's how "person #3 stays person #3."
- **Exponential smoothing** over the *probability vector* (not just the label):
  `smoothed_probs = α × prev_probs + (1-α) × new_probs`
  with α ≈ 0.65. This blends the current frame's prediction with the running history.
- **max_missing**: if a track isn't matched for 10 frames (~0.4s at 24 fps), it's dropped.

**Why smooth probabilities instead of labels?** Labels are discrete — you can't average "happy" and "sad." Probabilities are continuous, so you get smooth transitions and robust uncertainty.

### 3.4 `src/inference/pipeline.py` — `EmotionPipeline`

This is the glue. `predict_frame(frame, use_tracking)`:

1. Calls `detector.detect(frame)` → list of boxes.
2. For each box, crops the face and calls `classifier.predict(face)` → probabilities.
3. Applies the "uncertain" threshold (line 49): if confidence < 0.45, label it `"uncertain"` instead of guessing. This is important for UX — better to show "uncertain" than confidently wrong.
4. If `use_tracking=True` (video mode), runs the tracker over all boxes in the frame.
5. Returns a list of `FaceResult` dataclasses.

`frame_to_dict(results)` serializes those dataclasses to JSON-compatible dicts — this is the exact shape the backend sends to the frontend.

### 3.5 `src/utils/modeling.py` — `build_pipeline()`

The one function the backend actually calls. Reads the three config YAMLs, instantiates the detector, classifier, and tracker with those params, and returns a ready `EmotionPipeline`. This is the **dependency injection root** — every hyperparameter is configurable from YAML, nothing is hardcoded deep in the stack.

---

## 4. The backend — `backend/app/`

FastAPI server. Purpose: expose the pipeline as HTTP endpoints, handle file uploads, manage model lifecycle.

### 4.1 `backend/app/main.py`

The FastAPI app, with two important patterns:

**Lifespan context (startup hook):**
```python
@asynccontextmanager
async def lifespan(_app):
    service.warmup()              # eagerly load weights + run one dummy inference
    _app.state.ready = True
    yield
```
This forces model weights to load *before* the server accepts traffic. Without this, the first real request would take 10+ seconds (cold load), and health checks would lie about readiness.

**Two health endpoints:**
- `/health` — "am I alive?" (liveness probe). Returns 200 immediately.
- `/health/ready` — "can I serve traffic?" (readiness probe). Returns 503 until `warmup()` finishes.

Cloud Run's startup probe hits `/health/ready`; it won't route traffic to a new revision until that returns 200. That's how zero-downtime deploys work.

### 4.2 `backend/app/core/config.py`

Pydantic settings class — reads env vars, provides typed defaults.

Critical piece at the bottom:
```python
if settings.environment == "production" and settings.inference_mode == "mock":
    raise RuntimeError("Refusing to start: INFERENCE_MODE=mock in production.")
```
This is a **fail-fast guard**. If a bad deploy tries to ship the mock service to prod, the container crashes at import time, the deploy fails, and traffic stays on the previous revision. Defense in depth — even if Terraform, CI, and Secret Manager all misconfigure together, this still catches it.

### 4.3 `backend/app/api/routes.py`

Three endpoints:
- `POST /api/v1/infer/image` — accepts an image upload, returns detected faces + emotions.
- `POST /api/v1/infer/video` — accepts a video, runs inference frame-by-frame, returns annotated video URL + sample frames.
- `GET /api/v1/demo` — returns the current mode/environment for the UI to display.

All the actual logic is delegated to `InferenceService`.

### 4.4 `backend/app/services/inference_service.py`

The **service layer**. This is where mode switching happens:

- `mode == "mock"` — returns fake boxes. Used locally without model weights.
- `mode == "local"` — runs the actual pipeline in-process (the normal path).
- `mode == "provider"` — forwards the request to an external inference API (currently a stub in `provider_client.py`).

Why three modes? So you can develop the UI without a GPU (mock), test the real pipeline locally (local), or offload inference to a dedicated GPU service in prod (provider). All three swap without touching route code.

**Video inference** (`infer_video_bytes`):
- Writes the upload to a temp file (cv2 can't read raw bytes, only files).
- Opens it with `cv2.VideoCapture`, reads frame-by-frame.
- Runs the pipeline on every frame with `use_tracking=True` (this is why the tracker matters here).
- Annotates each frame (draws boxes + labels) and writes to an output MP4 via `cv2.VideoWriter`.
- Samples every 15th frame (max 8) to send back as base64 thumbnails for the UI preview.
- Returns `annotated_video_url` pointing to `/outputs/videos/{name}.mp4`.

`_cleanup_generated_videos` sweeps old output MP4s on every request — a poor-man's TTL so the container disk doesn't fill up.

### 4.5 `backend/app/services/model_loader.py`

At startup, if `models/detection/yolo_face.pt` isn't present on disk, this downloads it from GCS (`gs://<bucket>/yolo_face.pt`). That's how the Cloud Run container — which ships empty — gets its weights at boot. GCS has **object versioning enabled** (via Terraform), so if a bad weight ever gets uploaded, you can roll back to the previous blob.

### 4.6 `backend/app/services/provider_client.py`

Thin HTTP client for the "provider" mode. If you ever want to offload inference to something like Replicate, Modal, or a dedicated GPU service, this is where that logic goes. Currently unused in production.

---

## 5. The frontend — `frontend/`

React + Vite. No TypeScript. Minimal.

### 5.1 `frontend/src/services/api.js`

Four functions wrapping the backend HTTP API:
- `getHealth()` → `GET /health`
- `getDemoInfo()` → `GET /api/v1/demo`
- `inferImage(file)` → `POST /api/v1/infer/image` with multipart/form-data
- `inferVideo(file)` → `POST /api/v1/infer/video`

The base URL comes from `VITE_API_BASE_URL` (Vercel env var) — that's how prod frontend → prod backend wiring works without hardcoding.

### 5.2 `frontend/src/components/DemoPanel.jsx`

The UI. Three tabs:
- **Image upload** — file input + drag/drop. Renders result JSON + annotated image.
- **Video upload** — same, plus video player for the annotated output.
- **Webcam** — uses `navigator.mediaDevices.getUserMedia`, captures a frame via `<canvas>.toBlob()`, sends it to `/infer/image`.

### 5.3 `frontend/src/styles.css`

Styling. Key rule: `.image-preview { object-fit: contain; }` — this is why images now display full-size in correct aspect ratio instead of being cropped to fit a 320px box.

---

## 6. Training — `scripts/`

These are the scripts that *produced* the weights in `models/`. They don't run in production, but they're important for the story.

### 6.1 `scripts/train_detection.py`

Fine-tunes YOLO on the **WiderFace** dataset (a face-specific detection benchmark). Reads hyperparams from `configs/detection/base.yaml`, calls the Ultralytics `YOLO.train()` API, saves the resulting `.pt` to `models/detection/`.

### 6.2 `scripts/train_emotion.py`

Fine-tunes ResNet-18 on an FER-style dataset. Standard PyTorch loop: dataloader → forward → cross-entropy loss → Adam step → validation per epoch → save best checkpoint. Reads hyperparams from `configs/emotion/base.yaml`.

### 6.3 `scripts/convert_widerface_to_yolo.py`

Utility: WiderFace annotations are in their own format, YOLO wants `class x_center y_center w h` (normalized). This converts them.

### 6.4 `scripts/evaluate.py`

Runs the trained models against a held-out test set, prints mAP for detection and accuracy/F1 for emotion classification. Used during model selection.

### 6.5 `scripts/infer_image.py`, `infer_video.py`, `infer_stream.py`

CLI counterparts to the HTTP API. They call the same `build_pipeline()` function as the backend — so you can run the pipeline from the terminal without starting a server. Useful for debugging.

---

## 7. Docker — `docker/`

### 7.1 `docker/backend.Dockerfile`

Multi-stage pattern:
1. Base image: `python:3.11-slim`.
2. Install system deps (libgl for opencv).
3. `pip install -r requirements.txt` — layer-cached, so code changes don't reinstall torch.
4. Copy `src/`, `backend/`, `configs/` into the image.
5. `CMD` runs `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`.

**Why no model weights in the image?** Weights are ~200MB. Baking them in would bloat the image, slow pulls, and couple the image to a specific model version. Instead, weights are downloaded from GCS at startup — so upgrading a model is just `gsutil cp` + Cloud Run restart, no rebuild.

### 7.2 `docker/frontend.Dockerfile` + `frontend.nginx.conf`

Two-stage build: Node image runs `vite build`, then copies `dist/` into an nginx image. Nginx serves the static files. Currently **not used** in prod (we deploy the frontend to Vercel), but kept for self-hosted deploys.

---

## 8. Infra — `infra/terraform/`

This is the **MLOps heart** of the project. Everything on GCP is declared here as code.

### 8.1 `main.tf`

Root module. Declares the Google provider, pins the project ID and region, then composes four child modules:

### 8.2 `modules/artifact-registry/`

Creates a private Docker registry on GCP. This is where CI pushes the backend image. Cloud Run pulls from here. Keeps images private without needing Docker Hub auth.

### 8.3 `modules/gcs/`

Creates the model weights bucket. Critical setting:
```hcl
versioning { enabled = true }
```
Every upload creates a new generation; old generations aren't deleted. Safety net for "I just uploaded bad weights" mistakes.

### 8.4 `modules/secret-manager/`

Manages `INFERENCE_MODE` as a secret (even though it's not technically secret — the pattern matters). Terraform owns the secret value (`secret_data = var.inference_mode`), so changing mode is a one-line Terraform edit + apply — not a Cloud Run console click someone forgets to document.

Outputs `inference_mode_version` so the Cloud Run module can **pin to the exact version** — not "latest." This means a Terraform plan always shows you which secret version is deployed; no "works on Monday, breaks on Tuesday" surprises.

### 8.5 `modules/cloud-run/`

The actual compute. Key features:
- Env var `INFERENCE_MODE` wired to the pinned secret version.
- Env var `ENVIRONMENT=production` hardcoded — this is what trips the fail-fast guard in `config.py`.
- **Startup probe** on `/health/ready` — no traffic until warmup finishes.
- **Liveness probe** on `/health` — restarts the container if it stops responding.
- CPU+memory set via variables (defaults: 2 vCPU, 4GB — enough for CPU inference on a single face).

---

## 9. CI/CD — `.github/workflows/`

Three workflows, each with a job.

### 9.1 `ci.yml` — runs on every PR

- `ruff` lint
- `mypy` type check
- `pytest` backend tests (includes the startup-guard tests)
- `vite build` on frontend (catches compile errors)

Nothing deploys. This is the gate — if this fails, merge is blocked.

### 9.2 `deploy-staging.yml` — runs on push to `main`

1. Authenticates to GCP via Workload Identity Federation (no long-lived JSON keys).
2. Builds the backend Docker image, tags it with the commit SHA.
3. Pushes to Artifact Registry.
4. Runs `gcloud run deploy` pointing Cloud Run at the new image.
5. Cloud Run spins up the new revision, waits for readiness, then atomically shifts traffic.

Commit SHA in the image tag means **every deploy is traceable**: you can always look at prod and say "this is commit `af656ee`."

### 9.3 `deploy-prod.yml` — runs on manual trigger

Same as staging but with canary rollout (5% → 25% → 100%) and requires manual approval at each step. Currently prod and staging are the same service since this is a solo project, but the pattern is in place.

---

## 10. What happens when you hit "Analyze" on an image

End-to-end request trace, because this makes everything concrete:

1. **Browser** — User picks `cat.jpg`. `DemoPanel.jsx` calls `inferImage(file)`.
2. **api.js** — Creates `FormData`, POSTs to `https://<vercel-url>/...` → actually goes to `VITE_API_BASE_URL` = `https://emotion-vision-backend-<hash>.run.app/api/v1/infer/image`.
3. **Cloud Run front door** — Routes to the active revision's container.
4. **FastAPI** — `routes.py` receives the request, reads `file.read()` → bytes.
5. **InferenceService.infer_image_bytes** — in `local` mode:
   - `_decode_image` → `cv2.imdecode` → numpy array (H, W, 3).
   - `pipeline.predict_frame(frame, use_tracking=False)`.
6. **Pipeline**:
   - `YOLO` forward pass → list of detections.
   - For each: crop face → ResNet-18 forward pass → probs → label.
7. **Serialization** — `frame_to_dict` → list of dicts → FastAPI auto-JSONs it.
8. **Response** — ~200ms later, JSON hits the browser. `DemoPanel` renders boxes overlaid on the image + the probability table.

---

## 11. Fine-tuning — what actually happened

Pretrained YOLO is trained on 80 COCO classes (car, dog, person, ...). It's not great at faces specifically. **Fine-tuning** = take those pretrained weights, replace/extend the detection head, and keep training on WiderFace (a face-specific dataset). The early conv layers already know "what an edge looks like," so you only teach the later layers "what a face looks like." Converges in a few epochs instead of training from scratch (which would take days).

Same pattern for ResNet-18: start from ImageNet weights, replace the final 1000-way classification layer with a 7-way emotion head, train on FER data. The backbone already knows "what a face's eyes/mouth look like structurally"; we just teach the head to map those features to emotions.

That is the one-sentence version of why fine-tuning works: **reuse the general features, retrain the specific head.**

---

## 12. Why this is an MLOps project (not just ML)

ML projects stop at "the model works in a notebook." MLOps projects handle everything around that:

- **Reproducible environment** → Docker
- **Declarative infra** → Terraform
- **Automated testing + deployment** → GitHub Actions
- **Versioned model artifacts** → GCS object versioning
- **Config management** → Secret Manager, pinned versions
- **Observability** → health/readiness probes, Cloud Monitoring
- **Safe rollouts** → Cloud Run revisions + traffic shifting
- **Failsafe** → prod-mock guard

If tomorrow a teammate joins, they can clone the repo, run `terraform apply`, and have an identical stack up. That's the MLOps bar. The ML itself (YOLO + ResNet) is the easy part — half a day of training once you have the data. The hard part, and what this repo demonstrates, is turning that half-day into a production system that you can leave running unattended.

---

## 13. Live URLs

- **Frontend**: https://emotion-vision.vercel.app
- **Backend**: Cloud Run (auto-deployed from `main` via GitHub Actions)
- **Repo**: https://github.com/ChiragandAI/emotion-vision

---

## 14. How to read this repo for maximum understanding

Go in this order, with this doc open:

1. `src/inference/pipeline.py` — the ML heart, 110 lines.
2. `src/detection/face_detector.py` + `src/emotion/classifier.py` — the two models.
3. `src/tracking/smoother.py` — the one non-obvious algorithm.
4. `backend/app/main.py` + `backend/app/api/routes.py` — how HTTP meets ML.
5. `backend/app/services/inference_service.py` — the mode-switching layer.
6. `backend/app/core/config.py` — the fail-fast guard.
7. `infra/terraform/main.tf` and its modules — the infra story.
8. `.github/workflows/deploy-staging.yml` — the deploy story.
9. `scripts/train_*.py` — how the weights got there in the first place.

When something doesn't make sense in code, come back to the corresponding section here. Every non-obvious decision is explained above.
