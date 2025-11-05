# Quick Start Guide - 3 Cameras Setup

Jetson Orin PC #1 - Human Surveillance + Dual Stir-Fry Monitoring

---

## 📷 Camera Configuration

### Physical Connections (SG4A-NONX-G2Y-A1 Adapter)

| Port | Video Device | Purpose | Camera |
|------|--------------|---------|--------|
| **CN4** | `/dev/video0` | Human Surveillance | YOLO Person Detection |
| **CN5** | `/dev/video1` | Stir-Fry LEFT | Data Collection |
| **CN6** | `/dev/video2` | Stir-Fry RIGHT | Data Collection |
| CN7 | `/dev/video3` | *Not Used* | - |

---

## ⚙️ Configuration

Your `config.json` is already configured for 3 cameras:

```json
{
  // Camera 0: Human Surveillance (CN4 → video0)
  "camera_type": "gmsl",
  "camera_index": 0,

  // Camera 1: Stir-Fry LEFT (CN5 → video1)
  "stirfry_left_camera_type": "gmsl",
  "stirfry_left_camera_index": 1,

  // Camera 2: Stir-Fry RIGHT (CN6 → video2)
  "stirfry_right_camera_type": "gmsl",
  "stirfry_right_camera_index": 2
}
```

---

## 🚀 Running the System

### Option 1: Manual Run (Testing)

```bash
cd ~/jetson-camera-monitor/autostart_autodown
python3 JETSON1_INTEGRATED.py
```

**Expected startup output:**
```
[초기화] Jetson #1 통합 시스템 시작 중...
[설정] 카메라 0 (사람 감시): GMSL #0 @ 1920x1536
[설정] 카메라 1 (볶음 왼쪽): GMSL #1
[설정] 카메라 2 (볶음 오른쪽): GMSL #2
[GMSL] Loading drivers from ...
[GMSL] max96712.ko loaded successfully
[GMSL] sgx-yuv-gmsl2.ko loaded successfully with GMSLMODE_1=2,2,2,2
[카메라] 자동 ON/OFF 카메라 초기화 완료: GMSL #0
[카메라] 볶음 모니터링 왼쪽 카메라 초기화 완료: GMSL #1
[카메라] 볶음 모니터링 오른쪽 카메라 초기화 완료: GMSL #2
[YOLO] 모델 로드 완료
[초기화] GUI 초기화 완료
```

### Option 2: Auto-Start on Boot (Production)

```bash
cd ~/jetson-camera-monitor/autostart_autodown
./install_autostart.sh
```

This will:
- ✅ Install systemd service
- ✅ Enable auto-start on boot
- ✅ Start monitoring immediately

---

## 🖥️ GUI Layout

```
┌────────────────────────────────────────────────────────┐
│  Header: Time, Status, Controls                        │
├────────────────────────────────────────────────────────┤
│  Panel 1: Human Surveillance (YOLO Person Detection)   │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Video0: Person detection with bounding boxes    │  │
│  └──────────────────────────────────────────────────┘  │
├──────────────────────────┬─────────────────────────────┤
│  Panel 2: Stir-Fry LEFT  │  Panel 3: Stir-Fry RIGHT   │
│  ┌──────────────────────┐│  ┌──────────────────────┐  │
│  │  Video1: Left Camera ││  │  Video2: Right Camera│  │
│  └──────────────────────┘│  └──────────────────────┘  │
│  Saved: 0 frames         │  Saved: 0 frames           │
│                          │  [Start] [Stop] Buttons    │
└──────────────────────────┴─────────────────────────────┘
```

**Controls:**
- **Start Button**: Begins recording BOTH stir-fry cameras
- **Stop Button**: Stops recording and shows frame counts

---

## 📁 Data Storage

### Directory Structure

```
StirFry_Data/
├── left/              # LEFT camera recordings
│   └── 20251103/      # Date folder
│       ├── left_103045_123.jpg
│       ├── left_103045_156.jpg
│       └── ...
└── right/             # RIGHT camera recordings
    └── 20251103/
        ├── right_103045_124.jpg
        ├── right_103045_157.jpg
        └── ...

Detection/             # Human surveillance snapshots
└── 20251103/
    ├── 201523.jpg
    └── ...
```

**File Naming:**
- Left: `left_HHMMSSmmm.jpg` (includes milliseconds)
- Right: `right_HHMMSSmmm.jpg`
- Detection: `HHMMSS.jpg`

---

## 🔍 Verification

### 1. Check Camera Devices

```bash
ls -l /dev/video*
```

Expected output:
```
crw-rw----+ 1 root video 81, 0 Nov  3 10:00 /dev/video0  ← CN4
crw-rw----+ 1 root video 81, 1 Nov  3 10:00 /dev/video1  ← CN5
crw-rw----+ 1 root video 81, 2 Nov  3 10:00 /dev/video2  ← CN6
crw-rw----+ 1 root video 81, 3 Nov  3 10:00 /dev/video3  ← CN7 (unused)
```

### 2. Test Individual Cameras

```bash
# Test video0 (Human surveillance - CN4)
gst-launch-1.0 v4l2src device=/dev/video0 ! videoconvert ! autovideosink

# Test video1 (Stir-fry LEFT - CN5)
gst-launch-1.0 v4l2src device=/dev/video1 ! videoconvert ! autovideosink

# Test video2 (Stir-fry RIGHT - CN6)
gst-launch-1.0 v4l2src device=/dev/video2 ! videoconvert ! autovideosink

# Press Ctrl+C to stop each test
```

### 3. Check GMSL Drivers

```bash
lsmod | grep -E "(max96712|gmsl2)"
```

Expected output:
```
sgx_yuv_gmsl2         xxxxxx  0
max96712              xxxxxx  1 sgx_yuv_gmsl2
```

### 4. Check Service Status (if auto-start installed)

```bash
sudo systemctl status jetson-monitor.service
```

Expected:
```
● jetson-monitor.service - Jetson #1 Integrated Monitoring System
   Loaded: loaded
   Active: active (running)
```

---

## 🎯 Operation Modes

### Day Mode (07:30 - 14:45)
- **Human Surveillance**: YOLO person detection
- **Stir-Fry**: Standby (preview hidden until recording starts)

### Night Mode (14:45 - 07:30)
- **Human Surveillance**: Motion detection + snapshot saving
- **Stir-Fry**: Standby

### Recording Stir-Fry Data
1. Click **"시작"** (Start) button in the right panel
2. Both cameras start recording simultaneously
3. Frame counters update in real-time
4. Click **"중지"** (Stop) to finish and see summary

---

## 🐛 Troubleshooting

### Problem: Cameras are swapped

**Check which camera is which:**
```bash
# Test CN4 (should be human surveillance)
gst-launch-1.0 v4l2src device=/dev/video0 ! videoconvert ! autovideosink

# Test CN5 (should be stir-fry LEFT)
gst-launch-1.0 v4l2src device=/dev/video1 ! videoconvert ! autovideosink

# Test CN6 (should be stir-fry RIGHT)
gst-launch-1.0 v4l2src device=/dev/video2 ! videoconvert ! autovideosink
```

**Solution:**
1. **Physically swap camera cables** (easiest), OR
2. **Change indices in config.json**:
   ```json
   {
     "camera_index": X,              // Use correct index for human
     "stirfry_left_camera_index": Y,
     "stirfry_right_camera_index": Z
   }
   ```

### Problem: Only 2 cameras detected

**Verify all cameras are connected:**
```bash
v4l2-ctl --list-devices
```

**Check driver loaded for all 4 ports:**
```bash
dmesg | grep -i gmsl
```

### Problem: Black screen on one camera

**Check NVCSI clock:**
```bash
cat /sys/kernel/debug/bpmp/debug/clk/nvcsi/rate
# Should show: 214300000
```

**Manually reconfigure:**
```bash
cd ~/jetson-camera-monitor/camera_autostart
./camera_driver_autoload.sh
```

---

## 📊 Performance Tips

### If GUI is slow:

1. **Reduce camera resolution** in `config.json`:
   ```json
   {
     "gmsl_resolution_mode": 4  // Use 1280x720 instead of 1920x1536
   }
   ```

2. **Reduce YOLO image size** (edit JETSON1_INTEGRATED.py line ~90):
   ```python
   YOLO_IMGSZ = 320  # Reduced from 416
   ```

3. **Disable preview auto-hide** if causing issues

---

## 🔧 Service Management

```bash
# View logs
sudo journalctl -u jetson-monitor.service -f

# Restart after config changes
sudo systemctl restart jetson-monitor.service

# Stop service
sudo systemctl stop jetson-monitor.service

# Disable auto-start
sudo systemctl disable jetson-monitor.service
```

---

## 📝 Summary

| Component | Camera | Port | Video Device |
|-----------|--------|------|--------------|
| Human Surveillance | GMSL | CN4 | /dev/video0 |
| Stir-Fry LEFT | GMSL | CN5 | /dev/video1 |
| Stir-Fry RIGHT | GMSL | CN6 | /dev/video2 |

**Key Features:**
- ✅ Automatic GMSL driver loading
- ✅ 3 independent camera streams
- ✅ Simultaneous recording of both stir-fry cameras
- ✅ Separate storage for left/right cameras
- ✅ Auto-start on boot support

---

**Ready to run!** 🚀

For detailed GMSL camera documentation, see:
- `docs/GMSL_CAMERA_MIGRATION_GUIDE.md`
- `autostart_autodown/README_GMSL.md`
