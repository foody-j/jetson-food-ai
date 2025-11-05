# Camera Driver Auto-Start Setup

Automatically load SENSING camera drivers when Jetson boots.

---

## Files

- `camera_driver_autoload.sh` - Script that loads camera drivers
- `sensing-camera.service` - systemd service configuration
- `README.md` - This file

**Note:** This folder contains YOUR custom auto-start scripts. The manufacturer's driver files in `SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3/` remain unchanged.

---

## Quick Installation

```bash
cd ~/jetson-camera-monitor/camera_autostart

# 1. Make script executable
chmod +x camera_driver_autoload.sh

# 2. Install systemd service
sudo cp sensing-camera.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable sensing-camera.service
sudo systemctl start sensing-camera.service

# 3. Verify
sudo systemctl status sensing-camera.service
ls -l /dev/video*
```

---

## Configuration

### 1. Camera Types (lines 61-64)

Edit to match your camera types:

```bash
CAM1_TYPE=2  # Camera on port 0
CAM2_TYPE=2  # Camera on port 1
CAM3_TYPE=2  # Camera on port 2
CAM4_TYPE=2  # Camera on port 3
```

**Values:**
- `0` = GMSL
- `1` = GMSL2/6G
- `2` = GMSL2/3G (Current)

### 2. Camera Resolution (line 20)

Edit to set the default resolution for all cameras:

```bash
RESOLUTION_MODE=1  # Current: 1920x1536
```

**Available Resolutions:**
- `0` = 1920x1080 (Full HD)
- `1` = 1920x1536 (3:2 aspect ratio) - **Default**
- `2` = 2880x1860 (High resolution)
- `3` = 3840x2160 (4K)
- `4` = 1280x720 (HD)

### 3. Auto-Configure Resolution (line 23)

Enable/disable automatic resolution configuration:

```bash
AUTO_CONFIGURE_RESOLUTION=true  # Set to false to skip resolution setup
```

---

## Testing

```bash
# Test manually before installing
./camera_driver_autoload.sh

# Check if cameras appeared
ls -l /dev/video*

# Unload drivers (for re-testing)
sudo rmmod sgx-yuv-gmsl2
sudo rmmod max96712
```

---

## Uninstall

```bash
sudo systemctl stop sensing-camera.service
sudo systemctl disable sensing-camera.service
sudo rm /etc/systemd/system/sensing-camera.service
sudo systemctl daemon-reload
```

---

## Logs

```bash
# View service logs
sudo journalctl -u sensing-camera.service -f

# View recent logs
sudo journalctl -u sensing-camera.service --since "5 min ago"
```

---

## How It Works

1. **At boot** → systemd runs `camera_driver_autoload.sh`
2. **Script loads** → `max96712.ko` and `sgx-yuv-gmsl2.ko` from manufacturer's folder
3. **Cameras available** → `/dev/video0-3` appear
4. **Resolution configured** → All cameras set to 1920x1536 (or your configured mode)
5. **Your app starts** → Can immediately use cameras with correct resolution

---

## Expected Output

When the service runs successfully, you should see:

```
[INFO] Loading max96712.ko...
[OK] max96712.ko loaded successfully
[INFO] Loading sgx-yuv-gmsl2.ko with GMSLMODE_1=2,2,2,2...
[OK] sgx-yuv-gmsl2.ko loaded successfully
[INFO] Checking camera devices...
[OK] /dev/video0 exists
[OK] /dev/video1 exists
[OK] /dev/video2 exists
[OK] /dev/video3 exists
[INFO] Configuring camera resolutions to mode 1...
[INFO] Setting /dev/video0 to resolution mode 1...
[OK] /dev/video0 configured successfully
[INFO] Setting /dev/video1 to resolution mode 1...
[OK] /dev/video1 configured successfully
[INFO] Setting /dev/video2 to resolution mode 1...
[OK] /dev/video2 configured successfully
[INFO] Setting /dev/video3 to resolution mode 1...
[OK] /dev/video3 configured successfully
[INFO] Resolution configuration complete
Camera driver auto-load complete
```
