#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="${MODELS_DIR:-${ROOT_DIR}/models}"
MODEL_NAME="${1:-phi-3-mini-4k-instruct-q4.gguf}"
MODEL_URL="${MODEL_URL:-https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf/resolve/main/Phi-3-mini-4k-instruct-q4.gguf}"

mkdir -p "${MODELS_DIR}"
TARGET_PATH="${MODELS_DIR}/${MODEL_NAME}"

if [[ -f "${TARGET_PATH}" ]]; then
  echo "Model already present at ${TARGET_PATH}"
  exit 0
fi

echo "Downloading ${MODEL_NAME}..."
curl -L -o "${TARGET_PATH}" "${MODEL_URL}"
echo "Model saved to ${TARGET_PATH}"
