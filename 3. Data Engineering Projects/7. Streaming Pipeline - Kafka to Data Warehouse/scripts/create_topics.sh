#!/usr/bin/env bash
# Create (or re-create) the pipeline topics explicitly.
# Topic definitions live in src/setup/init_topics.py, not in a shell script.
set -euo pipefail
cd "$(dirname "$0")/.."

test -f .env || cp .env.example .env

if [[ "${1:-}" == "--delete" ]]; then
  docker compose run --rm topics-init src.setup.init_topics --delete
else
  docker compose run --rm topics-init src.setup.init_topics "$@"
fi
