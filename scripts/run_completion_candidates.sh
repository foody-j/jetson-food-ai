#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

BASE_DIR="${HOME}/AI_Data"
OUT_DIR="${HOME}/jetson-food-ai/reports/completion_candidates"
DEVICE="cpu"
LABEL_MODE="candidate"

mkdir -p "${OUT_DIR}"

echo "[RUN] completion candidates export"
echo "  base_dir : ${BASE_DIR}"
echo "  out_dir  : ${OUT_DIR}"
echo "  device   : ${DEVICE}"
echo "  label    : ${LABEL_MODE}"

python3 "${SCRIPT_DIR}/export_completion_candidates.py" \
  --base-dir "${BASE_DIR}" \
  --out-dir "${OUT_DIR}" \
  --device "${DEVICE}" \
  --label-mode "${LABEL_MODE}"

echo ""
echo "[DONE] CSV:"
echo "  ${OUT_DIR}/completion_candidates.csv"
echo "[DONE] Open folder:"
echo "  ${OUT_DIR}"
