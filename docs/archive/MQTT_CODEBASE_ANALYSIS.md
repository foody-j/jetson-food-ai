# Comprehensive MQTT Implementation Analysis - Frying AI Project

## Executive Summary

The Frying AI project on Jetson Orin is a sophisticated multi-component monitoring system with camera, vibration, and frying AI components. Currently, **basic MQTT support exists** in the auto-start/down system, but it lacks comprehensive metadata (IP addresses, PC information, system status).

---

## 1. EXISTING MQTT IMPLEMENTATIONS

### 1.1 Current MQTT Usage

#### Files with MQTT Code:
1. **`/home/dkutest/my_ai_project/autostart_autodown/JETSON1_INTEGRATED.py`** (GUI version)
   - Lines 22, 52-58: MQTT imports and configuration
   - Lines 113, 145, 355-386: MQTT client initialization
   - Lines 539, 578: MQTT publish for ON/OFF messages
   - Lines 838-840: MQTT cleanup on shutdown

2. **`/home/dkutest/my_ai_project/autostart_autodown/ROBOTCAM_HEADLESS.py`** (Headless version)
   - Lines 15, 61-67: MQTT imports and configuration
   - Lines 84-109: MQTT client setup
   - Lines 132-142: MQTT publish function
   - Lines 246, 277: Publishing ON/OFF messages

#### Current MQTT Implementation Details:

```python
# Configuration loaded from config.json (lines 52-58 in JETSON1_INTEGRATED.py)
MQTT_ENABLED = config.get('mqtt_enabled', False)
MQTT_BROKER = config.get('mqtt_broker', 'localhost')
MQTT_PORT = config.get('mqtt_port', 1883)
MQTT_TOPIC = config.get('mqtt_topic', 'robot/control')
MQTT_QOS = config.get('mqtt_qos', 1)
MQTT_CLIENT_ID = config.get('mqtt_client_id', 'robotcam_jetson')
```

**Limitations:**
- Only publishes simple ON/OFF messages
- No PC information (IP, hostname, system stats)
- No health monitoring data
- No system metadata
- Uses only `paho-mqtt` library (but it's not in requirements)

---

## 2. PROJECT STRUCTURE & COMPONENT COMMUNICATION

### 2.1 High-Level Architecture

```
my_ai_project/
├── autostart_autodown/                    # Auto-on/off system (YOLO + MQTT)
│   ├── JETSON1_INTEGRATED.py             # GUI version (Tkinter)
│   ├── ROBOTCAM_HEADLESS.py              # Headless version
│   └── config.json                        # Configuration
│
├── src/                                   # Main modular system
│   ├── core/
│   │   ├── config.py                     # Configuration management
│   │   └── utils.py                      # Utilities
│   │
│   ├── monitoring/
│   │   ├── camera/
│   │   │   ├── camera_base.py            # Base camera control
│   │   │   ├── motion_detector.py        # Motion detection
│   │   │   ├── recorder.py               # Video recording
│   │   │   └── monitor.py                # Camera monitoring
│   │   │
│   │   ├── vibration/
│   │   │   ├── rs485_sensor.py           # RS485 sensor interface
│   │   │   ├── vibration_detector.py     # Main detector
│   │   │   └── vibration_analyzer.py     # Analysis logic
│   │   │
│   │   └── frying/
│   │       ├── frying_data_collector.py  # Data collection
│   │       ├── food_segmentation.py      # AI segmentation
│   │       └── sensor_simulator.py       # Sensor simulation
│   │
│   ├── scheduler/
│   │   ├── work_scheduler.py             # Schedule management
│   │   └── service_manager.py            # Service lifecycle
│   │
│   └── gui/
│       ├── main_app.py                   # Flask app
│       └── dash_app.py                   # Dash dashboard
│
├── config/
│   ├── system_config.json                # Main system config
│   └── camera_config.json                # Camera config
│
└── requirements_monitoring.txt           # Dependencies
```

### 2.2 Component Communication Patterns

#### Current Communication:
1. **Auto-start/down system**: Publishes ON/OFF to MQTT
2. **Monitoring dashboard**: Web-based (Flask/Dash) with real-time updates
3. **Vibration system**: Data logged to files/analyzed internally
4. **Frying AI**: Sensor data collected + saved to JSON/CSV
5. **Work scheduler**: Controls service lifecycle

#### Data Flow:
```
Camera (USB) → YOLO Detection → ON/OFF MQTT Message
RS485 Sensor → Vibration Detector → CSV/JSON logging → Dashboard
Cameras (2) → Frying Data Collector → Images + Sensor Data → JSON/CSV
Work Scheduler → Service Manager → Service start/stop callbacks
```

---

## 3. TYPES OF DATA BEING SENT/RECEIVED

### 3.1 Camera/Vision Data
**Source:** Camera (USB video device)
**Currently:** 
- Live frames processed by YOLO
- Person detection with confidence scores
- Motion detection with blob areas
- Screenshots/snapshots saved as JPEG
- Video recordings in MJPG format

**Data Structure:**
```python
- Frame (numpy array): 640x360 to 1280x720 resolution
- Detection results: person count, bounding boxes, confidence
- Motion areas: contour areas, coordinates
```

### 3.2 Sensor Data (Vibration)
**Source:** RS485 Modbus vibration sensor via USB2RS485

**Data Structure (VibrationReading dataclass):**
```python
@dataclass
class VibrationReading:
    timestamp: float              # Unix timestamp
    x_axis: float                 # Acceleration (m/s²)
    y_axis: float
    z_axis: float
    magnitude: float              # Combined magnitude
    temperature: Optional[float]  # Sensor temperature
    frequency: Optional[float]    # Dominant frequency
```

**Sampling:** 10 Hz (10 samples/second)
**Storage:** CSV and real-time analysis

### 3.3 Frying/Cooking Data
**Source:** Two cameras + simulated temperature sensors

**Data Structures:**
```python
@dataclass
class SensorData:
    timestamp: float
    oil_temp: float               # Oil temperature (°C)
    fryer_temp: float            # Fryer temperature
    elapsed_time: float          # Time since cooking started

@dataclass
class FrameData:
    timestamp: float
    image_path: str              # Path to saved image
    sensor_data: SensorData
    is_complete: bool            # Completion status

@dataclass
class SessionData:
    session_id: str              # e.g., "chicken_20251030_094500"
    food_type: str               # chicken, shrimp, potato, etc.
    start_time: float
    end_time: Optional[float]
    completion_time: Optional[float]
    probe_temp: Optional[float]  # Ground truth temperature
    frames: List[FrameData]
    notes: str
```

**Storage:** Images (JPEG) + JSON metadata + CSV sensor logs

### 3.4 System/Scheduler Data
**Source:** Work scheduler and service manager

```python
Scheduler Status:
- Current mode (work/off-hours)
- Work hours (start/end times)
- Is work time (boolean)
- Manual override status
- Minutes until next event

Service Status:
- Service ID (camera, vibration, frying)
- Status (running/stopped)
- Uptime, frame count
- Error messages
```

---

## 4. CONFIGURATION FILES & NETWORKING SETTINGS

### 4.1 Primary Configuration Files

#### 1. **Auto-start/down Config** 
**Location:** `/home/dkutest/my_ai_project/autostart_autodown/config.json`

```json
{
  "mode": "auto",                           // auto, day, or night
  "day_start": "07:30",                    // Work hours start
  "day_end": "14:45",                      // Work hours end
  "camera_index": 1,                       // USB camera index
  "yolo_model": "yolo12n.pt",             // YOLO model
  "yolo_confidence": 0.7,                 // Detection threshold
  "detection_hold_sec": 30,               // Hold duration for ON
  "night_check_minutes": 10,              // Night mode check period
  "motion_min_area": 1500,                // Minimum motion area
  "snapshot_dir": "Detection",            // Snapshot directory
  "snapshot_cooldown_sec": 10,            // Snapshot cooldown
  "display_window": false,                // Show GUI
  "window_width": 1280,
  "window_height": 720,
  
  "mqtt_enabled": false,                  // MQTT toggle
  "mqtt_broker": "localhost",             // Broker host
  "mqtt_port": 1883,                      // Broker port
  "mqtt_topic": "robot/control",          // Topic
  "mqtt_qos": 1,                          // QoS level
  "mqtt_client_id": "robotcam_jetson",   // Client ID
  
  "stirfry_camera_index": 2,             // Second camera
  "stirfry_save_dir": "StirFry_Data"
}
```

#### 2. **System Configuration** 
**Location:** `/home/dkutest/my_ai_project/config/system_config.json`

```json
{
  "vibration": {
    "enabled": true,
    "sensor": {
      "port": "/dev/ttyUSB0",             // USB serial port
      "baudrate": 9600,
      "protocol": "modbus",
      "slave_address": 1,
      "timeout": 1.0
    },
    "analyzer": {
      "window_size": 100,
      "alert_thresholds": {
        "low": 2.0,
        "medium": 5.0,
        "high": 10.0,
        "critical": 20.0
      }
    },
    "log_directory": "data/vibration_logs",
    "sampling_rate": 10.0
  },
  "camera": {
    "enabled": true,
    "index": 0,
    "resolution": {
      "width": 640,
      "height": 360
    },
    "fps": 30,
    "name": "Default Camera"
  },
  "frying_ai": {
    "enabled": true,
    "fps": 2,
    "log_directory": "data/frying_dataset"
  },
  "scheduler": {
    "enabled": true,
    "work_hours": {
      "start": "08:30",
      "end": "19:00",
      "enabled_days": [0, 1, 2, 3, 4, 5, 6]
    },
    "grace_period_minutes": 5,
    "auto_start_enabled": true,
    "auto_stop_enabled": true,
    "timezone": "Asia/Seoul"
  },
  "web_server": {
    "host": "0.0.0.0",
    "port": 5000,
    "debug": false
  },
  "logging": {
    "level": "INFO",
    "log_directory": "logs"
  }
}
```

#### 3. **Camera Configuration**
**Location:** `/home/dkutest/my_ai_project/config/camera_config.json`

```json
{
  "system": {
    "timezone": "Asia/Seoul",
    "log_timezone": true
  },
  "camera": {
    "index": 0,
    "resolution": {
      "width": 640,
      "height": 360
    },
    "fps": 120,
    "name": "Jetson Camera"
  },
  "recording": {
    "codec": "MJPG",
    "output_dir": "output/recordings",
    "auto_start": true
  },
  "motion_detection": {
    "enabled": true,
    "threshold": 1000,
    "min_area": 500
  },
  "screenshot": {
    "output_dir": "output/screenshots",
    "format": "jpg",
    "auto_capture_on_motion": true
  }
}
```

### 4.2 Docker Configuration

**Location:** `/home/dkutest/my_ai_project/docker-compose.yml`

```yaml
services:
  ai-dev:
    image: jp6:jp6
    container_name: my-dev-container
    network_mode: host                # Uses host network
    environment:
      - TZ=Asia/Seoul
      - DISPLAY=${DISPLAY}
    devices:
      - /dev/video1:/dev/video1       # Camera device
      - /dev/video2:/dev/video2
      - /dev/nvhost-ctrl-gpu          # Jetson GPU access
      - /dev/nvmap
    volumes:
      - .:/project
      - /tmp/.X11-unix:/tmp/.X11-unix # X11 forwarding
    runtime: nvidia
    ipc: host
```

**Key Points:**
- Network mode set to `host` (direct access to host network)
- GPU devices mounted
- Camera devices available
- Timezone: Asia/Seoul

### 4.3 Web Server Configuration

**Main entry points:**
- **Flask:** `config['web_server']['host']` = "0.0.0.0", `port` = 5000
- **Dash:** Hardcoded at `http://localhost:8050` in dash_app.py

---

## 5. MONITORING DATA FLOWS

### 5.1 Real-time Monitoring Dashboard
**Location:** `/home/dkutest/my_ai_project/src/gui/dash_app.py`

The Dash dashboard creates a `DashboardData` class that buffers real-time data:

```python
class DashboardData:
    # Vibration buffers (max 300 points)
    vib_time = deque(maxlen=300)
    vib_x = deque(maxlen=300)
    vib_y = deque(maxlen=300)
    vib_z = deque(maxlen=300)
    vib_magnitude = deque(maxlen=300)
    
    system_status = {
        'initialized': bool,
        'services': [],
        'scheduler': {},
        'vibration': {},
        'alerts': []
    }
```

**Update frequency:** 1 second (1000ms interval)

### 5.2 Data Storage Locations

```
project_root/
├── Detection/                          # YOLO snapshots
│   └── YYYYMMDD/
│       └── HHMMSS.jpg
├── StirFry_Data/                       # Cooking sessions
│   └── food_type_YYYYMMdd_HHMMSS/
│       ├── images/
│       │   └── t0000.jpg, t0001.jpg...
│       ├── session_data.json           # Session metadata
│       └── sensor_log.csv              # Sensor timeline
├── data/
│   ├── vibration_logs/                 # Vibration data
│   │   └── session_HHMMSS_XXXXX.csv
│   └── frying_dataset/                 # Alias to frying data
├── output/
│   ├── recordings/                     # Video files
│   └── screenshots/                    # Captured images
├── logs/                               # Application logs
└── recordings/                         # Alternative recording location
```

---

## 6. EXISTING MQTT MESSAGE PATTERN

### Current Implementation

The current MQTT system is minimal and only handles ON/OFF messages:

```python
def publish_mqtt(self, message):
    """Publish message to MQTT broker"""
    if self.mqtt_client is not None:
        try:
            result = self.mqtt_client.publish(MQTT_TOPIC, message, qos=MQTT_QOS)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"[MQTT] メッセージ送信完了: {message}")
            else:
                print(f"[MQTT] 送信失敗 (コード {result.rc})")
        except Exception as e:
            print(f"[MQTT] 送信エラー: {e}")
```

**Published Messages:**
- `"ON"` - When person detected for DETECTION_HOLD_SEC seconds
- `"OFF"` - When no person for NIGHT_CHECK_MINUTES minutes at night

**Topics:**
- Default: `robot/control`
- Configurable via `mqtt_topic` in config

---

## 7. MISSING PC INFORMATION & METADATA

### 7.1 System Information NOT Currently Tracked

```
PC/Device Information:
- ✗ Hostname
- ✗ IP addresses (ethernet, wifi)
- ✗ MAC addresses
- ✗ System uptime
- ✗ CPU usage/temperature
- ✗ Memory usage
- ✗ GPU usage (Jetson-specific)
- ✗ Disk usage
- ✗ Network interfaces

Application Metadata:
- ✗ Software version
- ✗ Running services status
- ✗ Last system restart time
- ✗ Configuration hash/version
- ✗ Available models (YOLO, etc.)
- ✗ Jetson hardware info (Orin, Xavier, etc.)
```

### 7.2 Data NOT Being Published via MQTT

Currently only ON/OFF strings are sent. Missing:
- System health metrics
- Service status (camera, vibration, frying)
- Sensor readings
- Detection statistics
- Error/warning messages
- Sensor connectivity status
- Configuration changes

---

## 8. TECHNICAL REQUIREMENTS FOR MQTT EXPANSION

### 8.1 Current Libraries
From `requirements_monitoring.txt`:
```
paho-mqtt                  # For MQTT (currently used but NOT in requirements!)
flask>=2.0.0
dash>=2.14.0
dash-bootstrap-components>=1.5.0
plotly>=5.17.0
pyserial>=3.5             # RS485 sensor communication
numpy>=1.19.0
opencv-python>=4.5.0
jsonschema>=4.0.0
```

**Note:** `paho-mqtt` is used in code but NOT listed in requirements!

### 8.2 Available System Information Sources

1. **Python Libraries:**
   - `socket` - Hostname, IP addresses
   - `psutil` - CPU, memory, disk, processes
   - `platform` - OS, Python version
   - `os` - Environment variables
   - `subprocess` - System commands

2. **Jetson-specific:**
   - `/proc/device-tree/model` - Hardware model
   - `/sys/devices/virtual/dmi/id/` - System info
   - NVIDIA jetson-stats library (optional)

3. **Application:**
   - Config files (JSON)
   - Service manager status
   - VibrationDetector.get_current_status()
   - WorkScheduler.get_status()

---

## 9. RECOMMENDATIONS FOR IMPLEMENTATION

### High Priority:
1. **Fix MQTT in requirements** - Add `paho-mqtt` to requirements_monitoring.txt
2. **Centralized MQTT module** - Create `src/communication/mqtt_client.py`
3. **System info collector** - Create `src/core/system_info.py`
4. **Enhanced message schema** - JSON-based MQTT messages with metadata

### Medium Priority:
1. Integrate MQTT across all monitoring components
2. Add status topic subscriptions for two-way communication
3. Implement retained messages for configuration
4. Add debug logging for MQTT operations

### Low Priority:
1. TLS/SSL encryption support
2. Authentication (username/password)
3. Message persistence
4. Cluster/load balancing support

---

## 10. DATA STRUCTURE RECOMMENDATIONS

### Proposed MQTT Message Format

```json
{
  "device_id": "robotcam_jetson_001",
  "timestamp": 1698742500.123456,
  "device_info": {
    "hostname": "jetson-orin-kitchen",
    "ip_addresses": {
      "eth0": "192.168.1.100",
      "wlan0": "192.168.1.101"
    },
    "mac_address": "AA:BB:CC:DD:EE:FF",
    "hardware": "NVIDIA Jetson Orin",
    "uptime_seconds": 86400
  },
  "system_metrics": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "gpu_percent": 75.0,
    "disk_percent": 48.3,
    "temperature_c": 62.5
  },
  "services": {
    "camera": { "status": "running", "frames_processed": 1500 },
    "vibration": { "status": "running", "readings_count": 45000 },
    "frying_ai": { "status": "running", "sessions_active": 2 }
  },
  "detections": {
    "type": "yolo_person",
    "count": 2,
    "confidence_avg": 0.85
  }
}
```

---

## 11. FILE STRUCTURE SUMMARY

**Key Files for MQTT Implementation:**
- Auto-start: `/home/dkutest/my_ai_project/autostart_autodown/JETSON1_INTEGRATED.py`
- Headless: `/home/dkutest/my_ai_project/autostart_autodown/ROBOTCAM_HEADLESS.py`
- Monitoring: `/home/dkutest/my_ai_project/src/gui/dash_app.py`
- Config: `/home/dkutest/my_ai_project/config/system_config.json`
- Requirements: `/home/dkutest/my_ai_project/requirements_monitoring.txt`

**Absolute Paths:**
```
/home/dkutest/my_ai_project/
/home/dkutest/my_ai_project/autostart_autodown/
/home/dkutest/my_ai_project/config/
/home/dkutest/my_ai_project/src/
```

---

## Conclusion

The Frying AI project has a solid foundation with basic MQTT support for simple ON/OFF messaging. To implement a comprehensive MQTT system with PC information and metadata:

1. **Currently:** MQTT only publishes "ON"/"OFF" to `robot/control` topic
2. **Available:** Multiple data sources (cameras, sensors, scheduler, services)
3. **Missing:** System metrics, device info, health status, comprehensive JSON messages
4. **Opportunity:** Centralize all monitoring data via MQTT with standardized message schema
5. **Dependencies:** Need to add `paho-mqtt` to requirements, create system info collection modules

The modular architecture (`src/monitoring/`, `src/scheduler/`) is well-designed for extension with MQTT integration points.

