#!/usr/bin/env bash
set -u

# Export bucket inference visualization images for all sessions.
# Uses existing test_bucket_detection_simulation.py auto-all mode.

ROOT="/home/yjk/jetson-food-ai"
SIM="$ROOT/jetson2_frying_ai/test_bucket_detection_simulation.py"
CFG="$ROOT/jetson2_frying_ai/config_jetson2_web.json"
OUT_BASE="${1:-$ROOT/reports/bucket_vis_all}"
DEVICE="${DEVICE:-cuda}"
MAX_IMAGES="${MAX_IMAGES:-0}"   # 0 = all

mkdir -p "$OUT_BASE/pot1_left" "$OUT_BASE/pot2_right"

echo "[INFO] pot1(left) export start"
python3 "$SIM" \
  --auto-all \
  --base-dir "/home/yjk/AI_Data/pot1" \
  --auto-sides left \
  --config "$CFG" \
  --device "$DEVICE" \
  --max-images "$MAX_IMAGES" \
  --save-vis "$OUT_BASE/pot1_left"

echo "[INFO] pot2(right) export start"
python3 "$SIM" \
  --auto-all \
  --base-dir "/home/yjk/AI_Data/pot2" \
  --auto-sides right \
  --config "$CFG" \
  --device "$DEVICE" \
  --max-images "$MAX_IMAGES" \
  --save-vis "$OUT_BASE/pot2_right"

echo "[DONE] output=$OUT_BASE"

