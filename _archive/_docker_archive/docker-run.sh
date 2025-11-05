#!/bin/bash
#
# Docker startup script for Jetson #1 Monitoring System
# Handles X11 setup and GMSL driver loading
#

set -e

echo "=========================================="
echo "Jetson #1 Monitoring - Docker Startup"
echo "=========================================="
echo ""

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "⚠️  Warning: This doesn't appear to be a Jetson device"
fi

# Step 1: Enable X11 access for Docker
echo "[1/4] Setting up X11 access..."
xhost +local:docker || {
    echo "⚠️  Warning: xhost command failed. GUI may not work."
}

# Step 2: Load GMSL drivers on HOST (must be done before container starts)
echo "[2/4] Loading GMSL drivers on host..."
if ! lsmod | grep -q "max96712"; then
    echo "   GMSL drivers not loaded. Loading now..."
    cd camera_autostart
    sudo ./camera_driver_autoload.sh || {
        echo "❌ Error: Failed to load GMSL drivers"
        echo "   Please check driver files and permissions"
        exit 1
    }
    cd ..
    echo "   ✅ GMSL drivers loaded successfully"
else
    echo "   ✅ GMSL drivers already loaded"
fi

# Step 3: Verify camera devices
echo "[3/4] Verifying camera devices..."
if ls /dev/video* 1> /dev/null 2>&1; then
    ls -l /dev/video* | head -n 4
    echo "   ✅ Camera devices found"
else
    echo "   ⚠️  Warning: No camera devices found!"
fi

# Step 4: Detect docker-compose version
echo "[4/4] Starting Docker container..."
echo ""

# Detect if docker-compose (v1) or docker compose (v2) is available
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
    echo "   Using docker-compose (v1)"
elif docker compose version &> /dev/null; then
    COMPOSE_CMD="docker compose"
    echo "   Using docker compose (v2)"
else
    echo "❌ Error: Neither 'docker-compose' nor 'docker compose' found!"
    echo ""
    echo "Please install Docker Compose:"
    echo "   sudo apt-get install docker-compose"
    echo ""
    echo "Or use Docker Compose v2 (plugin):"
    echo "   Already installed with recent Docker versions"
    exit 1
fi

# Build and start container
$COMPOSE_CMD up --build -d jetson-monitor

# Show logs
echo ""
echo "=========================================="
echo "✅ Container started successfully!"
echo "=========================================="
echo ""
echo "📖 Useful commands:"
echo "   View logs:      $COMPOSE_CMD logs -f jetson-monitor"
echo "   Stop container: $COMPOSE_CMD stop jetson-monitor"
echo "   Restart:        $COMPOSE_CMD restart jetson-monitor"
echo "   Shell access:   docker exec -it jetson1-monitoring /bin/bash"
echo ""
echo "📺 GUI should appear on your display"
echo "   If GUI doesn't show, check: echo \$DISPLAY"
echo ""
echo "🎥 Cameras:"
echo "   video0: Human surveillance (CN4)"
echo "   video1: Stir-fry LEFT (CN5)"
echo "   video2: Stir-fry RIGHT (CN6)"
echo ""

# Follow logs
echo "Press Ctrl+C to stop following logs (container will keep running)"
echo ""
$COMPOSE_CMD logs -f jetson-monitor
