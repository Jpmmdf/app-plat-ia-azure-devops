#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_BIN="$ROOT_DIR/.venv/bin"
BUILD_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$BUILD_DIR"
}
trap cleanup EXIT

if [[ ! -x "$VENV_BIN/pywrangler" ]]; then
  echo "Erro: pywrangler não encontrado em $VENV_BIN" >&2
  echo "Instale com: $VENV_BIN/pip install workers-py uv" >&2
  exit 1
fi

export PATH="$VENV_BIN:$PATH"

echo "[1/3] Sincronizando dependências Python para Workers..."
(
  cd "$ROOT_DIR"
  pywrangler sync
)

echo "[2/3] Montando pacote de deploy limpo em $BUILD_DIR ..."
cp "$ROOT_DIR/server.py" "$BUILD_DIR/server.py"
cp "$ROOT_DIR/wrangler.toml" "$BUILD_DIR/wrangler.toml"
rsync -a "$ROOT_DIR/python_modules/" "$BUILD_DIR/python_modules/"

echo "[3/3] Publicando Worker..."
wrangler deploy --cwd "$BUILD_DIR"
