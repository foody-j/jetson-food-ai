# Jetson #1 Integrated Monitoring System

통합 모니터링 시스템 - GMSL/USB 카메라 지원, YOLO 감지, MQTT 통신

---

## 📋 Overview

This system is a comprehensive monitoring solution for Jetson Orin with:
- **Dual camera support**: Auto-start/down system + Stir-fry monitoring
- **USB and GMSL cameras**: Automatic driver loading and configuration
- **YOLO person detection**: Auto-start robot when person detected
- **Motion detection**: Night-time snapshot recording
- **MQTT integration**: Robot control and telemetry
- **Auto-start on boot**: Systemd service for production deployment

---

## 🎥 Camera Support

### Camera Types

| Type | Description | Auto-load | Resolution |
|------|-------------|-----------|------------|
| **USB** | Standard USB webcams | ✅ Auto | Configurable |
| **GMSL** | SENSING automotive cameras | ✅ Auto | Up to 4K |

### Camera Configuration

The system supports **2 independent cameras**:
1. **Camera 1 (Auto-start/down)**: YOLO person detection + motion detection
2. **Camera 2 (Stir-fry monitoring)**: Data collection for stir-fry process

Both cameras can be **USB or GMSL** independently.

---

## 📦 Files

```
autostart_autodown/
├── JETSON1_INTEGRATED.py       # Main integrated system ⭐
├── config.json                 # Configuration file ⭐
├── jetson-monitor.service      # Systemd service file
├── install_autostart.sh        # Auto-start installation script ⭐
├── uninstall_autostart.sh      # Uninstallation script
├── install_dependencies.sh     # Dependency installer
├── yolo12n.pt                  # YOLO model weights
└── README_GMSL.md             # This file
```

---

## 🚀 Quick Start

### Step 1: Configure Cameras

Edit `config.json`:

```json
{
  "camera_type": "gmsl",          // "usb" or "gmsl"
  "camera_index": 0,
  "camera_resolution": {
    "width": 1920,
    "height": 1536
  },
  "gmsl_mode": 2,                 // 0=GMSL, 1=GMSL2/6G, 2=GMSL2/3G
  "gmsl_resolution_mode": 1,      // 0-4 (see resolution modes)

  "stirfry_camera_type": "gmsl",
  "stirfry_camera_index": 1,
  "stirfry_gmsl_mode": 2,
  "stirfry_gmsl_resolution_mode": 1
}
```

### Step 2: Install Auto-Start Service

```bash
cd ~/jetson-camera-monitor/autostart_autodown
./install_autostart.sh
```

This will:
- ✅ Check dependencies (v4l-utils for GMSL)
- ✅ Install systemd service
- ✅ Enable auto-start on boot
- ✅ Start monitoring system

### Step 3: Verify

```bash
# Check service status
sudo systemctl status jetson-monitor.service

# View live logs
sudo journalctl -u jetson-monitor.service -f
```

---

## ⚙️ Configuration

### config.json Parameters

#### Camera Settings

```json
{
  // Camera 1 (Auto-start/down)
  "camera_type": "gmsl",          // "usb" or "gmsl"
  "camera_index": 0,              // Device index (0-3 for GMSL)
  "camera_resolution": {
    "width": 1920,
    "height": 1536
  },
  "camera_fps": 30,

  // GMSL-specific settings (ignored if USB)
  "gmsl_mode": 2,                 // 0=GMSL, 1=GMSL2/6G, 2=GMSL2/3G
  "gmsl_resolution_mode": 1,      // Resolution preset (0-4)
  "gmsl_driver_dir": "/home/dkuyj/jetson-camera-monitor/SG4A-NONX-G2Y-A1_ORIN_NANO_YUV_JP6.2_L4TR36.4.3",

  // Camera 2 (Stir-fry monitoring)
  "stirfry_camera_type": "gmsl",
  "stirfry_camera_index": 1,
  "stirfry_gmsl_mode": 2,
  "stirfry_gmsl_resolution_mode": 1
}
```

#### GMSL Resolution Modes

| Mode | Resolution | Aspect Ratio | Notes |
|------|------------|--------------|-------|
| 0 | 1920x1080 | 16:9 | Full HD |
| 1 | 1920x1536 | 3:2 | **Default** |
| 2 | 2880x1860 | ~3:2 | High resolution |
| 3 | 3840x2160 | 16:9 | 4K |
| 4 | 1280x720 | 16:9 | HD |

#### Auto-Start/Down Settings

```json
{
  "mode": "auto",                 // "auto", "day", "night"
  "day_start": "07:30",           // Day mode start time
  "day_end": "14:45",             // Day mode end time

  "yolo_model": "yolo12n.pt",     // YOLO model file
  "yolo_confidence": 0.7,         // Detection confidence (0.0-1.0)
  "detection_hold_sec": 30,       // Person detected for X seconds → ON
  "night_check_minutes": 10,      // No person for X minutes → OFF
  "motion_min_area": 1500,        // Motion detection threshold
  "snapshot_dir": "Detection",    // Snapshot save directory
  "snapshot_cooldown_sec": 10     // Cooldown between snapshots
}
```

#### MQTT Settings

```json
{
  "mqtt_enabled": false,          // Enable MQTT
  "mqtt_broker": "localhost",     // Broker address
  "mqtt_port": 1883,              // Broker port
  "mqtt_topic": "robot/control",  // Control topic
  "mqtt_qos": 1,                  // QoS level (0, 1, 2)
  "mqtt_client_id": "robotcam_jetson"
}
```

---

## 🔄 System Modes

### Day Mode (07:30 - 14:45)

**YOLO Person Detection**
- Continuously detects people using YOLO
- If person detected for 30 seconds → Send "ON" command (once)
- Displays live camera feed with bounding boxes

### Night Mode (14:45 - 07:30)

**Stage 1: No-Person Check (10 minutes)**
- YOLO checks for people
- If no person for 10 minutes → Send "OFF" command (once)
- Moves to Stage 2

**Stage 2: Motion Detection**
- Background subtraction (MOG2)
- Saves snapshots when motion detected
- Cooldown: 10 seconds between snapshots
- Saved to: `Detection/YYYYMMDD/HHMMSS.jpg`

---

## 📡 MQTT Messages

### Command Format

```json
{
  "command": "ON",                    // "ON" or "OFF"
  "source": "auto_start_system",
  "person_detected": true,
  "motion_detected": false,
  "system_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "temperature": 58.5,
    "uptime_hours": 12.5
  }
}
```

### Topics

- **Publish**: `frying_ai/jetson1/robot/control`
- **Status**: `frying_ai/jetson1/status`
- **Metrics**: `frying_ai/jetson1/metrics`

---

## 🖥️ GUI Interface

The system includes a full-screen GUI with:

### Header
- System status indicator
- Current date and time
- Vibration sensor check button
- Settings button (5-tap to show shutdown)

### Panel 1: Auto-Start/Down
- Current mode (Day/Night)
- Detection status (person count, countdown)
- MQTT connection status
- Live camera preview with bounding boxes

### Panel 2: Stir-Fry Monitoring
- Live camera preview
- Recording status
- Frame count
- Start/Stop buttons

### Panel 3: Developer Mode (Hidden)
- Night-time snapshot statistics
- Last snapshot preview
- Motion detection info
- Force snapshot mode button

---

## 🛠️ Service Management

### Control Commands

```bash
# Start service
sudo systemctl start jetson-monitor.service

# Stop service
sudo systemctl stop jetson-monitor.service

# Restart (after config changes)
sudo systemctl restart jetson-monitor.service

# Check status
sudo systemctl status jetson-monitor.service

# View logs in real-time
sudo journalctl -u jetson-monitor.service -f

# View recent logs
sudo journalctl -u jetson-monitor.service -n 100
```

### Installation

```bash
# Install auto-start service
cd ~/jetson-camera-monitor/autostart_autodown
./install_autostart.sh

# Uninstall service
./uninstall_autostart.sh
```

---

## 🔧 Troubleshooting

### Camera Issues

**GMSL Camera Not Detected**
```bash
# Check if drivers loaded
lsmod | grep -E "(max96712|gmsl2)"

# Manually load drivers
cd ~/jetson-camera-monitor/camera_autostart
./camera_driver_autoload.sh

# Check camera devices
ls -l /dev/video*
v4l2-ctl --list-devices
```

**USB Camera Not Working**
```bash
# Test USB camera
v4l2-ctl --list-devices

# Check camera index
python3 test_camera.py
```

### Service Issues

**Service Won't Start**
```bash
# View detailed logs
sudo journalctl -u jetson-monitor.service -xe

# Test manually
cd ~/jetson-camera-monitor/autostart_autodown
python3 JETSON1_INTEGRATED.py

# Check Python dependencies
pip3 list | grep -E "(opencv|ultralytics|paho-mqtt)"
```

**Black Screen / No Display**
```bash
# Check DISPLAY variable
echo $DISPLAY

# Grant X11 access
xhost +local:

# Check NVCSI clock (GMSL only)
cat /sys/kernel/debug/bpmp/debug/clk/nvcsi/rate
# Should show: 214300000
```

### Performance Issues

**High CPU Usage**
- Reduce YOLO image size (YOLO_IMGSZ in code)
- Increase frame skip (yolo_frame_skip)
- Lower camera resolution

**Memory Issues**
- Reduce camera resolution
- Disable camera preview when not needed
- Clear old snapshots regularly

---

## 📊 Directory Structure

```
Detection/                    # Motion snapshots
├── 20251103/                # Date folder
│   ├── 201523.jpg
│   ├── 201533.jpg
│   └── ...

StirFry_Data/                # Stir-fry recordings
├── 20251103/
│   ├── 091234_567.jpg
│   ├── 091234_600.jpg
│   └── ...
```

---

## 🔄 Switching Camera Types

### USB → GMSL

1. Edit `config.json`:
   ```json
   {
     "camera_type": "gmsl",
     "camera_index": 0,
     "gmsl_mode": 2,
     "gmsl_resolution_mode": 1
   }
   ```

2. Restart service:
   ```bash
   sudo systemctl restart jetson-monitor.service
   ```

### GMSL → USB

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

## 📚 Additional Documentation

- **GMSL Camera Migration Guide**: `../docs/GMSL_CAMERA_MIGRATION_GUIDE.md`
- **Camera Auto-Start Setup**: `../camera_autostart/README.md`
- **MQTT Client Documentation**: `../src/communication/README.md`

---

## 🔐 Security Notes

- Service runs as user `dkuyj` (not root)
- Camera drivers require `sudo` for loading
- MQTT credentials should be configured in production
- Consider firewall rules for MQTT port (1883)

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-11-03 | Initial GMSL camera support |
| 1.1.0 | 2025-11-03 | Auto-start service added |
| 1.2.0 | 2025-11-03 | Dual camera support |

---

## 🆘 Support

For detailed GMSL camera setup, see:
- `../docs/GMSL_CAMERA_MIGRATION_GUIDE.md`

For issues:
1. Check service logs: `sudo journalctl -u jetson-monitor.service -f`
2. Test cameras: `v4l2-ctl --list-devices`
3. Verify drivers: `lsmod | grep gmsl2`

---

**Hardware**: Jetson Orin Nano / AGX Orin
**OS**: Ubuntu 20.04/22.04 for Jetson
**JetPack**: 6.2 or later
**Python**: 3.8+
