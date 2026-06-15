# Security Policy

## Supported versions

`sql2json` is pre-1.0 (`0.x`). Security fixes are applied to the latest released
version only. Please upgrade to the most recent release before reporting an
issue.

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
pull requests, or discussions.**

Instead, use [GitHub's private vulnerability reporting](https://github.com/fsistemas/sql2json/security/advisories/new)
(the **"Report a vulnerability"** button under the repository's **Security**
tab). This opens a private advisory visible only to the maintainer.

When reporting, please include:

- A description of the issue and its impact.
- Steps to reproduce, or a proof of concept.
- The `sql2json` version and your environment (OS, Python version, database driver).

You can expect an initial acknowledgement within a reasonable timeframe. This is
a small, maintainer-run project, so please be patient. Once a fix is available,
the maintainer will coordinate disclosure with you.

## Security model — what you are responsible for

`sql2json` is a thin wrapper that executes the SQL it is given against a
database you configure. Understanding the trust boundary is essential to using
it safely.

### SQL execution risk

- **The tool executes whatever SQL it receives.** Inline SQL passed via
  `--query`, SQL loaded from `@/path/file.sql`, and named queries from your
  config are all run as-is. There is no allow-list, sandbox, or read-only
  enforcement.
- **Bind parameters are parameterized, but the query text is not.** Values
  passed as `--<param>` flags are bound safely as SQL parameters (`:param`).
  However, the query string itself is fully under the caller's control — never
  build a query string from untrusted input and pass it to `--query`.
- **Restrict at the database layer.** If you need read-only access, connect with
  a database user that only has `SELECT` privileges. `sql2json` will not stop a
  privileged connection from running `DELETE`, `DROP`, or `UPDATE`.
- **Prefer named queries** from your config file over inline SQL when exposing
  the tool to automation or agents — it limits the SQL surface to queries you
  have reviewed.

### Credential handling

- **Connection strings contain credentials.** Config files
  (`~/.sql2json/config.json` and the lookup-order alternatives) and raw
  SQLAlchemy URLs passed via `--name` may embed usernames and passwords. Treat
  these files as secrets: restrict their permissions and keep them out of
  version control.
- **The demo credentials are for local Docker only.** The `demo`/`demo` (and
  MySQL `root`) credentials in `docker-compose.yml`, `docker/config.json`, and
  the README exist solely for the local demo stack, whose ports bind to
  `127.0.0.1`. Never reuse them for any reachable database.
- **Be careful with shell history and logs.** Passing a connection URL inline
  via `--name` can leak it into shell history, process listings, and CI logs.
  Prefer a config file with appropriate file permissions.

### Untrusted output

- Query results are serialized to JSON/CSV/Excel as-is. If results contain
  attacker-controlled content, treat the output as untrusted when feeding it
  into downstream systems (spreadsheets, dashboards, shells).
