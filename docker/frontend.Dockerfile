# ── Stage 1: Build ──────────────────────────────────────────────────────────
# Use Node.js 20 Alpine as the build environment (Alpine = minimal Linux, smaller image)
# AS build names this stage so Stage 2 can reference it
FROM node:20-alpine AS build

# Set working directory inside the container
WORKDIR /app

# ARG: build-time variable — only exists while Docker is building the image, not at runtime
# Default points to localhost, overridden in CI/CD to the actual Cloud Run URL
ARG VITE_API_BASE_URL=http://localhost:8000

# Assign the ARG to an ENV so Vite can read it during the npm run build step
# Vite requires env variables to be prefixed with VITE_ to expose them to React code
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# Copy only package files first (layer caching trick)
# If source code changes but package.json doesn't, Docker skips npm ci
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies using the lockfile exactly (stricter than npm install, no version drift)
RUN npm ci

# Now copy all frontend source code
COPY frontend ./

# Compile React source into static HTML/CSS/JS files (output goes to /app/dist)
RUN npm run build

# ── Stage 2: Serve ──────────────────────────────────────────────────────────
# Start fresh from a minimal nginx image — Node.js, npm, and node_modules are all discarded
# Final image only contains nginx + the compiled static files (~500KB vs ~1GB with Node)
FROM nginx:1.27-alpine

# Use a custom nginx config that handles React single-page app routing
# (so refreshing on /about doesn't return a 404)
COPY docker/frontend.nginx.conf /etc/nginx/conf.d/default.conf

# Copy only the built output from Stage 1 — not the source, not node_modules
COPY --from=build /app/dist /usr/share/nginx/html

# nginx serves on port 80, the standard HTTP port
EXPOSE 80
