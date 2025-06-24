#!/usr/bin/env bash
set -euo pipefail

# Container build script for Ca-Bhfuil
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
IMAGE_NAME="ca-bhfuil"
TAG="latest"
DOCKERFILE="Dockerfile"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --tag)
            TAG="$2"
            shift 2
            ;;
        --name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --tag TAG      Set container tag (default: latest)"
            echo "  --name NAME    Set image name (default: ca-bhfuil)"
            echo "  --help         Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if container runtime is available
if command -v docker &> /dev/null; then
    RUNTIME="docker"
elif command -v podman &> /dev/null; then
    RUNTIME="podman"
else
    echo "Error: No container runtime found. Please install Docker or Podman."
    exit 1
fi

echo "Building production container..."
echo "Runtime: $RUNTIME"
echo "Image: $IMAGE_NAME:$TAG"
echo "Dockerfile: $DOCKERFILE"
echo ""

# Change to project directory
cd "$PROJECT_DIR"

# Build the container
$RUNTIME build \
    -f "$DOCKERFILE" \
    -t "$IMAGE_NAME:$TAG" \
    .

echo ""
echo "✅ Container built successfully: $IMAGE_NAME:$TAG"
echo ""
echo "To run the container:"
echo "  $RUNTIME run --rm $IMAGE_NAME:$TAG --help"
echo "  $RUNTIME run --rm $IMAGE_NAME:$TAG <command>"
echo ""
echo "To test the container:"
echo "  $RUNTIME run --rm $IMAGE_NAME:$TAG --version"
