#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LLAMA_DIR="${ROOT_DIR}/llama_cpp"
BUILD_DIR="${LLAMA_DIR}/build"

if [[ ! -d "${LLAMA_DIR}" ]]; then
  echo "llama_cpp directory not found. Initialize the submodule first." >&2
  exit 1
fi

GPU_FLAG="-DLLAMA_CUBLAS=OFF"
if command -v nvidia-smi >/dev/null 2>&1 || command -v nvcc >/dev/null 2>&1; then
  GPU_FLAG="-DLLAMA_CUBLAS=ON"
fi

cmake -S "${LLAMA_DIR}" -B "${BUILD_DIR}" ${GPU_FLAG} -DLLAMA_BUILD_EXAMPLES=ON
cmake --build "${BUILD_DIR}" --target main -- -j"$(nproc)"

echo "llama.cpp built successfully. Binary located at ${BUILD_DIR}/bin/main"
