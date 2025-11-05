#!/bin/bash
set -e

echo "[Docker] Jetson #1 Monitoring System Starting..."
echo "[Docker] Host: $(hostname)"
echo "[Docker] Date: $(date)"
echo ""

# Fix X11 permissions
echo "[Docker] Checking X11 configuration..."
if [ -n "$DISPLAY" ]; then
    echo "[OK] DISPLAY=$DISPLAY"
    if [ -n "$XAUTHORITY" ] && [ -f "$XAUTHORITY" ]; then
        echo "[OK] XAUTHORITY=$XAUTHORITY (exists)"
    else
        echo "[WARNING] XAUTHORITY file not found: $XAUTHORITY"
        echo "[ERROR] Run 'bash setup_x11.sh' on host before starting container!"
        exit 1
    fi
else
    echo "[WARNING] DISPLAY not set!"
fi
echo ""

# Check if GMSL drivers are already loaded on host
echo "[Docker] Checking GMSL drivers..."
if lsmod | grep -q "max96712"; then
    echo "[OK] GMSL drivers already loaded on host"
    ls -l /dev/video* 2>/dev/null || echo "[WARN] Camera devices not yet initialized"
else
    echo "[INFO] GMSL drivers not loaded yet"
    echo "[INFO] GMSLDriverManager will load drivers when JETSON1_INTEGRATED.py starts"
fi

echo ""
echo "[Docker] Starting JETSON1_INTEGRATED.py..."
echo "[INFO] Application will:"
echo "  1. Load GMSL drivers (if not already loaded)"
echo "  2. Initialize 3 GMSL cameras (/dev/video0, video1, video2)"
echo "  3. Start monitoring system"

# Change to application directory
cd /app/autostart_autodown || exit 1

exec python3 JETSON1_INTEGRATED.py
