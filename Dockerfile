# VOIP Provisioning Server Dockerfile
# ====================================
# Multi-stage build for minimal image size

FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN pip install --no-cache-dir build

# Copy source
COPY pyproject.toml requirements.txt ./
COPY src/ src/

# Build wheel
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# ---- Runtime image ----
FROM python:3.11-slim

LABEL maintainer="BRCS IT"
LABEL description="VOIP Phone Provisioning Server"

WORKDIR /app

# Install wheels from builder
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*.whl && rm -rf /wheels

# Copy templates and default config
COPY templates/ templates/
COPY config.yml .

# Create inventory directory (will be mounted as volume)
RUN mkdir -p inventory

# Create non-root user
RUN useradd --create-home --shell /bin/bash provisioner
RUN chown -R provisioner:provisioner /app
USER provisioner

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" || exit 1

# Run server
CMD ["python", "-m", "provisioner.server"]
