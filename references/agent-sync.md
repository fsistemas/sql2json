# Agent sync map for sql2json

This repository keeps the canonical sql2json skill in:

- `skills/sql2json/SKILL.md`

The matching agent targets are:

- Hermes: `~/.hermes/skills/productivity/sql2json/SKILL.md`
- Claude: `~/.claude/skills/sql2json/SKILL.md`

Use `scripts/install-skills.sh` when you want a friendly install that only links into agent roots that are present.
Use `scripts/sync-sql2json-skill.sh` when you want to force-refresh every configured target.
