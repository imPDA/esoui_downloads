FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends xz-utils && \
    rm -rf /var/lib/apt/lists/*

# RUN groupadd --system --gid 999 nonroot \
#  && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH="/app:$PYTHONPATH"

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_TOOL_BIN_DIR=/usr/local/bin

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

COPY ./src /app
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --group data-pipeline --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT []

# USER nonroot

CMD ["python", "data_pipeline/main.py"]