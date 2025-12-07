#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/broker/venv"
PYTHON_BIN="${VENV_DIR}/bin/python"
REQUIREMENTS_FILE="${ROOT_DIR}/broker/requirements.txt"

if [[ ! -d "${VENV_DIR}" ]]; then
  python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"
pip install --upgrade pip >/dev/null
pip install -r "${REQUIREMENTS_FILE}"

exec "${PYTHON_BIN}" -m broker.main "$@"
