# Docker Container Fixes - Apply Once

This document explains the fixes for Korean fonts and camera issues.

## Problems Fixed

1. ✅ **Korean fonts showing as squares** - Added Nanum fonts to Dockerfile
2. ✅ **Cameras not detected** - Fixed camera device mappings

## What Changed

### 1. Dockerfile
- Added Korean fonts: `fonts-nanum`, `fonts-nanum-coding`, `fonts-nanum-extra`
- Added required packages: `python3-tk`, `Pillow`, `ultralytics`, `paho-mqtt`, `psutil`

### 2. docker-compose.yml
- Added `/dev/video0:/dev/video0` mapping (Camera 1)
- Kept `/dev/video1:/dev/video1` mapping (Camera 2)

### 3. config.json
- Changed `camera_index` from 1 → 0
- Changed `stirfry_camera_index` from 2 → 1

## How to Apply

### Option 1: Rebuild Docker Image (Recommended - Permanent Fix)

```bash
# Exit container
exit

# On host - Rebuild the image
cd /home/dkutest/my_ai_project
docker compose down
docker compose build
docker compose up -d

# Enter new container
docker exec -it my-dev-container bash

# Setup X11 (for GUI)
exit
./setup_x11.sh
docker exec -it my-dev-container bash

# Test
cd /project/autostart_autodown
python3 JETSON1_INTEGRATED.py
```

### Option 2: Quick Temporary Fix (Until Next Restart)

```bash
# Inside container
apt update
apt install -y fonts-nanum fonts-nanum-coding fonts-nanum-extra
pip3 install Pillow ultralytics paho-mqtt psutil

# Exit and setup X11 on host
exit
./setup_x11.sh

# Re-enter container and test
docker exec -it my-dev-container bash
cd /project/autostart_autodown
python3 JETSON1_INTEGRATED.py
```

## Verify Fixes

### Check Korean Fonts
```bash
fc-list | grep -i nanum
```

Should show:
```
/usr/share/fonts/truetype/nanum/NanumGothic.ttf: NanumGothic:style=Regular
/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf: NanumGothic:style=Bold
...
```

### Check Camera Devices
```bash
ls -la /dev/video*
```

Should show:
```
crw-rw----+ 1 root video 81, 0 ... /dev/video0
crw-rw----+ 1 root video 81, 1 ... /dev/video1
```

### Test Camera Access
```bash
v4l2-ctl --list-devices
```

## Summary

**Before:**
- Korean text: ▢▢▢ (squares)
- Cameras: Not available (only /dev/video1 mapped)
- Config: Using cameras 1 and 2 (don't exist)

**After:**
- Korean text: 한글 텍스트 (readable)
- Cameras: /dev/video0 and /dev/video1 available
- Config: Using cameras 0 and 1 (exist)

## Future Restarts

After rebuilding the image with `docker compose build`, all these fixes will be permanent:
- ✅ Korean fonts always available
- ✅ Python packages always installed
- ✅ Camera mappings correct
- ⚠️ X11 setup still needs to run once after host reboot (`./setup_x11.sh`)
