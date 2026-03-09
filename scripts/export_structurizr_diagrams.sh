#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORKSPACE_DSL="${ROOT_DIR}/docs/structurizr/workspace.dsl"
OUTPUT_DIR="${ROOT_DIR}/docs/diagrams/structurizr"

if ! command -v structurizr-cli >/dev/null 2>&1; then
  echo "structurizr-cli nao encontrado no PATH."
  exit 1
fi

mkdir -p "${OUTPUT_DIR}"

structurizr-cli export \
  -w "${WORKSPACE_DSL}" \
  -f mermaid \
  -o "${OUTPUT_DIR}"

echo "Diagramas exportados em: ${OUTPUT_DIR}"
