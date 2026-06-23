# Docker Deployment Guide

## Purpose

This document describes how to build and run the Customer Complaint
Intelligence Platform using Docker.

The Docker image contains:
- The Streamlit dashboard (`app/`)
- Pipeline source code (`src/`)
- Config files (`config.yaml`, `.streamlit/config.toml`)
- Already-computed dashboard Parquet artifacts (`data/processed/`)
- Already-trained NLP model artifacts (`models/nlp/`)

The raw dataset (`data/raw/`) is excluded from the image. See
`architecture.md` → Deployment Layer for why the image is built this
way (one-command demo execution, not full-pipeline-from-scratch
execution inside the container).

---

## Build Image

```bash
docker build -t customer-complaint-intelligence:v1 .
```

---

## Run Container

```bash
docker run -p 8501:8501 customer-complaint-intelligence:v1
```

Open: `http://localhost:8501`

---

## Docker Hub Image

Repository: [hub.docker.com/repository/docker/shivamrajput130/customer-complaint-intelligence](https://hub.docker.com/repository/docker/shivamrajput130/customer-complaint-intelligence)

```bash
docker pull shivamrajput130/customer-complaint-intelligence:latest
docker run -p 8501:8501 shivamrajput130/customer-complaint-intelligence:latest
```

---

## Verifying the Container Is Running

```bash
docker ps
docker logs -f customer-complaint-intelligence
```

A healthy container should show the Streamlit startup log lines and
respond on `http://localhost:8501` within the configured health-check
start period.

---

## Production-Style Multi-Stage Dockerfile

```dockerfile
FROM python:3.11-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

FROM base AS dependencies

COPY requirements.txt .

RUN pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt

FROM dependencies AS runtime

COPY app/ app/
COPY src/ src/
COPY config.yaml .
COPY data/processed/ data/processed/
COPY models/nlp/ models/nlp/
COPY .streamlit/ .streamlit/

RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501')" || exit 1

CMD ["streamlit", "run", "app/streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

This is a multi-stage build: the `base` stage installs OS-level build
tools, `dependencies` installs Python packages (cached separately so
code changes don't force a full dependency reinstall), and `runtime`
copies in the actual application and pre-computed artifacts. The
container runs as a non-root user (`appuser`) rather than the default
root, which is a standard hardening practice — if the container were
ever compromised, the process would not have root privileges inside it.

---

## docker-compose.yaml

```yaml
version: "3.9"

services:
  complaint-intelligence:
    image: shivamrajput130/customer-complaint-intelligence:latest
    container_name: customer-complaint-intelligence
    ports:
      - "8501:8501"
    networks:
      - complaint-net
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8501')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

networks:
  complaint-net:
    driver: bridge
```

### Run with Compose

```bash
docker compose up -d
```

Logs:

```bash
docker logs -f customer-complaint-intelligence
```

Stop:

```bash
docker compose down
```

---

## Files Excluded from the Docker Image

`.dockerignore` excludes:

```text
data/raw/
assets/
reports/
tests/
notebooks/
logs/
.env
```

The image includes:

```text
app/
src/
config.yaml
data/processed/
models/nlp/
requirements.txt
.streamlit/
```

---

## Why the Image Includes Pre-Computed Artifacts

The image intentionally bundles `data/processed/` and `models/nlp/`
rather than expecting the user to run the preprocessing pipeline and
NLP training inside the container. This means a single `docker run`
produces a fully working dashboard immediately, at the cost of a larger
image than a minimal "just the app code" image would be. This is a
deliberate trade-off — see `case_study.md` → Rejected Approaches for
the alternative that was not used (retraining/reprocessing on container
startup).

---

## Troubleshooting

### Port Already Allocated

```bash
docker run -p 8502:8501 customer-complaint-intelligence:v1
```

Open: `http://localhost:8502`

### NLP Model Loading Error

This usually means a dependency version mismatch between the
environment the models were trained/pickled in and the environment
installed inside the container (`numpy`, `scikit-learn`, and `joblib`
versions all matter for unpickling). Ensure `models/nlp/` is included
in the build context and that `requirements.txt` pins versions matching
the training environment.

### Parquet File Missing

The dashboard expects pre-computed Parquet files under
`data/processed/dashboard/`. If the image was built without running the
pipeline first, run it before building:

```bash
python -m src.preprocessing
python -m src.pipeline
```

Then rebuild the image so the artifacts get copied in.

### Streamlit Theme Not Applying

The dark theme is controlled by `.streamlit/config.toml`. Confirm this
file exists at that exact path (not just `config.toml` in the project
root) — Streamlit only reads theme settings from
`.streamlit/config.toml` relative to the app's working directory.