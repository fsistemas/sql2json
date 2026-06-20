# Official sql2json image.
#
# The package is installed from PyPI (not the working tree) so a tagged image
# always matches the published release of the same version. Pass
# `--build-arg VERSION=X.Y.Z` to pin a specific release; with no VERSION the
# latest release on PyPI is installed.
ARG PYTHON_VERSION=3.10-slim
FROM python:${PYTHON_VERSION}

ARG VERSION=

# PostgreSQL + MySQL/MariaDB drivers come from the package extras; SQLite is
# built into Python. `${VERSION:+==${VERSION}}` expands to `==X.Y.Z` only when
# VERSION is set, otherwise installs the latest release.
RUN pip install --no-cache-dir "sql2json[postgres,mysql]${VERSION:+==${VERSION}}"

LABEL org.opencontainers.image.title="sql2json" \
      org.opencontainers.image.description="Run SQL queries via SQLAlchemy and output JSON, CSV, or Excel." \
      org.opencontainers.image.source="https://github.com/fsistemas/sql2json" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}"

# Run as an unprivileged user. The home directory holds the config
# (`/home/app/.sql2json`) and `/workspace` is the writable working dir for
# `--output` files; both are owned by `app`.
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /workspace \
    && chown app:app /workspace
USER app
WORKDIR /workspace

ENTRYPOINT ["sql2json"]
