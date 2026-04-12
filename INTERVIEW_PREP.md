# Interview Prep — System Design, MLOps, and Deployment

## Project: Emotion Vision — YOLO Face Detection + Emotion Classification
## Stack: React + FastAPI + GCP Cloud Run + Terraform + GitHub Actions + W&B

---

> How to use this file: Read each question out loud. Cover the answer. Try to say it yourself first. Then read the answer. The goal is to internalize the reasoning, not memorize the words.

---

## Section 1 — Infrastructure and Deployment

---

**Q: Walk me through how your application is deployed.**

A: The frontend is a React/Vite app deployed to Vercel, which gives me a global CDN and HTTPS out of the box. The backend is a FastAPI service containerized with Docker and deployed to GCP Cloud Run. Cloud Run is a serverless container platform — I give it a Docker image, it handles everything else: scaling, HTTPS, load balancing. All the infrastructure is defined in Terraform, so nothing is clicked manually in the console. Every change to infrastructure goes through code review just like application code.

---

**Q: What is Terraform and why did you use it instead of clicking in the GCP console?**

A: Terraform is an Infrastructure as Code tool. You describe your infrastructure in configuration files and Terraform creates or updates the actual cloud resources to match. I used it because clicking in a console is not reproducible — if I need to recreate the environment, or if a colleague needs to set up their own, there's no record of what was done. With Terraform, the entire infrastructure is version-controlled in Git. Anyone can run `terraform apply` and get an identical environment. It also means infrastructure changes go through pull requests, with review and history, same as code changes.

---

**Q: What is Cloud Run and how does it scale?**

A: Cloud Run is Google's serverless container platform. You give it a Docker image and it runs your code without you managing servers. It scales automatically based on incoming requests — if traffic spikes, it adds more container instances within seconds. If there's no traffic, it scales down to zero, meaning you pay nothing. For an ML inference API like mine, this is ideal because traffic is unpredictable — a portfolio site might get zero requests for days and then suddenly get a hundred from a recruiter sharing a link.

---

**Q: How would your system handle a sudden 10x spike in traffic?**

A: Cloud Run handles this automatically. It monitors CPU utilization and request concurrency. When either exceeds the target threshold, it spins up additional container instances — typically within 30 seconds. I keep one instance always warm (min-instances = 1) to avoid cold starts. At 10x traffic the system would scale horizontally with no manual intervention. If we're talking 100x or sustained very high traffic, I'd move the ML inference layer to GKE with GPU nodes and a Horizontal Pod Autoscaler, and separate the API routing layer from the inference layer so they scale independently.

---

**Q: What is a cold start and how did you handle it?**

A: A cold start happens when a request comes in and there are no warm container instances ready. Cloud Run has to pull the image, start the container, load the application, and load the ML models — for a PyTorch model this can take 15 to 30 seconds. To avoid this I set min-instances to 1, which keeps one container always running and warm. The trade-off is a small always-on cost, but for a portfolio demo where the first impression matters, a 30-second wait on the first request would be unacceptable.

---

**Q: Why did you separate the frontend and backend deployments?**

A: They have fundamentally different requirements. The frontend is a static collection of HTML, CSS, and JavaScript files — it needs a CDN for global fast delivery, that's all. Vercel is purpose-built for this and does it better than any general cloud platform. The backend runs Python code with ML models, needs compute, and may eventually need GPU access. Keeping them separate means I can scale, update, and optimize each independently. I can deploy a frontend change without touching the backend and vice versa. It's also a cleaner mental model — frontend is presentation, backend is computation.

---

**Q: How do you manage environment variables and secrets?**

A: Secrets — API keys, model credentials, database passwords — live in GCP Secret Manager, not in environment variable files or code. Cloud Run accesses them at runtime via a service account that has the minimum IAM permissions needed. This means secrets are never in Git, never in Docker images, never in plain text anywhere. Each environment (staging, production) has its own set of secrets. Rotation is handled in Secret Manager without touching the application code.

---

**Q: What is the difference between staging and production in your setup?**

A: Staging is a separate Cloud Run service running the same Docker image as production. Every code change is deployed to staging automatically when it merges to main. Staging runs with real infrastructure but fake or test data. Production only receives a deployment after staging passes integration tests and a human approves the release. This gives a safety layer — if something breaks in staging, production is unaffected. Staging also lets me test the full deployment pipeline (secrets, environment variables, external connections) before anything reaches real users.

---

## Section 2 — CI/CD Pipeline

---

**Q: Explain your CI/CD pipeline from a commit to production.**

A: When I open a pull request, GitHub Actions automatically runs three things in parallel: Python linting and type checking with ruff and mypy, unit tests with pytest, and a frontend build check with Vite. If any of these fail, the PR cannot merge. When the PR merges to main, a second pipeline runs: it builds a Docker image, tags it with the commit SHA, pushes it to GCP Artifact Registry, deploys it to the staging Cloud Run service, and then runs integration tests against the live staging URL — actual HTTP requests checking that the health endpoint returns 200, that an image inference request returns a valid response, and that latency is under 800ms. If those pass, the staging deployment is confirmed. Production deployment then requires a manual approval, after which it does a canary rollout — 5% of traffic goes to the new version, we monitor for 10 minutes, then 25%, then 100%.

---

**Q: Why do you tag Docker images with the commit SHA?**

A: So every image is traceable. If I see a bug in production I can look up which commit SHA is deployed, go to that exact commit in Git, and see precisely what code is running. If I tagged images as "latest" only, I'd have no idea what version is actually deployed. The SHA tag also makes rollback trivial — I just point Cloud Run at the previous SHA tag.

---

**Q: What is a canary deployment?**

A: A canary deployment is a rollout strategy where you send a small percentage of real traffic to the new version before fully switching over. In my setup, the new version starts at 5% of traffic. If error rates and latency stay within acceptable bounds for 10 minutes, it goes to 25%, then 100%. If something goes wrong at 5%, only 5% of users saw the bad behavior, and rolling back is instant — just shift traffic back to the previous revision. The name comes from the old mining practice of bringing canary birds into coal mines to detect gas before it could affect the miners.

---

**Q: What branching strategy do you use?**

A: Trunk-based development. There is one main branch and it is always in a deployable state. Developers work in short-lived feature branches — ideally merged within a day or two. There are no long-lived release branches or develop branches. This keeps the team moving fast, reduces merge conflicts, and means the main branch always reflects the current state of the product. It requires strong automated testing to work well, which is why the CI pipeline catches issues before merge.

---

**Q: What tests do you run in CI for an ML project specifically?**

A: Beyond standard unit tests, I run ML-specific tests: loading the model and running inference on a known test image, asserting the output shape and type are correct, checking that the predicted emotion label is in the valid set, and asserting inference latency is under a threshold. This catches regressions like a model file being corrupted, a dependency version change breaking inference, or a preprocessing change that silently changes output format. These tests run against the actual model, not a mock, so they catch real problems.

---

## Section 3 — MLOps and Model Management

---

**Q: What is MLOps and what does it mean in your project?**

A: MLOps is the practice of applying software engineering discipline to machine learning — version control, testing, automated deployment, monitoring — for both the code and the models. In my project it means: every training run is logged to W&B with its hyperparameters, dataset version, and metrics. Models are versioned and promoted through stages — Staging then Production — only when they meet a performance threshold. Deployment is automated through a CI/CD pipeline. The deployed model is monitored in production for latency and accuracy drift. If I retrain with new data, the new model has to beat the current production model's F1 score before it can deploy. This is the same discipline you'd apply to software — you wouldn't ship code without tests, and you shouldn't ship a new model without validation.

---

**Q: How do you version your ML models?**

A: Models are tracked in Weights & Biases. Every training run logs the hyperparameters, dataset used, training metrics (loss, accuracy, F1 per class), and the final model artifact. The artifact gets a version number and a stage — either Staging or Production. When I want to deploy a new model, I run evaluation against the held-out test set, and if it beats the current Production model's macro F1, it gets promoted to Production in the registry. The CI pipeline then picks up the Production-tagged model artifact and deploys it. This means there's always a clear record of which model is in production, what it scored, and what training run produced it.

---

**Q: How would you handle retraining when model performance degrades?**

A: First, detection. I monitor the distribution of incoming images and the distribution of predicted emotion labels in production. If the input distribution shifts significantly — say, the system suddenly starts getting many more low-light images than it was trained on — Evidently AI generates a data drift report. If prediction distribution shifts — say, the model starts predicting "neutral" 80% of the time when it used to be 40% — that's a signal of degradation. Second, response: I'd collect a sample of the new production inputs, label them (either manually or with a stronger model), add them to the training set, retrain, evaluate, and if the new model beats the current production F1, promote it through the standard pipeline. The key is that retraining is not manual and ad hoc — it follows the same versioned, tested, gated pipeline as the original training.

---

**Q: What metrics do you track for your emotion classifier?**

A: Macro F1 is the primary metric because the emotion classes are imbalanced — "neutral" appears far more than "disgusted" or "fearful." Accuracy alone would be misleading. I also track per-class recall so I can see which emotions the model struggles with — typically confused pairs like angry/disgusted or sad/fearful. For production monitoring I track inference latency (p50 and p95), error rate on the inference endpoint, and prediction distribution over time. For the face detector specifically I care about recall — missing a face is worse than a false positive.

---

**Q: What is data drift and why does it matter for ML?**

A: Data drift is when the distribution of inputs the model receives in production starts to differ from the distribution it was trained on. ML models are essentially pattern matchers — they learn patterns from training data. If production inputs look significantly different, the patterns don't generalize and performance degrades, often silently. For example, my emotion classifier was trained on frontal, well-lit faces. If deployed in a CCTV context with angled, low-light faces, the model will degrade even though the code hasn't changed. Monitoring for drift catches this before users notice. Evidently AI compares the statistical distribution of incoming image features against a baseline snapshot from training.

---

**Q: What is the difference between online and batch inference?**

A: Online inference is real-time — a user uploads an image, the model processes it immediately and returns a result in under a second. This is what my image endpoint does. Batch inference is processing a large volume of inputs offline, often scheduled — for example, processing all videos uploaded in the last 24 hours overnight. My video processing endpoint approaches batch territory — it's an async job because processing a 2-minute video takes time. At scale you'd use a proper job queue (like Cloud Tasks or Pub/Sub) so the API returns a job ID immediately and the client polls for completion, rather than holding an HTTP connection open for minutes.

---

## Section 4 — System Design

---

**Q: Design a system that can handle 10,000 concurrent image uploads for emotion detection.**

A: At that scale I'd decompose the system into separate layers. First, the upload layer: clients upload images directly to GCS via signed URLs — the backend generates a short-lived signed URL and the browser uploads to GCS directly, so the backend never touches the bytes and doesn't become a bottleneck. GCS triggers a Pub/Sub message when each upload completes. Second, the inference layer: a pool of workers (Cloud Run Jobs or GKE pods with autoscaling) consumes from the Pub/Sub topic. Each worker pulls a job, downloads the image from GCS, runs YOLO detection and emotion classification, writes the result to Cloud SQL, and publishes a completion event. Third, the result layer: the client polls a results endpoint or receives a webhook. The key insight is decoupling upload from inference — they scale independently, and a spike in uploads doesn't cascade into inference failures.

---

**Q: How would you reduce inference latency?**

A: Several layers. First, Redis caching — if the same image is uploaded twice (hashed by content), return the cached result in under 5ms instead of running inference. Second, model optimization — export the PyTorch model to ONNX and run it with ONNX Runtime, which is typically 2-3x faster than PyTorch for inference. Then quantize the model to INT8, which reduces model size and speeds up inference at a small accuracy cost. Third, hardware — move from CPU inference to a GPU instance; a T4 GPU gives roughly 10x throughput for vision models. Fourth, batching — instead of processing one image at a time, accumulate requests for 20ms and process a batch together; GPUs are much more efficient on batches than single images.

---

**Q: Your video inference is slow. How would you fix it?**

A: The current approach processes the entire video synchronously inside an HTTP request, which is wrong for anything over a few seconds. The correct architecture is: the client uploads the video to GCS via a signed URL, the backend records a job in the database and returns a job ID immediately (202 Accepted), a background worker picks up the job from a queue, processes the video frame by frame, writes the annotated output to GCS, and updates the job status in the database. The client polls the job status endpoint. This decouples upload latency from processing time, lets multiple videos be processed in parallel, and gives the user feedback without holding an HTTP connection open for minutes.

---

**Q: How does your system handle failures gracefully?**

A: At the API level, every endpoint has input validation — wrong file type or oversized file returns a 400 or 413 before touching the model. If the model fails for any reason, the service returns a structured error response, not a crash. Cloud Run restarts failed containers automatically. For video processing jobs, failed jobs are retried up to three times with exponential backoff before being marked as failed, and the client is notified. At the deployment level, canary rollouts mean a bad deploy only affects 5% of traffic before being caught and rolled back. I also have health checks — Cloud Run routes traffic only to instances that pass the /health check.

---

**Q: How do you handle multiple faces in a single image?**

A: The YOLO detector returns bounding boxes for every detected face in the image. For each bounding box, I crop the face region, pad it slightly to preserve facial context, resize to the classifier input size (224x224), normalize with the backbone's expected statistics, and run the emotion classifier. The response includes an array of results — one entry per detected face — each with its bounding box coordinates, detection confidence, predicted emotion, and emotion confidence. If a face's emotion confidence is below a threshold I return "uncertain" rather than forcing an incorrect label.

---

## Section 5 — Security

---

**Q: How do you secure your API?**

A: Several layers. CORS is locked to my Vercel frontend domain — other websites can't make requests to my API from a browser. File size limits prevent payload attacks. Content-type validation rejects anything that isn't an image or video before it touches the inference code. Rate limiting at the API Gateway layer prevents a single IP from hammering the endpoint and running up compute costs. GCP Cloud Armor acts as a Web Application Firewall, blocking known attack patterns. Secrets are in Secret Manager, not in code or environment files. The Cloud Run service account has only the permissions it needs and nothing more — principle of least privilege.

---

**Q: Why didn't you add user authentication?**

A: Because this is a public portfolio demo, and auth would hurt it. The goal is for anyone — a recruiter, a hiring manager, a collaborator — to open the URL and immediately try the demo without friction. Adding a login flow would reduce that. There's no user data being stored, no private data, no billing per user. The threats I care about — abuse and DoS — are handled by rate limiting and file size limits, not by auth. If this became a paid product with user accounts, I'd add JWT-based auth with short-lived tokens, refresh token rotation, and scope-limited access. Knowing when to add auth is as important as knowing how to add it.

---

**Q: What is the principle of least privilege?**

A: Every component in the system gets only the permissions it needs to do its job and nothing more. My Cloud Run service has a dedicated service account. That account can read from the specific GCS bucket where models are stored, read the specific secrets it needs from Secret Manager, and write to the outputs bucket. It cannot create new cloud resources, access other projects, modify IAM, or read secrets it doesn't need. If the service account is compromised, the blast radius is small — an attacker gets only what that account could access. This is a foundational security principle and applies equally to service accounts, database users, and API tokens.

---

## Section 6 — Trade-off Questions

---

**Q: Why GCP Cloud Run and not AWS Lambda or Azure Container Apps?**

A: All three are viable serverless container platforms. I chose Cloud Run for three reasons: it has the most generous always-free tier (2 million requests per month), it supports arbitrary Docker containers without size restrictions that Lambda imposes, and the cold start behavior for container-based workloads is better than Lambda. For a real team the choice would depend on what cloud the organization already uses. The concepts — serverless containers, auto-scaling, pay-per-request — are identical across all three.

---

**Q: Why Vercel for the frontend instead of GCP Cloud CDN?**

A: Vercel is faster to set up and free for static sites. Cloud CDN requires a Load Balancer, a GCS bucket configured as a backend, and CDN policy configuration — it's several Terraform resources. Vercel is one command. The end result is the same — a globally distributed static site — but Vercel gets there in minutes. In a real organization on GCP I'd use Cloud CDN for consistency. For a solo portfolio project, Vercel is the practical choice.

---

**Q: Why W&B instead of MLflow for experiment tracking?**

A: Both are correct choices and I know both. W&B has a better hosted UI out of the box — experiment comparison, metric plots, and model registry are all built in and free for open projects. MLflow is more self-hosted-friendly and is common in enterprise environments where data can't leave the company's infrastructure. If I were in a large organization with data privacy requirements, I'd run MLflow on internal infrastructure. For an open portfolio project, W&B's hosted version gives me more for less setup.

---

**Q: Why Supabase instead of Cloud SQL for the database?**

A: Cloud SQL has no free tier — even the smallest instance costs around $7 per month. Supabase provides hosted PostgreSQL with a 500MB free tier. It's the same PostgreSQL underneath — the SQL queries, schema design, and connection patterns are identical. In production at a company on GCP I'd use Cloud SQL for native integration and better SLA guarantees. For a portfolio project where the database is a small job queue for video processing, Supabase is the practical choice. The architecture is the same, the specific host differs.

---

**Q: When would you move from Cloud Run to Kubernetes (GKE)?**

A: Cloud Run is ideal for stateless HTTP services with variable traffic. I'd move to GKE when: the ML models require GPU acceleration (Cloud Run GPU support is limited compared to GKE), when I need stateful workloads like a model server with a persistent KV cache, when I need fine-grained control over scheduling and resource allocation, or when I'm running multiple ML services that need to communicate efficiently over a service mesh. GKE is more powerful but also more complex to operate — more YAML, more networking configuration, more to monitor. Cloud Run's simplicity is a feature, not a limitation, until you outgrow it.

---

## Section 7 — Behavioral / Process Questions

---

**Q: How would you roll back a bad deployment?**

A: On Cloud Run, rollback is one command or one click — I point traffic back to the previous revision. Because every Docker image is tagged with its commit SHA and stored in Artifact Registry, the previous version is always available. The canary strategy means I'd likely catch a bad deployment at 5% traffic before it reaches 100%, so fewer users are affected. In the worst case of a full rollout, I run `gcloud run services update-traffic --to-revisions=PREVIOUS_SHA=100` and traffic shifts instantly. I then investigate the bad revision, fix the issue, and go through the pipeline again.

---

**Q: How do you know if your deployed model is performing well?**

A: Three signals. First, infrastructure metrics — latency and error rate from Cloud Monitoring. If the endpoint starts returning 500 errors or latency spikes, something is wrong with the serving layer. Second, prediction distribution monitoring — I track the distribution of predicted emotion labels over time. If "neutral" goes from 40% to 80% of predictions overnight, the model may have degraded or the inputs changed. Third, data drift reports from Evidently AI — periodic comparison of incoming image feature distributions against the training baseline. Together these give me confidence that the model is not just running but running well.

---

**Q: What would you do differently if you were doing this at a company with a team of 10 engineers?**

A: Several things. I'd use separate GCP projects for dev, staging, and production — not just separate Cloud Run services — for complete blast radius isolation. I'd add a proper feature store for managing preprocessing features consistently between training and serving. I'd use a dedicated model serving framework like BentoML or Triton Inference Server rather than running inference directly in FastAPI, which gives better batching, model versioning, and GPU utilization. I'd add an A/B testing framework so we could run model experiments on real traffic with statistical rigor. I'd add proper distributed tracing so we can debug latency across services. And I'd set up a proper on-call rotation with PagerDuty integration on the monitoring alerts.

---

**Q: What did you learn from building this that you didn't expect?**

A: The hard part of MLOps is not the individual tools — it's the integration between them. Getting training, versioning, CI/CD, serving, and monitoring to work as a coherent pipeline where a new model flows automatically from training to production with appropriate gates — that's where the complexity lives. I also learned that monitoring for ML systems needs to go beyond standard infrastructure monitoring. A service can be technically healthy — low error rate, good latency — while the model's predictions are quietly degrading because the input distribution shifted. That's a class of failure that software engineers don't typically encounter, and it requires ML-specific tooling to catch.

---

*File created: April 2026*
*Project: Emotion Vision — github.com/[your-handle]/emotion-vision*
