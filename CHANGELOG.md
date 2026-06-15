# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

> **Next release target: `0.2.0` (minor bump, breaking under SemVer).**
> The next release tightens the public Python API: the `sql2json.parameter`
> date helpers (`is_number`, `first_day_month`, `first_day_year`,
> `last_day_month`, `last_day_year`, `parse_field`, `parse_formula`) become
> private and are no longer re-exported. `parse_parameter` remains the
> supported public entry point. `sql2json` is pre-1.0, so this ships as a
> minor bump with **no formal deprecation cycle**.
>
> This release includes API-boundary work: privatizing helpers, adding
> explicit `__all__` exports, and single-sourcing the package version via
> `importlib.metadata.version("sql2json")`.
>
> **Migration:** if you imported any of those date helpers from
> `sql2json.parameter`, switch to the public `parse_parameter` for
> date-variable resolution.

### Added
- Explicit `__all__` exports for the supported top-level Python API and `sql2json.parameter` surface.
- Python API documentation and runnable examples under `examples/python_api`.
- `--timezone` flag: accepts an IANA timezone name (e.g. `--timezone America/New_York`, `--timezone UTC`) and uses it when resolving `CURRENT_DATE`, `START_CURRENT_MONTH`, and all other date variables. Defaults to local system timezone (backward-compatible). An invalid timezone name produces a structured JSON error on stderr and a non-zero exit code.

### Changed
- Package version is now single-sourced from installed package metadata via `importlib.metadata.version("sql2json")`.
- `sql2json.parameter` now only exports the public `parse_parameter` entry point; lower-level date helper functions are private implementation details.

## [0.1.11] - 2026-05-16

### Added
- `--list-connections`: prints a JSON array of configured connection names and exits
- `--list-queries`: prints a JSON array of configured query names and exits
- `list_connections(config_path)` and `list_queries(config_path)` exported from the Python package
- Config file lookup now checks `./sql2json.json` and `./.sql2json/config.json` in the current directory before falling back to `~/.sql2json/config.json`
- Structured JSON error output on stderr (`{"error": "...", "type": "..."}`) when the CLI fails; stdout remains empty on error and exit code is non-zero

### Fixed
- SQLAlchemy 2.x compatibility: `row.keys()` replaced with `result_proxy.keys()` in row mapping
- `--config` kwarg is now popped before being forwarded to SQLAlchemy; previously it was incorrectly passed as a SQL bind parameter
- Build backend corrected from the non-existent `uv.build` to `hatchling`

### Changed
- AGENTS.md rewritten: removed references to non-existent `--description` and `--format dict` flags; added discovery, error handling, and Python API sections

## [0.1.10] - 2020-05-25

### Added
- Add support to write output to csv, excel or json file using --output sales.csv, --output sales.csv, --output sales.json
- New parameter output, the name of the file to write the data. With custom variables like --output Sales-{CURRENT_DATE-5}_{CURRENT_DATE+2}
- New parameter format(default=json). Values json, csv, excel
- Add examples to README.md for output, format

## [0.1.9] - 2020-01-19

### Added
- Support map column value as key, value ussing --key column1 --value column2
- Add README.md, improve documentation

### Removed
- README.rst

## [0.1.8] - 2020-01-18

### Added
- Support map column value as key, value ussing --key column1 --value column2
- New flag jsonkeys: coma separated columns to convert JSON functions result as JSON not as string

## [0.1.7] - 2020-01-04

### Added
- Support to read sql from external file using --query @FULL_PATH_TO_MY_FILE
- You can pass a custom config file as parameter --config. Ex. --config /Users/myuser/my-config.json

### Changed
- FIX to accept any parameter, not only date formulas
- Remove empty flag: true/false from response when user pass wrapper flag
