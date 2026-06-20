# Releasing sql2json

**This is a maintainer-only process.** Releases to [PyPI](https://pypi.org/project/sql2json/)
are published exclusively by the project maintainer. External contributors are
welcome to open issues and pull requests, but cutting and publishing a release
(version bumps, tags, and PyPI uploads) is reserved for the maintainer.

If you are a contributor and believe a release is warranted, open an issue
requesting one rather than bumping the version yourself.

## Prerequisites (maintainer)

- Push access to `master` and permission to create tags.
- A PyPI account with upload rights to the `sql2json` project, and a token
  configured via `UV_PUBLISH_TOKEN` or `~/.pypirc`.
- `uv` installed locally.

## Checklist

1. **Bump the version** in `pyproject.toml`:

   ```toml
   version = "0.2.1"
   ```

   `sql2json` is pre-1.0 and follows [Semantic Versioning](https://semver.org/)
   with the pre-1.0 convention that **breaking changes ship in a minor bump**
   (e.g. `0.2.x → 0.3.0`), not a major. The version is single-sourced: the
   package reads it at runtime via `importlib.metadata.version("sql2json")`, so
   `pyproject.toml` is the only place to edit.

2. **Update `CHANGELOG.md`** — move the `[Unreleased]` entries into a new dated
   `[0.2.1]` section at the top, following
   [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format.

3. **Run the full quality gates** (everything CI enforces):

   ```bash
   uv run --extra dev black --check .
   uv run --extra dev flake8
   uv run --extra dev mypy
   uv run --extra dev pytest --cov
   ```

4. **Commit** the version bump and changelog:

   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "chore: bump version to 0.2.1"
   ```

5. **Tag** (always prefix with `v`):

   ```bash
   git tag v0.2.1
   ```

6. **Push the commit and tag together**:

   ```bash
   git push origin master --tags
   ```

7. **Build and publish to PyPI**:

   ```bash
   uv build      # produces dist/sql2json-0.2.1.tar.gz and the wheel
   uv publish    # uploads to PyPI
   ```

8. **Publish the Docker image** to
   [`docker.io/fsistemas/sql2json`](https://hub.docker.com/r/fsistemas/sql2json).

   This runs from your local machine — it is **not** wired into CI. The image
   installs `sql2json==<version>` from PyPI, so it must run **after** step 7 (the
   version has to exist on PyPI first). Both Podman and Docker are shown; either
   works.

   First, log in to Docker Hub once (use a Docker Hub
   [access token](https://hub.docker.com/settings/security) as the password,
   not your account password):

   ```bash
   podman login docker.io   # username: fsistemas
   # or: docker login docker.io
   ```

   **One-time setup for cross-arch builds.** Building a non-native architecture
   (e.g. `linux/arm64` on an `amd64` host) requires `qemu-user-static`
   registered as kernel `binfmt_misc` handlers. This is a **host-level** change
   that needs real root — running the `tonistiigi/binfmt` installer inside a
   *rootless* container does **not** work (the registration can't reach the host
   kernel, and the build fails with `exec /bin/sh: Exec format error`). Install
   it once with your distro package or as root:

   ```bash
   # Arch / Manjaro:
   sudo pacman -S qemu-user-static qemu-user-static-binfmt
   # Debian / Ubuntu:
   sudo apt install qemu-user-static binfmt-support
   # Or, as real root (not rootless), the portable installer:
   sudo podman run --rm --privileged docker.io/tonistiigi/binfmt --install arm64
   # Verify the handler is registered on the host:
   ls /proc/sys/fs/binfmt_misc/ | grep qemu-aarch64
   ```

   **Podman** (multi-arch via a manifest list):

   ```bash
   podman manifest create docker.io/fsistemas/sql2json:0.2.1
   podman build --platform linux/amd64,linux/arm64 \
     --build-arg VERSION=0.2.1 \
     --manifest docker.io/fsistemas/sql2json:0.2.1 .
   podman manifest push docker.io/fsistemas/sql2json:0.2.1 \
     docker.io/fsistemas/sql2json:0.2.1
   # Stable releases only — also publish the moving `latest` tag:
   podman manifest push docker.io/fsistemas/sql2json:0.2.1 \
     docker.io/fsistemas/sql2json:latest
   ```

   **amd64-only fallback** (if qemu/arm64 emulation isn't available): publish a
   single-arch image instead — still useful for most servers and CI. Re-publish
   as multi-arch once the host is set up. Pass `--platform linux/amd64
   --pull=always` to force the correct base image (see the cached-arch gotcha
   below):

   ```bash
   podman build --platform linux/amd64 --pull=always --build-arg VERSION=0.2.1 \
     -t docker.io/fsistemas/sql2json:0.2.1 \
     -t docker.io/fsistemas/sql2json:latest .
   podman push docker.io/fsistemas/sql2json:0.2.1
   podman push docker.io/fsistemas/sql2json:latest   # stable releases only
   ```

   > **Cached-arch base-image gotcha.** After a cross-arch / multi-arch build
   > attempt, your local image store can hold a *non-native* base image (e.g. an
   > `arm64` `python:3.10-slim` pulled during an `--platform linux/arm64`
   > experiment). Podman will silently reuse that cached base for a subsequent
   > plain `podman build`, producing an image that fails to run with
   > `exec /bin/sh: Exec format error` and a build-time warning like
   > `image platform (linux/arm64/v8) does not match the expected platform
   > (linux/amd64)`. Always build with an explicit `--platform` **and**
   > `--pull=always` so the correct base image is fetched rather than reusing the
   > wrong cached one. To inspect what's cached: `podman images --format
   > '{{.Repository}}:{{.Tag}} {{.Arch}}'`.

   **Docker** (`buildx` equivalent):

   ```bash
   docker buildx build --platform linux/amd64,linux/arm64 \
     --build-arg VERSION=0.2.1 \
     -t docker.io/fsistemas/sql2json:0.2.1 \
     -t docker.io/fsistemas/sql2json:latest \
     --push .
   ```

   **Tagging rules:** push the immutable `:0.2.1` tag every release; move
   `:latest` **only** for stable releases (never for pre-releases / RCs). Treat
   published version tags as write-once.

   **Verify** the pushed image (either tool):

   ```bash
   podman pull docker.io/fsistemas/sql2json:0.2.1
   podman run --rm docker.io/fsistemas/sql2json:0.2.1 --query "SELECT 1 AS a, 2 AS b"
   # → [{"a": 1, "b": 2}]
   podman run --rm --entrypoint pip docker.io/fsistemas/sql2json:0.2.1 \
     show sql2json | grep ^Version   # must read: Version: 0.2.1
   ```

## Notes

- Build artifacts (`dist/`, `*.egg-info/`) are in `.gitignore` — never commit
  them.
- The build backend is **hatchling** (set in `pyproject.toml`). Do not use
  `python setup.py` or `setuptools` commands.
- Verify the published release at <https://pypi.org/project/sql2json/> and that
  `pip install sql2json==0.2.1` resolves the new version.
