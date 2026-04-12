# Base image: official Python 3.11 slim variant (smaller than full python image, no unnecessary OS packages)
FROM python:3.11-slim

# PYTHONDONTWRITEBYTECODE: don't create .pyc files (not needed in containers)
# PYTHONUNBUFFERED: print statements appear in logs immediately, not buffered
# PIP_NO_CACHE_DIR: don't cache pip downloads (saves image size)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Install system-level libraries that OpenCV and video processing need
# These are OS packages (apt-get), not Python packages (pip)
# --no-install-recommends: skip optional extras to keep image smaller
# rm -rf /var/lib/apt/lists/*: delete apt cache after installing to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory — all subsequent commands run from /app inside the container
WORKDIR /app

# Copy only requirements first (layer caching trick)
# If source code changes but requirements.txt doesn't, Docker skips the pip install step
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

# Now copy the actual source code (after installing deps to preserve cache)
COPY backend /app/backend
COPY src /app/src
COPY configs /app/configs

# Model weights are NOT baked into the image.
# - Local development: mount your local models/ folder as a volume via docker-compose
# - Production (Cloud Run): weights are downloaded from GCS at container startup

# Create the outputs directory so the app can write video/image results
RUN mkdir -p /app/outputs/videos

# Document that the app listens on port 8000 (does not actually publish it — that's done at runtime)
EXPOSE 8000

# Default inference mode — can be overridden at runtime with --env INFERENCE_MODE=mock
ENV INFERENCE_MODE=local

# Start the FastAPI server on all network interfaces (0.0.0.0) so it's reachable from outside the container
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
