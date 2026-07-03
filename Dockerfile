# =============================================================================
# Automated Tender Response Agent — Dockerfile
# =============================================================================
# Multi-stage build:
#   builder  — installs Python dependencies
#   runtime  — slim final image
# =============================================================================

FROM python:3.12-slim AS builder

# System deps for PDF & document processing
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt

# =============================================================================

FROM python:3.12-slim AS runtime

LABEL maintainer="your-email@example.com"
LABEL description="Automated Tender Response Agent (AI + RAG)"

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# System runtime libs
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application source
COPY app/ ./app/
COPY data/ ./data/

# Create directories that must exist at runtime
RUN mkdir -p vector_store data/raw data/processed

# Run as non-root for security
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
