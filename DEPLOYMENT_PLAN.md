# Industry-Standard MLOps Deployment Plan

## Project: Emotion Vision — YOLO Face Detection + Emotion Classification

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        USERS                                │
└───────────────────────────┬─────────────────────────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
    ┌───────────────┐              ┌─────────────────┐
    │   Vercel CDN  │              │  GCP Cloud CDN  │
    │  (Frontend)   │              │  (Media/Assets) │
    └───────┬───────┘              └────────┬────────┘
            │                              │
            ▼                              ▼
    ┌───────────────┐       ┌──────────────────────────┐
    │  React / Vite │       │   GCP Cloud Load Balancer│
    │  (Static SPA) │       │   + Cloud Armor (WAF)    │
    └───────────────┘       └────────────┬─────────────┘
                                         │
                            ┌────────────▼─────────────┐
                            │   GCP API Gateway        │
                            │   (Rate limiting, Auth,  │
                            │    Request routing)      │
                            └────────────┬─────────────┘
                                         │
                     ┌───────────────────┼──────────────────┐
                     ▼                   ▼                   ▼
            ┌────────────────┐  ┌──────────────┐  ┌─────────────────┐
            │  Cloud Run     │  │  Cloud Run   │  │  Cloud Run      │
            │  (Prod)        │  │  (Staging)   │  │  (Jobs - video) │
            │  FastAPI +     │  │  FastAPI +   │  │  Async video    │
            │  ML Inference  │  │  ML Inference│  │  processing     │
            └───────┬────────┘  └──────────────┘  └────────┬────────┘
                    │                                        │
            ┌───────┴────────────────────────────────┐      │
            ▼               ▼                ▼        │      ▼
    ┌──────────────┐ ┌────────────┐ ┌──────────────┐ │  ┌────────┐
    │  Supabase    │ │   Redis    │ │  GCS Buckets │ │  │  GCS   │
    │  PostgreSQL  │ │  (Upstash) │ │  (uploads +  │◄┘  │ Models │
    │  (job queue) │ │  (cache)   │ │   outputs)   │    └────────┘
    └──────────────┘ └────────────┘ └──────────────┘
```

---

## Full Stack — Tool Decisions and Reasoning

| Component | Tool | Why |
|-----------|------|-----|
| **Frontend hosting** | Vercel | Industry standard for React/Vite static apps. Edge CDN built-in. |
| **Backend hosting** | GCP Cloud Run | Serverless containers. Auto-scales to zero. What real companies use. |
| **Container registry** | GCP Artifact Registry | Native GCP integration. Stores versioned Docker images. |
| **IaC** | Terraform | Every resource defined in code, not clicked in console. Reproducible. |
| **CI/CD** | GitHub Actions | Automates lint → test → build → deploy on every push. |
| **Branching strategy** | Trunk-based development | Short-lived feature branches, PRs merged to main daily. |
| **Secrets** | GCP Secret Manager | No secrets in code or env files. IAM-scoped access per service account. |
| **Canary deployments** | Cloud Run traffic splitting | New model version gets 5% traffic, monitored, then promoted to 100%. |
| **Experiment tracking** | Weights & Biases (W&B) | Industry-standard ML experiment tracking. Free for open projects. |
| **Model registry** | W&B Model Registry | Version control for models. Staging → Production promotion gate. |
| **Monitoring** | Cloud Monitoring + Grafana | Infra metrics + ML-specific dashboards. Alerts on error rate and latency. |
| **ML drift detection** | Evidently AI | Detects when input distribution shifts and model degrades silently. |
| **Inference caching** | Redis via Upstash | Identical image hashes return cached result in <5ms. Free tier. |
| **Database** | Supabase PostgreSQL | Job queue for async video processing. Free tier. |
| **Media storage** | GCP Cloud Storage (GCS) | Uploads, processed outputs, model weights. Signed URLs for direct upload. |

---

## CI/CD Pipeline (GitHub Actions)

```
PR opened
    │
    ├── [parallel] Python lint + type check (ruff, mypy)
    ├── [parallel] Unit tests (pytest)
    └── [parallel] Frontend build check (vite build)
    │
    ▼ (all pass)
Docker build (multi-stage, production image)
    │
    ▼
Push to GCP Artifact Registry
  Tagged: sha-{commit}, branch-{name}, latest
    │
    ▼
Deploy to Cloud Run STAGING
    │
    ▼
Integration tests against staging URL
    ├── GET /health → 200
    ├── POST /api/v1/infer/image with test image
    ├── Assert latency < 800ms
    └── Assert emotion label in valid set {happy,sad,angry,surprised,fearful,disgusted,neutral}
    │
    ▼ (tests pass) → PR can merge to main
    │
    ▼ (merge to main triggers prod deploy)
Canary deployment to Cloud Run PROD
    ├── 5% traffic → new revision
    ├── Monitor 10 minutes (error rate, latency p95)
    ├── 25% traffic → monitor 10 minutes
    ├── 100% traffic if healthy
    └── Auto-rollback if error rate > 2%
    │
    ▼
Smoke tests on prod
Post deploy notification (webhook / Discord)
```

---

## Scaling Story (Small → Large User Base)

This is the answer to "how would you handle 10x traffic?" in system design interviews.

| Traffic Level | State | What handles it |
|---------------|-------|-----------------|
| **0 users** | Idle / night | Cloud Run scales to 0 instances. Cost = $0. |
| **1–50 req/min** | Normal portfolio traffic | 1 warm instance. Redis cache handles repeated uploads. |
| **50–500 req/min** | Viral / recruiter sharing | Cloud Run auto-scales to ~5 instances within 30 seconds. |
| **500–5000 req/min** | Real product traffic | Cloud Run scales to 100+ instances. API Gateway rate-limits abuse. CDN serves frontend globally. |
| **5000+ req/min** | Migrate path | Move ML inference to GKE with GPU nodes, HPA, horizontal sharding. Split inference and API layers. |

Cloud Run handles 1 to 500 req/min automatically with no configuration changes. This is the key advantage of serverless containers.

---

## Authentication Decision

### Does this project need auth?

**Short answer: Not traditional login auth. But yes to rate limiting and abuse protection.**

This is a public portfolio demo, not a multi-user SaaS product. There are no user accounts, no private data, no billing. Full OAuth2/JWT login would be incorrect here — it would add friction and reduce demo conversions.

### What you DO need (and why it counts as production-grade):

| Protection | Tool | Why |
|------------|------|-----|
| **Rate limiting** | API Gateway or Cloud Run request limits | Prevents one person from running 10,000 inferences and costing you money |
| **File size limits** | Already implemented in routes.py (8MB image, 120MB video) | Prevents payload attacks |
| **CORS lockdown** | Already implemented via ALLOWED_ORIGINS | Prevents other websites from calling your API |
| **Input validation** | Already implemented (content_type checks) | Prevents malformed payloads |
| **WAF (Web Application Firewall)** | GCP Cloud Armor | Blocks known attack patterns and bad IPs |

### The correct auth answer for an interview:

> "This is a public demo. Auth would reduce conversion on a portfolio site. Instead I rate-limit by IP at the API Gateway layer, validate all inputs, lock CORS to my frontend domain, and use Cloud Armor as a WAF. If this became a paid product, I'd add JWT-based auth with short-lived tokens and scope-limited service accounts for backend-to-backend calls."

This is exactly the right answer. Knowing WHEN to add auth is a sign of seniority.

---

## Deployment Readiness Assessment

### What is already in good shape

| Area | Status | Notes |
|------|--------|-------|
| Docker — backend | Ready | Multi-stage build, slim base image, system deps handled |
| Docker — frontend | Ready | Multi-stage Nginx build with build-arg for API URL |
| docker-compose | Ready | Works for local development and testing |
| FastAPI structure | Ready | Routes, schemas, services, config all separated |
| CORS config | Ready | Controlled via ALLOWED_ORIGINS env var |
| File size limits | Ready | Configurable via env vars |
| Inference modes | Ready | mock / local / provider switchable via INFERENCE_MODE |
| Env-based config | Ready | All settings driven by environment variables |
| Model weights | Present | yolo_face.pt and emotion_resnet18.pt exist in models/ |

### What needs to be built before deploying

| Gap | Priority | Work needed |
|-----|----------|-------------|
| Terraform IaC | High | Write Terraform for Cloud Run, Artifact Registry, Secret Manager, GCS |
| GitHub Actions pipeline | High | CI/CD workflow file (.github/workflows/) |
| GCP Secret Manager wiring | High | Move secrets out of env vars into Secret Manager |
| ALLOWED_ORIGINS for prod | High | Set to production Vercel URL, not localhost |
| Model weights in GCS | High | Move model files to GCS bucket, load from there in Cloud Run |
| Staging environment | Medium | Separate Cloud Run service for staging |
| Rate limiting | Medium | IP-based limits at API Gateway or middleware level |
| Health check endpoint | Done | /health exists |
| Structured logging | Medium | Switch print/logging to structured JSON for Cloud Logging |
| W&B experiment tracking | Medium | Wire into training scripts for model versioning |
| Redis caching | Low | Add after core deploy works |
| Monitoring dashboards | Low | Set up after deploy |

---

## Implementation Phases

### Phase 1 — Containerize and Deploy (Target: working public URL)

1. Write Terraform for GCP project:
   - Artifact Registry repository
   - Cloud Run service (staging + prod)
   - GCS bucket for model weights and outputs
   - Secret Manager secrets
   - Service accounts with minimal IAM
2. Push Docker image to Artifact Registry manually
3. Deploy to Cloud Run staging manually via gcloud CLI
4. Deploy React frontend to Vercel
5. Verify end-to-end: Vercel → Cloud Run → ML inference → response

### Phase 2 — CI/CD Pipeline

1. Create `.github/workflows/ci.yml`
   - On PR: lint, type check, pytest, frontend build
   - On merge to main: Docker build, push to Artifact Registry, deploy to staging, integration tests
2. Create `.github/workflows/deploy-prod.yml`
   - Manual approval gate for production
   - Canary rollout via Cloud Run traffic splitting
3. Set GitHub repository secrets (GCP service account key, project ID)

### Phase 3 — MLOps Layer

1. Add W&B tracking to training scripts (log accuracy, F1, latency, hyperparams)
2. Set up model versioning: models tagged with version, training run ID, metrics
3. Add model performance gate to CI: new model must beat baseline F1 before it can deploy
4. Document baseline vs fine-tuned comparison

### Phase 4 — Observability

1. Enable Cloud Monitoring for Cloud Run (automatic)
2. Set up alerts:
   - Error rate > 1% on any endpoint
   - Latency p95 > 800ms
   - Instance count > 10 (cost alert)
3. Create Grafana dashboard connecting to Cloud Monitoring
4. Add Evidently AI report generation for input drift

### Phase 5 — Polish and Portfolio Packaging

1. Architecture diagram in README
2. Deployment runbook (how to roll back a bad model)
3. Baseline vs fine-tuned model comparison documented
4. Cost breakdown documented
5. Live URL linked from GitHub profile

---

## Terraform Directory Structure (To Be Created)

```
infra/
  terraform/
    modules/
      cloud-run/
        main.tf
        variables.tf
        outputs.tf
      artifact-registry/
        main.tf
        variables.tf
      gcs/
        main.tf
        variables.tf
      secret-manager/
        main.tf
        variables.tf
    environments/
      staging/
        main.tf
        terraform.tfvars
        backend.tf
      prod/
        main.tf
        terraform.tfvars
        backend.tf
    variables.tf
    outputs.tf
```

---

## GitHub Actions Directory Structure (To Be Created)

```
.github/
  workflows/
    ci.yml              # PR checks: lint, test, build
    deploy-staging.yml  # Auto-deploy to staging on merge to main
    deploy-prod.yml     # Manual-approval deploy to production
  CODEOWNERS            # Who reviews what
```

---

## Cost Breakdown (Monthly, Portfolio Traffic)

| Service | Free Tier | Expected Usage |
|---------|-----------|----------------|
| GCP Cloud Run | 2M requests, 360K vCPU-seconds | Well within free tier |
| GCP Artifact Registry | 5 GB | 2–3 GB for Docker images |
| GCP Secret Manager | 6 active secrets free | ~5 secrets needed |
| GCP Cloud Storage | 5 GB free | Model weights ~500MB, outputs vary |
| GCP Cloud Monitoring | 150MB logs/day free | Fine for low traffic |
| Vercel | Unlimited hobby | Static SPA, always free |
| Upstash Redis | 10K commands/day free | Sufficient for demo traffic |
| Supabase PostgreSQL | 500MB free | Job queue, very small |
| W&B | Free for open projects | Unlimited experiment tracking |
| GitHub Actions | Free for public repos | Unlimited minutes |

**Total expected monthly cost: $0**

---

## Key Interview Talking Points

### On infrastructure
> "All infrastructure is defined in Terraform. No one clicks in the GCP console. Any engineer can spin up a fresh staging environment in under 10 minutes by running terraform apply."

### On CI/CD
> "Every PR triggers automated checks. Nothing reaches staging without passing lint, type checking, and model inference tests. Production requires a manual approval and deploys via canary — 5% traffic first, monitored, then promoted."

### On scaling
> "Cloud Run scales to zero at night and auto-scales up under load. For this project we'd comfortably handle 500 requests per minute on the free tier. If this needed to go to 50,000 requests per minute we'd move ML inference to GKE with GPU nodes and separate the API and inference layers."

### On auth
> "This is a public portfolio demo. Adding login would hurt conversion. Instead we rate-limit by IP at the API layer, validate all inputs server-side, lock CORS to our frontend domain, and use Cloud Armor as a WAF. If this became a paid product, we'd add JWT auth with scope-limited tokens."

### On model deployment
> "Models are versioned in W&B. A new model version only reaches production after it passes an automated accuracy gate in CI that compares it against the current production baseline. Deployment uses Cloud Run traffic splitting — the new model gets 5% of real traffic before full rollout."

### On observability
> "Three signals: logs via Cloud Logging, metrics via Cloud Monitoring, traces via Cloud Trace. We alert on error rate above 1% and p95 latency above 800ms. We also run Evidently AI reports to detect input data drift — when the kinds of images users upload start to differ from what the model was trained on."

---

## What GCP Is

GCP stands for **Google Cloud Platform**. It is Google's public cloud offering, equivalent to Amazon Web Services (AWS) or Microsoft Azure. It provides:

- **Compute**: Cloud Run (serverless), GKE (Kubernetes), Compute Engine (VMs)
- **Storage**: Cloud Storage (GCS), Cloud SQL, Firestore, BigQuery
- **Networking**: Cloud Load Balancer, Cloud CDN, Cloud Armor
- **ML**: Vertex AI, AutoML, TPU access
- **DevOps**: Artifact Registry, Cloud Build, Cloud Deploy
- **Observability**: Cloud Monitoring, Cloud Logging, Cloud Trace

For this project we use GCP for backend hosting (Cloud Run), container storage (Artifact Registry), media storage (GCS), secrets (Secret Manager), and monitoring (Cloud Monitoring).

---

*Plan authored: April 2026*
*Stack: React + FastAPI + YOLO11 + EfficientNet-B2 + GCP Cloud Run + Vercel + Terraform + GitHub Actions*
