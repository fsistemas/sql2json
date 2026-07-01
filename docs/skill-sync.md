# sql2json skill sync

Canonical skill source:

- `skills/sql2json/SKILL.md`

Supported agent skill locations:

- Hermes: `~/.hermes/skills/productivity/sql2json/SKILL.md`
- Claude: `~/.claude/skills/sql2json/SKILL.md`
- Pi: `~/.pi/agent/skills/sql2json/SKILL.md`

Refresh everything with:

```bash
./scripts/install-skills.sh
```

or, to force-link every configured target regardless of presence checks:

```bash
./scripts/sync-sql2json-skill.sh
```

Notes:

- The install script detects which global agent roots exist and only installs into those locations.
- The sync script force-refreshes all known targets and is useful after editing the canonical skill.
