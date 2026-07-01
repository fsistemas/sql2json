# sql2json workflow overlay

Read `WORKFLOW.md` first, then apply this sql2json-specific overlay.

## Project configuration

- Board project key: `S2J`
- Base branch: `master`
- Branch format: `feature/S2J-N`
- Public repository: keep commits, PR bodies, and checked-in docs public-safe.
- Release targets: PyPI package `sql2json` and Docker Hub image
  `docker.io/fsistemas/sql2json` (`linux/amd64` + `linux/arm64`).

## Branches, commits, and PRs

- Start every task from a clean, synced `master`.
- Use one branch and one PR per board issue.
- Branch names use only the issue identifier, for example `feature/S2J-2`.
- Prefer concise conventional commits:
  - `feat: add query discovery`
  - `fix: handle CSV output path`
  - `docs: update release workflow`
  - `test: add integration coverage`
  - `chore: bump version to 0.3.2`
- Do not add agent attribution, generated-by footers, or private board details to
  commits or PR bodies.

## Validation gates

Choose the smallest gate that proves the change, but do not skip required gates
when code paths change.

### Docs-only changes

```bash
uv run pytest
```

For shell-script docs or script changes, also run:

```bash
bash -n scripts/<script>.sh
```

### Python code changes

```bash
uv run --extra dev black --check .
uv run --extra dev flake8
uv run --extra dev mypy
uv run --extra dev pytest --cov
```

### Database behavior changes

Run the Python code gates plus the real-database integration suite:

```bash
uv run --extra dev --extra integration pytest -m integration tests/integration
```

If local container tooling is not available, use the wrapper that provisions a
compose stack when appropriate:

```bash
./scripts/test-integration.sh
```

### CLI/output behavior changes

Add or update unit tests for the CLI contract and run at least:

```bash
uv run pytest tests/test_cli.py tests/test_output_files.py tests/test_transformations.py
```

Run the full Python gate before opening the PR when practical.

### Docker changes

Run the relevant tests and a local image smoke test. The Dockerfile installs
`sql2json` from PyPI, so pass a published version when verifying release-image
behavior:

```bash
podman build --platform linux/amd64 --pull=always --build-arg VERSION=0.3.1 -t sql2json-test .
podman run --rm sql2json-test --query "SELECT 1 AS a, 2 AS b"
```

Use `docker` equivalents if Docker is the available container runtime.

## Release discipline

Releases are maintainer-only. External contributors and agents should not bump
versions, create tags, publish to PyPI, or publish Docker images unless the
maintainer explicitly asks for release work.

When release work is requested, follow `RELEASING.md` exactly:

1. Bump `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Run the full quality gates.
4. Commit the release metadata.
5. Tag with a `v` prefix, for example `v0.3.2`.
6. Push the commit and tag to `master`.
7. Build and publish to PyPI with `uv build` / `uv publish`.
8. Publish Docker Hub images only after the PyPI version exists.
9. Push immutable Docker tag `X.Y.Z`; move `latest` only for stable releases.
10. Verify the pushed image runs and reports the expected package version.

For Docker Hub, preserve multi-architecture support (`linux/amd64` and
`linux/arm64`) whenever publishing a stable release. Treat published PyPI and
Docker version tags as immutable.

## sql2json safety reminders

- The CLI executes arbitrary SQL and commits writes by default.
- Use `--read-only` for exploratory or agent-driven database inspection unless a
  write is explicitly intended.
- Tests should use in-memory SQLite, temporary files, testcontainers, or the
  documented integration stack — never a real user database.
- Keep `AGENTS.md`, `README.md`, `CLAUDE.md`, and `skills/sql2json/SKILL.md`
  aligned when changing public CLI behavior.
