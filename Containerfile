# Dev container for the platform-service Django stack.
# Holds Python + uv + a few CLI conveniences; your code is bind-mounted at runtime.
FROM python:3.12-slim

# CLI conveniences: git/make for the workflow, curl + ca-certs, psql client for debugging.
# psycopg[binary] ships its own libpq, so no build toolchain is needed here.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        git \
        make \
        postgresql-client \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Bring in uv from the official image (pinned by digest-less tag; fine for a dev box).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Keep the virtualenv OUTSIDE the bind-mounted workspace so it never touches the host
# tree and never mixes host/container platforms.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /workspace

# Idle by default; you exec into it (make sh) or run server/worker via compose commands.
CMD ["sleep", "infinity"]
