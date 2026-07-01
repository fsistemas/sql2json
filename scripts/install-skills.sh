#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
canonical="$repo_root/skills/sql2json/SKILL.md"

agents=(
  "hermes:$HOME/.hermes/skills/productivity/sql2json/SKILL.md"
  "claude:$HOME/.claude/skills/sql2json/SKILL.md"
  "pi:$HOME/.pi/agent/skills/sql2json/SKILL.md"
)

installed=()
skipped=()

for entry in "${agents[@]}"; do
  name="${entry%%:*}"
  target="${entry#*:}"
  base_dir="$(dirname "$(dirname "$target")")"

  if [[ -d "$base_dir" || -e "$base_dir" ]]; then
    mkdir -p "$(dirname "$target")"
    ln -sfn "$canonical" "$target"
    installed+=("$name")
  else
    skipped+=("$name")
  fi
done

printf 'installed: %s\n' "${installed[*]:-(none)}"
printf 'skipped: %s\n' "${skipped[*]:-(none)}"
printf 'canonical: %s\n' "$canonical"
