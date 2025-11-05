#!/bin/bash
# Quick temporary fixes (until Docker rebuild)

echo "=== Quick Fixes for Current Container ==="
echo ""

# Fix 1: Install Korean fonts
echo "1. Installing Korean fonts..."
apt update > /dev/null 2>&1
apt install -y fonts-nanum fonts-nanum-coding fonts-nanum-extra > /dev/null 2>&1
echo "   ✓ Korean fonts installed"

# Fix 2: Install Python packages
echo "2. Installing Python packages..."
pip3 install Pillow ultralytics paho-mqtt psutil > /dev/null 2>&1
echo "   ✓ Python packages installed"

# Fix 3: Fix Ultralytics config directory
echo "3. Fixing Ultralytics config directory..."
mkdir -p /root/.config/Ultralytics
chmod -R 777 /root/.config/Ultralytics
export YOLO_CONFIG_DIR=/root/.config/Ultralytics
echo "   ✓ Ultralytics config directory fixed"

echo ""
echo "=== All Quick Fixes Applied! ==="
echo ""
echo "Note: These fixes are temporary and will be lost on container restart."
echo "For permanent fixes, rebuild the Docker image with: docker compose build"
echo ""
