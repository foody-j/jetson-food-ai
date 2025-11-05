# GMSL Camera Migration Guide

This guide explains how to migrate from USB cameras to GMSL cameras in the Jetson monitoring system.

---

## Table of Contents

1. [Overview](#overview)
2. [Camera Types Supported](#camera-types-supported)
3. [GMSL Camera Setup](#gmsl-camera-setup)
4. [Configuration](#configuration)
5. [Migration Steps](#migration-steps)
6. [Troubleshooting](#troubleshooting)

---

## Overview

The Jetson monitoring system now supports **both USB and GMSL cameras** with automatic driver loading and configuration.

**Key Features:**
- ✅ Universal camera abstraction (USB + GMSL)
- ✅ Automatic GMSL driver loading
- ✅ Automatic resolution configuration
- ✅ Auto-start on boot (systemd service)
- ✅ Easy switching between camera types via configuration

---

## Camera Types Supported

### USB Cameras
- Standard V4L2 USB cameras
- Plug-and-play, no driver installation needed
- Lower resolution, lower cost
- Example: Logitech webcams, generic USB cameras

### GMSL Cameras (SENSING)
- High-resolution automotive cameras
- Requires kernel module installation
- Higher performance, higher resolution
- GMSL2/3G and GMSL2/6G support
- Up to 4 cameras simultaneously

**GMSL Camera Specifications:**
- **GMSL Mode 0**: Legacy GMSL
- **GMSL Mode 1**: GMSL2/6G (6Gbps)
- **GMSL Mode 2**: GMSL2/3G (3Gbps) - Default

**Resolution Modes:**
- Mode 0: 1920x1080 (Full HD)
- Mode 1: 1920x1536 (3:2 aspect ratio) - **Default**
- Mode 2: 2880x1860 (High resolution)
- Mode 3: 3840x2160 (4K)
- Mode 4: 1280x720 (HD)

---

## GMSL Camera Setup

### Prerequisites

1. **Hardware:**
   - Jetson Orin Nano / AGX Orin
   - SENSING GMSL2 cameras (up to 4)
   - GMSL deserializer board (MAX96712)

2. **Software:**
   - Ubuntu 20.04/22.04 for Jetson
   - JetPack 6.2 or later
   - SENSING camera drivers in: `SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/`

3. **Python Packages:**
   ```bash
   pip3 install opencv-python pillow ultralytics paho-mqtt
   sudo apt install v4l-utils  # Required for GMSL cameras
   ```

### Driver Files

The GMSL drivers are located in:
```
/home/dkuyj/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/
└── ko/
    ├── max96712.ko          # Deserializer driver
    └── sgx-yuv-gmsl2.ko     # Camera driver
```

**These drivers are automatically loaded by the monitoring system** when GMSL cameras are configured.

---

## Configuration

### Main Configuration File

Edit `autostart_autodown/config.json`:

```json
{
  "camera_type": "gmsl",          // "usb" or "gmsl"
  "camera_index": 0,              // Camera device index (0-3 for GMSL)
  "camera_resolution": {
    "width": 1920,
    "height": 1536
  },
  "camera_fps": 30,
  "gmsl_mode": 2,                 // 0=GMSL, 1=GMSL2/6G, 2=GMSL2/3G
  "gmsl_resolution_mode": 1,      // 0-4 (see resolution modes above)
  "gmsl_driver_dir": "/home/dkuyj/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3",

  // Stir-fry camera (Camera 2)
  "stirfry_camera_type": "gmsl",
  "stirfry_camera_index": 1,
  "stirfry_gmsl_mode": 2,
  "stirfry_gmsl_resolution_mode": 1,

  // ... other settings ...
}
```

### Camera Type Switching

To switch from USB to GMSL:

```json
// Before (USB):
{
  "camera_type": "usb",
  "camera_index": 0
}

// After (GMSL):
{
  "camera_type": "gmsl",
  "camera_index": 0,
  "gmsl_mode": 2,
  "gmsl_resolution_mode": 1
}
```

---

## Migration Steps

### Step 1: Update Configuration

Edit `autostart_autodown/config.json`:

```bash
cd ~/jetson-camera-monitor/autostart_autodown
nano config.json
```

Change:
- `"camera_type": "usb"` → `"camera_type": "gmsl"`
- Add `"gmsl_mode": 2`
- Add `"gmsl_resolution_mode": 1`

### Step 2: Install System Service

Run the installation script:

```bash
cd ~/jetson-camera-monitor/autostart_autodown
./install_autostart.sh
```

This will:
- ✅ Check and install v4l-utils
- ✅ Install systemd service
- ✅ Enable auto-start on boot
- ✅ Optionally start the service now

### Step 3: Verify Installation

Check service status:

```bash
sudo systemctl status jetson-monitor.service
```

View live logs:

```bash
sudo journalctl -u jetson-monitor.service -f
```

### Step 4: Test Camera

The monitoring system will automatically:
1. Load GMSL drivers on startup
2. Configure camera resolution
3. Start monitoring and YOLO detection

Check for successful initialization in logs:
```
[GMSL] Loading drivers from ...
[GMSL] max96712.ko loaded successfully
[GMSL] sgx-yuv-gmsl2.ko loaded successfully
[카메라] 자동 ON/OFF 카메라 초기화 완료: GMSL #0
```

---

## Troubleshooting

### Issue: "Camera device not found"

**Symptoms:**
```
[ERROR] /dev/video0 not found
```

**Solutions:**
1. Check physical connections
2. Verify drivers are loaded:
   ```bash
   lsmod | grep -E "(max96712|gmsl2)"
   ```
3. Manually load drivers:
   ```bash
   cd ~/jetson-camera-monitor/camera_autostart
   ./camera_driver_autoload.sh
   ```

### Issue: "Failed to load GMSL drivers"

**Symptoms:**
```
[ERROR] Failed to load GMSL drivers
```

**Solutions:**
1. Check driver files exist:
   ```bash
   ls -l ~/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko/
   ```
2. Check permissions:
   ```bash
   sudo chmod 644 ~/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko/*.ko
   ```
3. Check kernel compatibility:
   ```bash
   uname -r  # Should match driver version
   ```

### Issue: "v4l2-ctl not found"

**Symptoms:**
```
[WARN] v4l2-ctl not found
```

**Solution:**
```bash
sudo apt update
sudo apt install v4l-utils
```

### Issue: Black screen / No video

**Symptoms:**
- Camera opens but shows black screen
- No frames received

**Solutions:**
1. Check NVCSI clock configuration:
   ```bash
   cat /sys/kernel/debug/bpmp/debug/clk/nvcsi/rate
   # Should show: 214300000
   ```
2. Verify camera power:
   ```bash
   v4l2-ctl --list-devices
   ```
3. Try different resolution mode in config.json

### Issue: Service fails to start

**Symptoms:**
```
sudo systemctl status jetson-monitor.service
● jetson-monitor.service - Jetson #1 Integrated Monitoring System
   Loaded: loaded
   Active: failed
```

**Solutions:**
1. Check logs:
   ```bash
   sudo journalctl -u jetson-monitor.service -n 50
   ```
2. Test manually:
   ```bash
   cd ~/jetson-camera-monitor/autostart_autodown
   python3 JETSON1_INTEGRATED.py
   ```
3. Check DISPLAY environment:
   ```bash
   echo $DISPLAY  # Should be :0 or :1
   ```

### Issue: Multiple camera conflicts

**Symptoms:**
- Only first camera works
- Camera indices mixed up

**Solutions:**
1. Check all cameras:
   ```bash
   ls -l /dev/video*
   v4l2-ctl --list-devices
   ```
2. Verify GMSL modes match your cameras in config.json
3. Ensure camera indices are unique (0, 1, 2, 3)

---

## Switching Back to USB Cameras

If you need to switch back to USB cameras:

1. Edit `config.json`:
   ```json
   {
     "camera_type": "usb",
     "camera_index": 0
   }
   ```

2. Restart service:
   ```bash
   sudo systemctl restart jetson-monitor.service
   ```

3. (Optional) Unload GMSL drivers:
   ```bash
   sudo rmmod sgx-yuv-gmsl2
   sudo rmmod max96712
   ```

---

## Advanced Usage

### Manual Driver Loading

If you need to load drivers manually (for testing):

```bash
cd ~/jetson-camera-monitor/camera_autostart
./camera_driver_autoload.sh
```

### Multiple GMSL Camera Configuration

For 4 GMSL cameras with different types:

```json
{
  "camera_type": "gmsl",
  "camera_index": 0,
  "gmsl_mode": 2,           // Camera 0: GMSL2/3G

  "stirfry_camera_type": "gmsl",
  "stirfry_camera_index": 1,
  "stirfry_gmsl_mode": 2    // Camera 1: GMSL2/3G
}
```

The driver will be loaded with: `GMSLMODE_1=2,2,2,2` (all cameras GMSL2/3G)

### Programmatic Camera Creation

In your Python code:

```python
from src.monitoring.camera.camera_factory import (
    CameraConfig, CameraType, UniversalCamera
)

# Create GMSL camera
config = CameraConfig(
    camera_type=CameraType.GMSL,
    camera_index=0,
    resolution=(1920, 1536),
    gmsl_mode=2,
    gmsl_resolution_mode=1
)

camera = UniversalCamera(config)
if camera.initialize():
    ret, frame = camera.read_frame()
    # ... use frame ...
    camera.release()
```

---

## Service Management

### Install/Uninstall

```bash
# Install auto-start service
cd ~/jetson-camera-monitor/autostart_autodown
./install_autostart.sh

# Uninstall service
./uninstall_autostart.sh
```

### Control Service

```bash
# Start
sudo systemctl start jetson-monitor.service

# Stop
sudo systemctl stop jetson-monitor.service

# Restart (after config changes)
sudo systemctl restart jetson-monitor.service

# Check status
sudo systemctl status jetson-monitor.service

# View logs
sudo journalctl -u jetson-monitor.service -f

# Disable auto-start
sudo systemctl disable jetson-monitor.service

# Re-enable auto-start
sudo systemctl enable jetson-monitor.service
```

---

## Files Overview

### Key Files

| File | Purpose |
|------|---------|
| `src/monitoring/camera/camera_factory.py` | Universal camera abstraction (USB + GMSL) |
| `autostart_autodown/config.json` | Main configuration file |
| `autostart_autodown/JETSON1_INTEGRATED.py` | Monitoring system main script |
| `autostart_autodown/jetson-monitor.service` | Systemd service file |
| `autostart_autodown/install_autostart.sh` | Installation script |
| `autostart_autodown/uninstall_autostart.sh` | Uninstallation script |
| `camera_autostart/camera_driver_autoload.sh` | Manual driver loading script |
| `SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/ko/` | GMSL kernel modules |

---

## Reference

### Camera Configuration Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `camera_type` | string | `"usb"` | Camera type: `"usb"` or `"gmsl"` |
| `camera_index` | int | `0` | Camera device index (0-3 for GMSL) |
| `camera_resolution.width` | int | `640` | Frame width in pixels |
| `camera_resolution.height` | int | `360` | Frame height in pixels |
| `camera_fps` | int | `30` | Frames per second |
| `gmsl_mode` | int | `2` | GMSL type: 0=GMSL, 1=GMSL2/6G, 2=GMSL2/3G |
| `gmsl_resolution_mode` | int | `1` | Resolution preset (0-4) |
| `gmsl_driver_dir` | string | `"..."` | Path to GMSL driver directory |

### System Requirements

| Component | Requirement |
|-----------|-------------|
| Hardware | Jetson Orin Nano / AGX Orin |
| OS | Ubuntu 20.04/22.04 for Jetson |
| JetPack | 6.2 or later |
| Python | 3.8+ |
| Disk Space | 2GB+ for models and recordings |
| RAM | 4GB+ recommended |

---

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. View system logs: `sudo journalctl -u jetson-monitor.service -f`
3. Check camera devices: `ls -l /dev/video*`
4. Test cameras manually: `v4l2-ctl --list-devices`

---

**Last Updated:** 2025-11-03
**Version:** 1.0.0
