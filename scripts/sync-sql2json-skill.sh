#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
canonical="$repo_root/skills/sql2json/SKILL.md"

targets=(
  "$HOME/.hermes/skills/productivity/sql2json/SKILL.md"
  "$HOME/.claude/skills/sql2json/SKILL.md"
  "$HOME/.pi/agent/skills/sql2json/SKILL.md"
)

for target in "${targets[@]}"; do
  mkdir -p "$(dirname "$target")"
  ln -sfn "$canonical" "$target"
done

printf 'synced %s\n' "$canonical"
printf '  -> %s\n' "${targets[@]}"
