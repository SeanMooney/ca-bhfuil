# Multi-stage build: UV builder + Alpine runtime
# Based on packaging design in docs/design/packaging.md

# ============================================================================
# Stage 1: Builder - Use UV image for fast Python builds
# ============================================================================
FROM ghcr.io/astral-sh/uv:python3.12-alpine AS builder

# Set working directory
WORKDIR /app

# Copy dependency files first for better caching
COPY pyproject.toml uv.lock ./

# Install system dependencies needed for building (libgit2, etc.)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libgit2-dev \
    pkgconfig \
    git

# Create virtual environment and install dependencies
RUN uv venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies using UV
RUN uv pip install -r pyproject.toml

# Copy source code
COPY . .

# Build the package
RUN uv build

# Install the built package
RUN uv pip install dist/*.whl

# ============================================================================
# Stage 2: Runtime - Minimal Alpine image
# ============================================================================
FROM python:3.12-alpine AS runtime

# Install runtime dependencies (libgit2 for pygit2)
RUN apk add --no-cache \
    libgit2 \
    git \
    && rm -rf /var/cache/apk/*

# Create non-root user
RUN addgroup -g 65532 -S nonroot && \
    adduser -u 65532 -S nonroot -G nonroot

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Switch to non-root user
USER nonroot

# Set working directory
WORKDIR /workspace

# Default entrypoint
ENTRYPOINT ["ca-bhfuil"]
CMD ["--help"]
