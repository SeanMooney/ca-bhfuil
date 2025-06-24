# Multi-stage build: Alpine builder → Distroless runtime
# Based on Ca-Bhfuil packaging design v2.0

# Stage 1: Builder - Alpine Linux with build tools
FROM python:3.12-alpine@sha256:c7eb5c92b7933fe52f224a91a1ced27b91840ac9c69c58bef0ba1a93a9e7e52d as builder

# Install system build dependencies
RUN apk add --no-cache \
    gcc=13.2.1_git20231014-r0 \
    musl-dev=1.2.4_git20230717-r4 \
    libgit2-dev=1.7.2-r0 \
    pkgconfig=2.1.0-r0 \
    libffi-dev=3.4.4-r3 \
    openssl-dev=3.1.6-r0

# Install UV for fast package management
RUN pip install --no-cache-dir uv==0.4.18

# Set working directory
WORKDIR /build

# Copy dependency files for better layer caching
COPY pyproject.toml uv.lock ./

# Copy source code
COPY src/ src/
COPY README.md CLAUDE.md ./

# Install dependencies and build package
RUN uv sync --frozen --no-dev && \
    uv build && \
    pip install --no-deps dist/*.whl

# Stage 2: Runtime - Google Distroless Python
FROM gcr.io/distroless/python3-debian12:3.12@sha256:b31a10825c7ad6b44bfe67a436d6b5c73e49b0ad31b6e4a0ec4e22bb91d1e6fb

# Set working directory
WORKDIR /app

# Copy the Python environment with installed package from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/ca-bhfuil /usr/local/bin/ca-bhfuil

# Set environment variables
ENV CA_BHFUIL_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

# Use nonroot user (UID 65532) - default in distroless
USER 65532:65532

# Default command
ENTRYPOINT ["ca-bhfuil"]
CMD ["--help"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["ca-bhfuil", "--version"]

# OCI labels for metadata
LABEL org.opencontainers.image.title="Ca-Bhfuil" \
      org.opencontainers.image.description="Git repository analysis tool for tracking commits across stable branches" \
      org.opencontainers.image.source="https://github.com/SeanMooney/ca-bhfuil" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.authors="Sean Mooney" \
      org.opencontainers.image.vendor="Ca-Bhfuil Project"
