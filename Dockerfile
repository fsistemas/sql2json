# Official sql2json image.
#
# The package is installed from PyPI (not the working tree) so a tagged image
# always matches the published release of the same version. Pass
# `--build-arg VERSION=X.Y.Z` to pin a specific release; with no VERSION the
# latest release on PyPI is installed.
#
# Notes:
#   * Alpine base — small footprint (~99 MB image).
#   * Multi-stage build — the compiler toolchain (psycopg2 has no musl wheel and
#     is built from source) stays in the builder stage and never reaches the
#     runtime image, keeping it minimal.
#   * Runs as an unprivileged user.
ARG PYTHON_VERSION=3.13-alpine

# --- Builder: compile psycopg2 and install the package into a venv -----------
FROM python:${PYTHON_VERSION} AS builder

ARG VERSION=

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# psycopg2-binary ships only glibc (manylinux) wheels, so on Alpine/musl it is
# built from source — that needs a C toolchain and the libpq headers. PyMySQL is
# pure Python and SQLite is built into Python, so no other build deps are needed.
RUN apk add --no-cache build-base postgresql-dev

# `${VERSION:+==${VERSION}}` expands to `==X.Y.Z` only when VERSION is set,
# otherwise installs the latest release.
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install "sql2json[postgres,mysql]${VERSION:+==${VERSION}}"

# --- Runtime: minimal Alpine carrying only the venv and libpq ----------------
FROM python:${PYTHON_VERSION} AS runtime

ARG VERSION=

# libpq is the only runtime shared library psycopg2 needs; the build toolchain
# is intentionally left behind in the builder stage.
RUN apk add --no-cache libpq

LABEL org.opencontainers.image.title="sql2json" \
      org.opencontainers.image.description="Run SQL queries via SQLAlchemy and output JSON, CSV, or Excel." \
      org.opencontainers.image.source="https://github.com/fsistemas/sql2json" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}"

# Copy the ready-to-run virtualenv from the builder and put it first on PATH so
# `sql2json` (and `pip`, for the release verify step) resolve from it.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Run as an unprivileged user. The home directory holds the config
# (`/home/app/.sql2json`) and `/workspace` is the writable working dir for
# `--output` files; both are owned by `app`.
RUN adduser -D -u 1000 app \
    && mkdir -p /workspace \
    && chown app:app /workspace
USER app
WORKDIR /workspace

ENTRYPOINT ["sql2json"]
