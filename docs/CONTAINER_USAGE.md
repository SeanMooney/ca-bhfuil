# Ca-Bhfuil Container Usage Guide

> **Complete guide for using Ca-Bhfuil containers with security verification**

## Quick Start

### Running the Container

```bash
# Basic usage
docker run --rm ghcr.io/seanmooney/ca-bhfuil:latest --help

# With local repository
docker run --rm -v $(pwd):/workspace ghcr.io/seanmooney/ca-bhfuil:latest status

# Interactive mode
docker run -it --rm --entrypoint sh ghcr.io/seanmooney/ca-bhfuil:latest
```

### Using with Podman

```bash
# Same commands work with Podman
podman run --rm ghcr.io/seanmooney/ca-bhfuil:latest --version

# Rootless containers
podman run --rm -v $(pwd):/workspace:Z ghcr.io/seanmooney/ca-bhfuil:latest status
```

## Security Verification

### Container Signature Verification

Ca-Bhfuil containers are signed using [Cosign](https://docs.sigstore.dev/cosign/overview/) with GitHub OIDC for keyless signing.

#### Install Cosign

```bash
# Install cosign
curl -O -L "https://github.com/sigstore/cosign/releases/latest/download/cosign-linux-amd64"
sudo mv cosign-linux-amd64 /usr/local/bin/cosign
sudo chmod +x /usr/local/bin/cosign
```

#### Verify Container Signatures

```bash
# Verify container signature (replace with actual version)
cosign verify \
  --certificate-identity-regexp=".*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/seanmooney/ca-bhfuil:v1.0.0

# Verify with specific GitHub identity
cosign verify \
  --certificate-identity="https://github.com/SeanMooney/ca-bhfuil/.github/workflows/build-and-release.yml@refs/tags/v1.0.0" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/seanmooney/ca-bhfuil:v1.0.0
```

#### Verify SBOM Attestations

```bash
# Verify SBOM attestation
cosign verify-attestation \
  --type spdxjson \
  --certificate-identity-regexp=".*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/seanmooney/ca-bhfuil:v1.0.0

# Download and inspect SBOM
cosign download attestation \
  --predicate-type spdxjson \
  ghcr.io/seanmooney/ca-bhfuil:v1.0.0 | jq '.payload | @base64d | fromjson'
```

### Python Package Verification

Python packages are published to PyPI with PEP 740 attestations when available.

```bash
# Install with pip (attestations are verified automatically when supported)
pip install ca-bhfuil

# Verify package integrity
pip check ca-bhfuil
```

## Container Configuration

### Environment Variables

```bash
# Set ca-bhfuil environment
docker run --rm -e CA_BHFUIL_ENV=production ghcr.io/seanmooney/ca-bhfuil:latest

# Configure logging level
docker run --rm -e CA_BHFUIL_LOG_LEVEL=DEBUG ghcr.io/seanmooney/ca-bhfuil:latest
```

### Volume Mounts

```bash
# Mount git repository
docker run --rm \
  -v /path/to/repo:/workspace \
  ghcr.io/seanmooney/ca-bhfuil:latest status

# Mount config directory
docker run --rm \
  -v ~/.config/ca-bhfuil:/home/nonroot/.config/ca-bhfuil:ro \
  ghcr.io/seanmooney/ca-bhfuil:latest config show

# Mount cache for performance
docker run --rm \
  -v ca-bhfuil-cache:/home/nonroot/.cache/ca-bhfuil \
  -v $(pwd):/workspace \
  ghcr.io/seanmooney/ca-bhfuil:latest search "CVE-2024"
```

## Examples

### Repository Analysis

```bash
# Analyze current directory
docker run --rm -v $(pwd):/workspace ghcr.io/seanmooney/ca-bhfuil:latest status

# Search for commits
docker run --rm -v $(pwd):/workspace \
  ghcr.io/seanmooney/ca-bhfuil:latest search "fix security"

# Verbose output
docker run --rm -v $(pwd):/workspace \
  ghcr.io/seanmooney/ca-bhfuil:latest status --verbose
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Analyze Repository
  run: |
    docker run --rm \
      -v ${{ github.workspace }}:/workspace \
      ghcr.io/seanmooney/ca-bhfuil:latest status --verbose
```

```yaml
# GitLab CI example
analyze_commits:
  image: ghcr.io/seanmooney/ca-bhfuil:latest
  script:
    - ca-bhfuil status --verbose
  only:
    - main
```

## Troubleshooting

### Debug Container Issues

```bash
# Access container shell
docker run -it --rm --entrypoint sh ghcr.io/seanmooney/ca-bhfuil:latest

# Check installed packages
docker run --rm ghcr.io/seanmooney/ca-bhfuil:latest sh -c "pip list"

# Inspect container layers
docker history ghcr.io/seanmooney/ca-bhfuil:latest
```

### Common Issues

#### Permission Denied

```bash
# Use proper SELinux context (Podman/RHEL)
podman run --rm -v $(pwd):/workspace:Z ghcr.io/seanmooney/ca-bhfuil:latest status

# Run as current user (if needed)
docker run --rm --user $(id -u):$(id -g) \
  -v $(pwd):/workspace ghcr.io/seanmooney/ca-bhfuil:latest status
```

#### Git Repository Access

```bash
# Ensure git config is available
docker run --rm \
  -v ~/.gitconfig:/home/nonroot/.gitconfig:ro \
  -v $(pwd):/workspace \
  ghcr.io/seanmooney/ca-bhfuil:latest status
```

#### Network Issues

```bash
# Test network connectivity
docker run --rm ghcr.io/seanmooney/ca-bhfuil:latest sh -c "ping -c 1 github.com"

# Use host network for debugging
docker run --rm --network host ghcr.io/seanmooney/ca-bhfuil:latest
```

## Security Best Practices

### Container Runtime Security

1. **Always verify signatures** before running containers
2. **Use specific version tags** instead of `latest` in production
3. **Run with minimal privileges** - containers run as non-root by default
4. **Mount volumes read-only** when possible
5. **Use secrets management** for sensitive configuration

### Example Secure Usage

```bash
# Production usage example
cosign verify \
  --certificate-identity-regexp=".*" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  ghcr.io/seanmooney/ca-bhfuil:v1.2.3

docker run --rm \
  --security-opt=no-new-privileges \
  --cap-drop=ALL \
  --read-only \
  -v $(pwd):/workspace:ro \
  -v /tmp:/tmp \
  ghcr.io/seanmooney/ca-bhfuil:v1.2.3 status
```

## Available Tags

- `latest` - Latest stable release (main branch)
- `v1.2.3` - Specific version releases
- `main` - Development builds (not signed)

## Support

For issues with containers:
- [Container Issues](https://github.com/SeanMooney/ca-bhfuil/issues/new?labels=container)
- [Security Reports](https://github.com/SeanMooney/ca-bhfuil/security/advisories/new)

For general usage:
- [Documentation](https://github.com/SeanMooney/ca-bhfuil/docs)
- [Discussions](https://github.com/SeanMooney/ca-bhfuil/discussions)