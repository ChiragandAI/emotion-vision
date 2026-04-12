# Deployment Guide

## Dockerized local run

```bash
docker compose up --build
```

Services:

- Frontend: `http://localhost:8080`
- Backend API: `http://localhost:8000`

## Environment notes

- Frontend uses `VITE_API_BASE_URL` at build time.
- Backend uses `INFERENCE_MODE`, defaulting to `local` in the Docker setup.
- Backend CORS can be controlled with `ALLOWED_ORIGINS` as a comma-separated list.
- Model weights are expected under `models/`.
- Generated annotated videos are written to `outputs/videos/`.

## Recommended cloud split

### Best practical option

- Frontend: Vercel
- Backend: Render or Google Cloud Run
- Storage for generated outputs: cloud object storage later if traffic grows

This project is a good fit for a split deployment because:

- the frontend is a static Vite app
- the backend is a Python inference API
- the backend may later need more CPU/GPU flexibility than the frontend

## Platform comparison

### Vercel

Best for:

- frontend only
- fast static deployment
- preview deployments

Not ideal for:

- heavy Python ML inference backend

### Render

Best for:

- easiest full-stack deployment path
- Docker-based backend deployment
- small portfolio backend

Tradeoff:

- cold starts and CPU limits are not ideal for heavier inference loads

### Google Cloud Run

Best for:

- containerized backend
- good scaling behavior
- cleaner production path than hobby platforms

Tradeoff:

- slightly more setup than Render

### AWS

Best for:

- maximum flexibility
- long-term production architecture

Tradeoff:

- overkill for a portfolio MVP unless you already know the AWS stack well

### Azure

Best for:

- enterprise ecosystems

Tradeoff:

- not the simplest first deployment path for this project

### Supabase

Best for:

- auth, database, storage

Not ideal as the main hosting platform for this ML inference app by itself.

## My recommendation

For this project, I would choose:

1. Frontend on Vercel
2. Backend on Render first, or Cloud Run if you want a stronger production story
3. Move generated video outputs to cloud storage later if needed

That gives you:

- the easiest public portfolio deployment
- strong frontend UX
- a backend that can still run your Dockerized FastAPI service

## Later production upgrade path

If you want a stronger production/cloud story later:

1. keep frontend on Vercel
2. move backend container to Google Cloud Run
3. store outputs in Google Cloud Storage
4. move model serving to GPU-backed infrastructure only if real-time traffic grows
