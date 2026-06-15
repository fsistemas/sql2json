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

## Notes

- Build artifacts (`dist/`, `*.egg-info/`) are in `.gitignore` — never commit
  them.
- The build backend is **hatchling** (set in `pyproject.toml`). Do not use
  `python setup.py` or `setuptools` commands.
- Verify the published release at <https://pypi.org/project/sql2json/> and that
  `pip install sql2json==0.2.1` resolves the new version.
