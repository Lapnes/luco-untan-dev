# Multi-stage Dockerfile untuk Luco (Informatika UNTAN)
# Kompatibel dengan OCI container image untuk deployment ke Docker / Proxmox VE

# Stage 1: Build & install environment via Pixi
FROM ghcr.io/prefix-dev/pixi:latest AS builder
WORKDIR /app

COPY pixi.toml pixi.lock ./
RUN pixi install --locked --frozen

# Stage 2: Minimal runtime image
FROM debian:bookworm-slim AS runtime
WORKDIR /app

# Salin environment dari builder
COPY --from=builder /app/.pixi/envs/default /app/.pixi/envs/default

ENV PATH="/app/.pixi/envs/default/bin:$PATH"
ENV PYTHONPATH="/app/src"
ENV PYTHONUNBUFFERED=1

# Salin source code & vault data
COPY src ./src
COPY vault ./vault
COPY scripts ./scripts

EXPOSE 8000

# Healthcheck tanpa dependensi curl luar (memakai modul python bawaan)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "luco.api:app", "--host", "0.0.0.0", "--port", "8000"]

