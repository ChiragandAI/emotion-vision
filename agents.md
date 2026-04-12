# Agents

## Vision

Build a high-quality facial emotion recognition system that works on images, videos, and live streams. The system should first detect faces and then classify the emotion of each detected face with strong accuracy, stable real-time performance, and a clean path to fine-tuning and deployment.

The main purpose of this project is to showcase practical fine-tuning knowledge, not just model consumption.

## Product Goal

Create a production-ready pipeline that:

- accepts image, video, and webcam/live-stream input
- detects one or more faces in each frame
- classifies the emotion of every detected face
- overlays results in real time
- supports training, fine-tuning, evaluation, and export for deployment
- ships as a public-facing portfolio website on the internet
- demonstrates that both the detector and the classifier were fine-tuned as part of the project

## Primary Portfolio Objective

This project should explicitly demonstrate:

- optional domain-specific fine-tuning of a YOLO-based face detector when needed
- fine-tuning a CNN-based emotion classifier
- comparing baseline versus fine-tuned performance
- turning trained models into a deployable product
- presenting the full workflow as a portfolio-quality case study

## Application Architecture

This project is not only a model pipeline. It is a full-stack product.

### Frontend

- Build the user-facing interface in React.
- The React app should provide:
  - homepage and product overview
  - image upload workflow
  - video upload workflow
  - webcam or live-stream demo
  - result visualization with boxes, labels, and confidence
  - project explanation for portfolio presentation
  - model and stack overview
  - contact or profile links for portfolio credibility

### Backend

- Build the backend in FastAPI.
- The FastAPI service should provide:
  - health endpoints
  - image inference endpoints
  - video inference endpoints
  - webcam or stream session support where practical
  - model management and inference routing
  - async job handling for longer video processing
  - file upload handling
  - result serialization and response formatting

### Portfolio Website Requirement

The final result should work as a polished portfolio-grade website that can be deployed publicly and demonstrated to recruiters, clients, or collaborators.

It should include:

- a clean landing page
- a working interactive demo
- clear explanation of the AI pipeline
- stack and architecture summary
- performance notes and limitations
- screenshots or recorded sample outputs
- deployment-ready frontend and backend separation
- production-safe API configuration
- error handling and fallback states
- responsive design for desktop and mobile

## Deployment Modes

Support both of the following inference strategies.

### Mode 1: External inference API

- Start by integrating API calls to the company or provider offering inference APIs.
- The backend should be able to send frames or files to an external inference service and return normalized predictions to the React frontend.
- This is the fastest way to get an online demo working if hosted model serving is not ready.

### Mode 2: Self-hosted model inference

- If model weights are small enough and latency/cost are acceptable, download and host the models directly.
- Self-hosted inference can run:
  - on the local development machine
  - on a GPU-enabled cloud VM
  - on Google Cloud Platform
  - on another cloud provider with GPU support
- The backend should be designed so the inference layer can switch between external API mode and self-hosted mode with minimal frontend changes.

### Preferred implementation order

1. validate out-of-the-box YOLO face detection first
2. fine-tune YOLO only if domain performance is not good enough
3. fine-tune the emotion classifier
4. export and validate trained weights
5. self-host the fine-tuned models when feasible
6. use provider API inference only as a fallback when deployment limits make self-hosting impractical

## Recommended System Design

### Stage 1: Face Detection

- Use a YOLO-based face detector.
- Preferred starting point: Ultralytics YOLO11.
- Practical recommendation:
  - start with a small or medium YOLO11 variant for real-time inference
  - use the detector out of the box first
  - fine-tune only if the target domain has missed detections, occlusion issues, camera-angle bias, or low-light failure cases

### Stage 2: Emotion Classification

- Use a CNN classifier on cropped face regions.
- Preferred starting backbone choices:
  - `EfficientNet-B0/B2` for strong accuracy-to-speed tradeoff
  - `ResNet18/ResNet34` for a stable and well-understood baseline
- Best practical path:
  - baseline with `ResNet18`
  - improved model with `EfficientNet-B2`
  - optionally compare against a lightweight ViT later if the CNN baseline plateaus

### Stage 3: Temporal Stability for Video and Streams

- Add prediction smoothing across adjacent frames.
- Use one or more of:
  - moving average over class probabilities
  - exponential smoothing
  - face tracking with persistent IDs
- This reduces flicker and makes stream output look much more reliable.

### Stage 4: Web Product Layer

- React frontend for uploads, live demo, and portfolio presentation
- FastAPI backend for orchestration, inference, file handling, and result delivery
- storage for uploaded media and generated outputs
- deployment configuration for public hosting
- observability, logging, and error reporting

## Target Emotion Labels

Support a clear canonical class set first, then expand only if the data supports it.

### Recommended base classes

- happy
- sad
- angry
- surprised
- fearful
- disgusted
- neutral

### Extended classes

- frustrated
- annoyed
- confused
- tired

Note: `frustrated` and `annoyed` are useful product labels, but they are harder to learn reliably because many public datasets focus on the seven basic emotions. If needed, these should be introduced through additional fine-tuning or custom labeling.

## Best-Practice Dataset Strategy

Use separate datasets for detection and emotion recognition.

### Face detection datasets

- WiderFace for robust face localization across scale and crowd density
- YOLO-format custom face dataset if you need domain-specific data such as classroom, office, CCTV, or webcam angles

### Emotion classification datasets

- FER2013 as a baseline starter dataset
- RAF-DB for stronger real-world facial expression quality
- AffectNet if available for broader coverage and better generalization
- CK+ only as a secondary or sanity-check dataset, not as the main production dataset

### Best combination

For a strong build:

1. pretrain or initialize the detector on a face dataset such as WiderFace
2. train the emotion classifier on RAF-DB or AffectNet
3. use FER2013 for additional benchmarking or supplementary training
4. collect a small custom validation set from the actual target environment

## Fine-Tuning Workflow Environment

Fine-tuning should be done in notebook-based environments that are practical for GPU access and easy to present in a portfolio.

### Preferred training environments

- Google Colab
- Kaggle Notebooks

### Why these environments

- they make GPU-backed experimentation more accessible
- they are convenient for iterative training and evaluation
- they are easy to showcase as part of a portfolio case study
- they allow saving notebooks, metrics, and exported weights as project artifacts

### Expected notebook deliverables

- face detector fine-tuning notebook
- emotion classifier fine-tuning notebook
- evaluation notebook with baseline-versus-fine-tuned comparisons
- export notebook or section for model artifact packaging

## Input Modes

The system must support the following:

### 1. Image mode

- detect all faces in the image
- crop each face
- classify each crop
- return annotated image and structured predictions

### 2. Video mode

- process frames at a configurable interval
- track faces frame to frame when possible
- smooth predictions for temporal consistency
- export annotated video if needed

### 3. Live-stream mode

- capture frames from webcam, RTSP, or browser stream
- run low-latency inference
- maintain face identity and stable emotion predictions
- display real-time overlays and optionally log results

### 4. Website demo mode

- allow browser-based upload and inference through React
- support webcam capture from the browser
- send media to FastAPI endpoints
- show processed outputs and structured prediction summaries
- degrade gracefully when live inference is unavailable

## End-to-End Pipeline

1. Receive image, video, or live stream.
2. Preprocess frame.
3. Run YOLO face detection.
4. Filter detections by confidence threshold.
5. Expand face box slightly to preserve facial context.
6. Crop and resize detected face.
7. Normalize face image for classifier input.
8. Run emotion classifier.
9. Apply temporal smoothing if input is video or live stream.
10. Draw bounding boxes, class labels, and confidence scores.
11. Return predictions and optionally save outputs.
12. Expose outputs through FastAPI responses and React UI rendering.

## Full-Stack Technical Plan

### React frontend responsibilities

- file upload UI
- drag-and-drop image and video support
- webcam capture UI
- inference progress indicators
- annotated output preview
- result cards and confidence summaries
- portfolio sections such as project story, model details, and architecture diagrams

### FastAPI backend responsibilities

- receive uploads from the React client
- validate file types and file sizes
- run or route inference
- manage sync image inference and async video inference
- expose JSON results and processed media URLs
- support CORS, environment-based configuration, and production deployment

### Supporting services

- object storage for media and output artifacts when deployed
- job queue for longer-running video tasks if needed
- model registry or model path configuration
- monitoring and logging

## Inference Integration Strategy

### External API path

The backend should define an inference client abstraction that can call a third-party or company-provided API.

Capabilities:

- send image or frame payloads
- receive bounding boxes and emotion predictions
- normalize provider responses into the app's internal schema
- handle retries, timeouts, auth headers, and rate limits

### Self-hosted path

The backend should also define a local inference adapter for downloaded model weights.

Capabilities:

- load YOLO face detector weights
- load emotion classifier weights
- run direct inference in Python
- support later export to ONNX or TensorRT

### Architecture rule

- The React app should not care whether inference comes from an external provider API or a self-hosted model.
- FastAPI should be the single integration boundary for inference.

## Training Plan

### Phase 1: Baseline

- use a pretrained YOLO11 model for face detection and validate it out of the box
- train `ResNet18` on the primary emotion dataset
- evaluate image inference quality on held-out validation data
- record baseline metrics before fine-tuning

### Phase 2: Accuracy Upgrade

- switch classifier to `EfficientNet-B2`
- improve preprocessing and augmentation
- address class imbalance
- add label smoothing and focal loss experiments
- fine-tune the CNN classifier in Colab or Kaggle
- fine-tune the YOLO detector in Colab or Kaggle only if baseline face detection is not sufficient

### Phase 3: Video Optimization

- add face tracking
- add temporal smoothing
- benchmark FPS, latency, and stability on webcam input

### Phase 4: Production Hardening

- collect domain-specific samples
- fine-tune on in-domain data
- export models to ONNX or TensorRT if needed
- package inference into app or service

### Phase 5: Web deployment

- build React UI for public demo
- expose FastAPI endpoints for browser use
- add deployment configuration for frontend and backend
- configure storage, environment variables, and domain setup
- optimize latency and reliability for public traffic

### Phase 6: Portfolio packaging

- prepare baseline-versus-fine-tuned comparisons
- present notebook outputs and training artifacts
- document dataset choices, training decisions, and deployment tradeoffs

## Fine-Tuning Guidance

### Fine-tuning YOLO

Fine-tune the detector when:

- the input domain differs from common face datasets
- faces are small, partially occluded, rotated, or low-light
- your camera angle is fixed and domain-specific
- out-of-the-box YOLO11 face detection is not reliable enough in the real deployment environment

Key metrics:

- mAP@50
- recall
- latency per frame
- baseline versus fine-tuned comparison

### Fine-tuning the emotion classifier

Fine-tune the classifier when:

- emotion accuracy is weak on real users
- confusion is high between similar expressions
- the target classes include `frustrated` or `annoyed`

Key metrics:

- accuracy
- macro F1-score
- confusion matrix
- per-class recall

### Fine-tuning requirement

For this project, fine-tuning is a required part of the portfolio story.

At minimum:

- fine-tune one CNN emotion classifier
- save trained checkpoints
- document the training setup and evaluation results

YOLO fine-tuning is optional and should be done only if the out-of-the-box detector is not good enough for the target domain.

## Preprocessing Recommendations

### Detection preprocessing

- resize images to a fixed YOLO input size
- preserve aspect ratio
- use confidence and IoU thresholds tuned on validation data

### Face crop preprocessing

- slightly pad bounding boxes around the face
- resize to classifier input size such as `224x224`
- normalize with the classifier backbone's expected statistics
- optionally align faces if rotation is a frequent issue

## Augmentation Strategy

Use moderate augmentation to improve generalization without destroying emotional cues.

Recommended augmentations:

- random horizontal flip
- brightness and contrast jitter
- mild blur
- random crop with face preserved
- small rotation
- random occlusion or cutout in moderation

Avoid overly aggressive transformations that distort expressions.

## Model Selection Recommendation

If the goal is one of the best balanced versions of this system, use:

- face detector: a recent Ultralytics YOLO model fine-tuned for face detection
- emotion classifier: `EfficientNet-B2`
- video stability: face tracking plus exponential smoothing

If the goal is fastest prototyping, use:

- face detector: YOLO small variant
- emotion classifier: `ResNet18`

## GPU Compute Guidance

### Training

- GPU compute is strongly recommended for model training and fine-tuning.
- Training YOLO and the emotion classifier on CPU is possible in theory, but it will be slow and impractical for serious experimentation.
- If fine-tuning is part of the plan, assume GPU is needed.
- Google Colab or Kaggle should be treated as the default training environment unless a better GPU resource is available.

### Inference

- GPU is not strictly required for basic image inference.
- CPU inference can be acceptable for:
  - single-image predictions
  - low-volume demo traffic
  - early local development
- GPU is recommended for:
  - real-time webcam inference
  - video processing at good speed
  - multiple concurrent users on a deployed website
  - larger detection or classification models

### Practical recommendation

- local development: CPU is enough for UI, API, and basic image testing
- training and serious benchmarking: use GPU
- public portfolio website:
  - self-hosted CPU inference may be enough for image uploads and low traffic if models are lightweight
  - real-time video or webcam inference will usually benefit from GPU-backed deployment
  - if free GPU hosting is not available, use provider API inference or limit live-demo expectations

## Evaluation Plan

### Offline evaluation

- face detection precision, recall, and mAP
- emotion classification accuracy and macro F1
- confusion matrix by class
- baseline versus fine-tuned checkpoint comparison

### Real-world evaluation

- FPS on webcam stream
- average inference latency
- stability of emotion label over time
- performance in low light and partial occlusion
- behavior with multiple faces in the frame

## Suggested Success Criteria

- accurate face detection across common real-world conditions
- emotion macro F1 strong enough to avoid obvious class collapse
- real-time webcam inference on a modern GPU
- stable predictions without heavy flicker
- clean failure behavior when confidence is low

## Confidence and Output Design

For each detected face, return:

- bounding box coordinates
- face detection confidence
- predicted emotion label
- emotion confidence
- tracked identity for video or stream mode if available

Use a confidence threshold to suppress weak or noisy emotion predictions. If confidence is too low, return `uncertain` instead of forcing an incorrect label.

## Recommended Repository Structure

```text
project/
  frontend/
    src/
    public/
    components/
    pages/
    hooks/
    services/
  backend/
    app/
      api/
      core/
      services/
      schemas/
      models/
      workers/
      utils/
  data/
    raw/
    processed/
    splits/
  models/
    detection/
    emotion/
    exported/
  notebooks/
    detection_finetuning.ipynb
    emotion_finetuning.ipynb
    evaluation.ipynb
  src/
    detection/
    emotion/
    tracking/
    inference/
    api/
    utils/
  configs/
    detection/
    emotion/
    inference/
    deployment/
  scripts/
    train_detection.py
    train_emotion.py
    evaluate.py
    infer_image.py
    infer_video.py
    infer_stream.py
  tests/
  outputs/
  docker/
  infra/
```

## Engineering Roadmap

### Milestone 1

- set up repo structure
- load pretrained detector
- train baseline emotion classifier
- support single-image inference
- define FastAPI backend structure
- define React frontend structure
- prepare Colab or Kaggle notebook workflow

### Milestone 2

- add video inference
- add result rendering
- benchmark accuracy and speed
- add image upload flow in React
- add FastAPI image inference endpoint
- fine-tune YOLO detector in Colab or Kaggle
- fine-tune CNN emotion classifier in Colab or Kaggle

### Milestone 3

- add face tracking and smoothing
- support webcam and RTSP stream
- improve deployment readiness
- add React webcam demo
- add API abstraction for external inference provider
- export fine-tuned model weights

### Milestone 4

- fine-tune on custom target-domain data
- export optimized models
- package into app, API, or edge deployment
- add production deployment configuration
- make the project presentable as a public portfolio site
- deploy to Google Cloud Platform or another free-tier-friendly cloud where possible

## Risks and Mitigations

### Risk: weak labels for advanced emotions

- mitigation: start with seven core emotions
- mitigation: add `frustrated` and `annoyed` only with strong custom data

### Risk: video flicker

- mitigation: add tracking and temporal smoothing

### Risk: poor performance in real lighting conditions

- mitigation: collect target-domain samples and fine-tune

### Risk: multiple faces or partial occlusion

- mitigation: improve detector training and use more realistic validation data

## Recommended Final Stack

If building the strongest practical first version, use this stack:

- frontend: React
- backend: FastAPI
- detector: YOLO11 face detector, fine-tuned only if required by the target domain
- classifier: `EfficientNet-B2`
- tracking: ByteTrack or a lightweight tracker
- smoothing: exponential moving average on logits or probabilities
- deployment: Python inference first, ONNX export later
- training environment: Google Colab or Kaggle
- hosting target: Google Cloud Platform or another free-tier-friendly cloud where possible
- inference serving: self-hosted fine-tuned models when practical, provider API fallback when deployment constraints require it

## Cloud Deployment Strategy

The deployment plan should prioritize platforms that are free, low-cost, or provide a usable free tier.

### Preferred targets

- Google Cloud Platform
- other cloud platforms with a meaningful free tier for static hosting, backend hosting, or low-volume inference

### Practical deployment split

- frontend can usually be deployed on a static hosting platform or free web tier
- FastAPI backend can be deployed on a small free-tier service if inference load is light
- model inference can be:
  - self-hosted on CPU for low-traffic image demos
  - routed to a provider API
  - moved to GPU-backed infrastructure later if the free tier is insufficient

## Deliverable Definition

The final system should:

- provide a React-based public website
- expose a FastAPI backend
- run on images, videos, and live streams
- detect all visible faces
- classify each face emotion reliably
- remain stable over time in video
- support retraining and fine-tuning
- be structured for future deployment as an app or API
- support either provider API inference or self-hosted model inference
- be credible as a portfolio project on the public internet
- clearly demonstrate fine-tuning work performed in Colab or Kaggle notebooks
- show that the deployed product is based on fine-tuned models rather than only off-the-shelf inference

The most important fine-tuning proof can come from the emotion classifier even if YOLO11 is kept out of the box.

## Notes

- As of March 31, 2026, I am treating a current Ultralytics YOLO-family model as the recommended starting point and pairing it with a fine-tuned face-detection workflow rather than assuming an off-the-shelf generic detector is enough.
- The highest-value improvement beyond the baseline will usually come from better emotion data and temporal smoothing, not only from changing backbone size.
- The best early delivery path is usually React + FastAPI + external inference API integration first, then optional migration to self-hosted weights when performance, cost, and ops tradeoffs are favorable.
- For this project specifically, the portfolio value comes first from demonstrating fine-tuning skill and then from demonstrating deployment skill.
- Fine-tuning the emotion model is the core requirement. Fine-tuning YOLO11 is a conditional enhancement, not a mandatory step.
