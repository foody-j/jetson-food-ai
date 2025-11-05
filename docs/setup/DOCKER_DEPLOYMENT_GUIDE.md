# Docker Deployment Guide

Complete guide for deploying Jetson #1 Monitoring System with Docker

---

## 📋 Overview

This guide explains how to run the Jetson monitoring system (3 GMSL cameras) in a Docker container with GPU acceleration and GUI support.

**Benefits of Docker Deployment:**
- ✅ Isolated environment
- ✅ Easy deployment across multiple Jetson devices
- ✅ Dependency management
- ✅ Reproducible builds
- ✅ Easy rollback if issues occur

---

## 🔧 Prerequisites

### 1. Docker Installation

```bash
# Check if Docker is installed
docker --version
docker-compose --version

# If not installed, install Docker for Jetson
# (Should already be installed with JetPack)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# Add user to docker group (to run without sudo)
sudo usermod -aG docker $USER
# Logout and login for changes to take effect
```

### 2. NVIDIA Docker Runtime

```bash
# Check if NVIDIA runtime is configured
docker info | grep -i runtime

# Should show: nvidia

# If not, configure it:
sudo nano /etc/docker/daemon.json
```

Add:
```json
{
    "default-runtime": "nvidia",
    "runtimes": {
        "nvidia": {
            "path": "nvidia-container-runtime",
            "runtimeArgs": []
        }
    }
}
```

Then restart Docker:
```bash
sudo systemctl restart docker
```

### 3. X11 Display Access

```bash
# Grant Docker X11 access
xhost +local:docker
```

---

## 🚀 Quick Start

### Option 1: Using Convenience Script (Recommended)

```bash
cd ~/jetson-camera-monitor

# Run everything (loads drivers + starts container)
./docker-run.sh
```

**What it does:**
1. Enables X11 access for Docker
2. Loads GMSL drivers on host
3. Verifies camera devices
4. Builds Docker image
5. Starts container with GUI

### Option 2: Manual Steps

```bash
cd ~/jetson-camera-monitor

# 1. Enable X11
xhost +local:docker

# 2. Load GMSL drivers ON HOST (not in container!)
cd camera_autostart
sudo ./camera_driver_autoload.sh
cd ..

# 3. Build and start container
docker-compose up --build -d jetson-monitor

# 4. View logs
docker-compose logs -f jetson-monitor
```

---

## 📦 Docker Files Explanation

### 1. Dockerfile

Defines the container image:
- Base: NVIDIA JetPack 6.2 (r36.4.0)
- Installs: Python packages, YOLO, OpenCV, MQTT, Korean fonts
- Configures: GMSL driver loading, camera access
- Entry point: Automatically starts monitoring system

### 2. docker-compose.yml

Defines service configuration:
- **jetson-monitor**: Production monitoring service
  - Privileged mode (for GMSL drivers)
  - GPU access (NVIDIA runtime)
  - Camera device mapping
  - X11 display forwarding
  - Auto-restart on failure

- **ai-dev**: Development container (optional)
  - Interactive shell
  - Full project access

### 3. docker-run.sh

Convenience script that:
- Sets up X11
- Loads GMSL drivers
- Starts container
- Shows logs

---

## 🎯 Usage

### Starting the System

```bash
# Start monitoring system
docker-compose up -d jetson-monitor

# Start with rebuild (after code changes)
docker-compose up --build -d jetson-monitor

# Start and follow logs
docker-compose up jetson-monitor
```

### Viewing Logs

```bash
# Follow live logs
docker-compose logs -f jetson-monitor

# View last 50 lines
docker-compose logs --tail=50 jetson-monitor

# View logs with timestamps
docker-compose logs -t jetson-monitor
```

### Stopping the System

```bash
# Stop container (preserves data)
docker-compose stop jetson-monitor

# Stop and remove container
docker-compose down jetson-monitor

# Stop all services
docker-compose down
```

### Restarting

```bash
# Restart container
docker-compose restart jetson-monitor

# Restart with rebuild
docker-compose up --build -d jetson-monitor
```

### Shell Access

```bash
# Access running container
docker exec -it jetson1-monitoring /bin/bash

# Once inside:
cd /app/autostart_autodown
ls -l
python3 JETSON1_INTEGRATED.py  # Run manually
```

### Development Container

```bash
# Start development container (interactive)
docker-compose run --rm ai-dev

# Inside container:
cd /project
python3 autostart_autodown/JETSON1_INTEGRATED.py
```

---

## 🔍 Troubleshooting

### Problem: GUI doesn't appear

**Solution:**
```bash
# 1. Check DISPLAY variable
echo $DISPLAY  # Should be :0 or :1

# 2. Grant X11 access
xhost +local:docker

# 3. Restart container
docker-compose restart jetson-monitor
```

### Problem: No camera devices

**Solution:**
```bash
# 1. Check cameras on HOST (not in container)
ls -l /dev/video*

# 2. Load drivers on HOST
cd camera_autostart
sudo ./camera_driver_autoload.sh

# 3. Restart container
docker-compose restart jetson-monitor
```

### Problem: GMSL drivers not loading

**Solution:**
```bash
# Drivers MUST be loaded on HOST, not in container
# Container shares host kernel

# On HOST:
lsmod | grep -E "(max96712|gmsl2)"

# If not loaded:
cd ~/jetson-camera-monitor/camera_autostart
sudo ./camera_driver_autoload.sh

# Then restart container
docker-compose restart jetson-monitor
```

### Problem: Permission denied for camera

**Solution:**
```bash
# Check camera permissions on host
ls -l /dev/video*

# Should show group 'video'
# If not, add user to video group:
sudo usermod -aG video $USER

# Restart container
docker-compose restart jetson-monitor
```

### Problem: Container exits immediately

**Solution:**
```bash
# Check logs for errors
docker-compose logs jetson-monitor

# Common issues:
# - DISPLAY not set
# - Cameras not accessible
# - Python errors

# Run container in debug mode
docker-compose run --rm jetson-monitor /bin/bash
```

---

## 📁 Data Persistence

### Volume Mounts

Data is persisted through volume mounts in `docker-compose.yml`:

```yaml
volumes:
  # Recordings persist on host
  - ./autostart_autodown/Detection:/app/autostart_autodown/Detection
  - ./autostart_autodown/StirFry_Data:/app/autostart_autodown/StirFry_Data
```

**Data Location:**
- Host: `~/jetson-camera-monitor/autostart_autodown/Detection/`
- Host: `~/jetson-camera-monitor/autostart_autodown/StirFry_Data/`

**Even if container is removed, data remains on host!**

---

## 🔄 Updating the Application

### Method 1: Code Changes (No Rebuild)

Since code is mounted as a volume, changes are live:

```bash
# 1. Edit code on host
nano ~/jetson-camera-monitor/autostart_autodown/config.json

# 2. Restart container
docker-compose restart jetson-monitor

# Changes take effect immediately!
```

### Method 2: Rebuild Image

For dependency changes:

```bash
# Rebuild and restart
docker-compose up --build -d jetson-monitor
```

---

## 🏭 Production Deployment

### Auto-start on Boot

#### Option 1: Docker Compose (Recommended)

```bash
# 1. Edit docker-compose.yml
# Change: restart: unless-stopped
# To:     restart: always

# 2. Start container
docker-compose up -d jetson-monitor

# Container now auto-starts on boot
```

#### Option 2: Systemd Service

Create `/etc/systemd/system/jetson-docker.service`:

```ini
[Unit]
Description=Jetson Monitoring Docker Container
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/dkuyj/jetson-camera-monitor
ExecStartPre=/bin/bash -c 'xhost +local:docker'
ExecStartPre=/home/dkuyj/jetson-camera-monitor/camera_autostart/camera_driver_autoload.sh
ExecStart=/usr/bin/docker-compose up -d jetson-monitor
ExecStop=/usr/bin/docker-compose stop jetson-monitor
User=dkuyj

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable jetson-docker.service
sudo systemctl start jetson-docker.service
```

---

## 🧹 Maintenance

### Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove unused images
docker image prune

# Remove all unused Docker data
docker system prune -a
```

### View Resource Usage

```bash
# Check container stats
docker stats jetson1-monitoring

# View disk usage
docker system df
```

---

## 🎨 GUI Configuration

### Full Screen Mode

The GUI starts in full-screen by default. Press **Escape** to exit full-screen.

### Adjust Display

If GUI is too small/large:

Edit `autostart_autodown/JETSON1_INTEGRATED.py`:
```python
# Line ~78-79
WINDOW_WIDTH = 1280   # Adjust
WINDOW_HEIGHT = 720   # Adjust
```

Then restart:
```bash
docker-compose restart jetson-monitor
```

---

## 📊 Monitoring

### Health Check

```bash
# Check if container is running
docker ps | grep jetson1-monitoring

# Check camera status inside container
docker exec jetson1-monitoring ls -l /dev/video*

# Check GMSL drivers inside container
docker exec jetson1-monitoring lsmod | grep gmsl2
```

### Logs Location

```bash
# Docker logs
docker-compose logs jetson-monitor > monitoring.log

# Application logs (inside container)
docker exec jetson1-monitoring cat /app/autostart_autodown/app.log
```

---

## 🔐 Security Notes

- Container runs in **privileged mode** (required for GMSL drivers)
- Full `/dev` access (required for cameras)
- Host network mode (for MQTT and X11)
- Consider firewall rules if exposing MQTT

---

## 📚 Additional Resources

### Useful Commands

```bash
# Enter container shell
docker exec -it jetson1-monitoring /bin/bash

# Copy files from container
docker cp jetson1-monitoring:/app/autostart_autodown/Detection/ ./backup/

# View container details
docker inspect jetson1-monitoring

# Follow specific log stream
docker-compose logs -f jetson-monitor | grep "\[카메라\]"
```

### Docker Compose Commands

```bash
docker-compose up      # Start in foreground
docker-compose up -d   # Start in background (detached)
docker-compose stop    # Stop containers
docker-compose start   # Start stopped containers
docker-compose restart # Restart containers
docker-compose down    # Stop and remove containers
docker-compose ps      # List containers
docker-compose logs    # View logs
docker-compose build   # Rebuild images
```

---

## ❓ FAQ

### Q: Can I run without Docker?

Yes! See `autostart_autodown/install_autostart.sh` for native installation.

### Q: Will Docker slow down performance?

No. Docker on Linux has near-native performance, especially with GPU passthrough.

### Q: Can I access cameras from both host and container?

No. Camera devices can only be accessed by one process at a time. If the container is running, host can't access cameras directly.

### Q: How do I backup my data?

Data is stored on host filesystem:
```bash
tar -czf backup.tar.gz autostart_autodown/Detection autostart_autodown/StirFry_Data
```

---

## 🆘 Getting Help

1. **Check logs**: `docker-compose logs jetson-monitor`
2. **Test cameras**: `docker exec jetson1-monitoring ls -l /dev/video*`
3. **Verify drivers**: `lsmod | grep gmsl2` (on HOST)
4. **Check GUI**: `echo $DISPLAY`

---

**Version:** 1.0.0
**Last Updated:** 2025-11-03
