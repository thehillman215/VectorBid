# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Build arguments for metadata
ARG COMMIT_SHA=unknown
ARG BUILD_DATE=unknown

# Set metadata labels
LABEL org.opencontainers.image.title="VectorBid"
LABEL org.opencontainers.image.description="AI-powered pilot schedule bidding assistant"
LABEL org.opencontainers.image.version="${COMMIT_SHA}"
LABEL org.opencontainers.image.created="${BUILD_DATE}"
LABEL org.opencontainers.image.source="https://github.com/vectorbid/vectorbid"
LABEL org.opencontainers.image.licenses="MIT"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=main.py \
    PORT=5000

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    glibc-source \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r vectorbid && useradd -r -g vectorbid vectorbid

# Set work directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/logs && \
    chown -R vectorbid:vectorbid /app

# Switch to non-root user
USER vectorbid

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)" || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--keepalive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "main:app"]