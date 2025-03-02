# A multi-stage image build to create a final image without uv.
ARG NODE_ENV=development
# First, build the application in the `/app` directory.
# See `Dockerfile` for details.
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
# Disable Python downloads, because we want to use the system interpreter
# across both images. If using a managed Python version, it needs to be
# copied from the build image into the final image; see `standalone.Dockerfile`
# for an example.
ENV UV_PYTHON_DOWNLOADS=0

WORKDIR /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev
ADD . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Then, use a final image without uv
FROM python:3.13-slim-bookworm AS base
# It is important to use the image that matches the builder, as the path to the
# Python executable must be the same, e.g., using `python:3.11-slim-bookworm`
# will fail.

# Install curl to check health in docker compose
RUN apt-get update && apt-get install -y curl

RUN groupadd -r app_group && useradd -r -g app_group app_user
USER app_user
COPY --from=builder --chown=app_user:app_group /app/.venv /app/.venv
COPY --from=builder --chown=app_user:app_group /app/app /app/uv.lock /app/

FROM base AS final-development
CMD ["fastapi", "dev", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS final-production
CMD ["fastapi", "run", "--host", "0.0.0.0", "--port", "8000"]

FROM final-${NODE_ENV} AS final
# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"
WORKDIR /app
EXPOSE 8000
