# MQTT Implementation - Quick Reference Guide

## Current State

### MQTT is Already Implemented (But Limited)
- **Files:** `JETSON1_INTEGRATED.py` & `ROBOTCAM_HEADLESS.py`
- **Functionality:** Publishes "ON"/"OFF" messages only
- **Topic:** `robot/control` (configurable)
- **Messages:** Plain text strings (not JSON)
- **Issue:** Not in requirements.txt (missing dependency!)

---

## Data Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRYING AI MONITORING SYSTEM                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  INPUTS:                        PROCESSING:                     │
│  ├─ Camera 1 (USB)              ├─ YOLO Detection              │
│  ├─ Camera 2 (USB)              ├─ Motion Detection            │
│  ├─ RS485 Vibration Sensor      ├─ Vibration Analysis         │
│  ├─ Temperature Sensors         ├─ Frying Session Tracking    │
│  └─ System Clock                └─ Work Scheduler             │
│                                                                 │
│  OUTPUTS:                       STORAGE:                        │
│  ├─ MQTT Messages (ON/OFF)      ├─ JSON Config Files          │
│  ├─ Web Dashboard               ├─ Image Files (JPG)          │
│  ├─ Console Logs                ├─ CSV Sensor Logs            │
│  └─ Flask/Dash Web UI           ├─ Session Metadata           │
│                                 └─ Application Logs            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Data Types

### 1. Vibration Data (VibrationReading)
```
timestamp: 1698742500.123
x_axis: 0.45 m/s²
y_axis: 0.38 m/s²
z_axis: 0.52 m/s²
magnitude: 0.75 m/s²
temperature: 62.3°C (optional)
frequency: 50.5 Hz (optional)
```

### 2. Frying Session Data (SessionData)
```
session_id: "chicken_20251030_094500"
food_type: "chicken"
start_time: 1698742500.0
oil_temp: 170.2°C
fryer_temp: 175.1°C
completion_time: 1698742530.0
probe_temp: 75.5°C (ground truth)
frames: 120 images + metadata
```

### 3. Detection Data (Person)
```
person_count: 2
confidence: 0.87
bounding_boxes: [(x1,y1,x2,y2), ...]
detection_hold_sec: 30 (before triggering ON)
```

---

## Configuration Locations

| File | Location | Purpose |
|------|----------|---------|
| Auto-start config | `/autostart_autodown/config.json` | MQTT, YOLO, timing settings |
| System config | `/config/system_config.json` | Vibration, scheduler, web server |
| Camera config | `/config/camera_config.json` | Camera resolution, FPS, motion |
| Requirements | `/requirements_monitoring.txt` | Dependencies (MISSING paho-mqtt!) |

---

## Missing Information Not Being Tracked

### PC/Device Information
- [ ] Hostname
- [ ] IP addresses (ETH, WiFi)
- [ ] MAC address
- [ ] Jetson hardware model (Orin, Xavier, etc.)
- [ ] System uptime
- [ ] OS version
- [ ] Python version

### System Metrics
- [ ] CPU usage (%)
- [ ] Memory usage (%)
- [ ] GPU usage (% - Jetson specific)
- [ ] Disk usage (%)
- [ ] CPU temperature (°C)
- [ ] Network interfaces status

### Application Status
- [ ] Software version
- [ ] Service states (camera, vibration, frying)
- [ ] Configuration version/hash
- [ ] Available ML models
- [ ] Error/warning logs
- [ ] Last restart time

---

## Recommended MQTT Topics

### Current
```
robot/control                      # Just "ON" or "OFF"
```

### Proposed Comprehensive Structure
```
jetson/+device_id+/status         # System health
jetson/+device_id+/camera         # Camera detection data
jetson/+device_id+/vibration      # Vibration readings
jetson/+device_id+/frying         # Cooking session data
jetson/+device_id+/system         # PC/system info
jetson/+device_id+/scheduler      # Work schedule status
jetson/+device_id+/alerts         # Warnings and errors
```

---

## Available System Information Sources

### Python Libraries (Standard)
```
socket          # hostname, IP addresses
platform        # OS, Python version
os              # environment variables
psutil          # CPU, memory, disk, temperature
subprocess      # System commands
```

### Jetson-Specific
```
/proc/device-tree/model           # Hardware model
/sys/devices/virtual/dmi/id/       # System info
```

### Application
```
ServiceManager.get_all_statuses()  # Service states
WorkScheduler.get_status()         # Schedule info
VibrationDetector.get_current_status()  # Vibration state
Config files (JSON)                # Settings
```

---

## Critical Issues to Fix

### 1. Missing Dependency (CRITICAL)
**File:** `/requirements_monitoring.txt`
**Issue:** Uses `paho-mqtt` but not listed
**Fix:** Add `paho-mqtt>=1.6.1` to requirements

### 2. Limited MQTT Scope
**Current:** Only ON/OFF to robot/control
**Needed:** Comprehensive JSON messages with metadata

### 3. No System Info Collection
**Missing:** Module to gather PC/system information
**Create:** `src/core/system_info.py`

### 4. No Centralized MQTT Manager
**Scattered:** MQTT code duplicated in multiple files
**Improve:** Create `src/communication/mqtt_client.py`

---

## Implementation Priority

### Phase 1 (High) - Foundation
1. Add `paho-mqtt` to requirements.txt
2. Create `src/core/system_info.py` for PC info
3. Create `src/communication/mqtt_client.py` for MQTT management
4. Update autostart scripts to use new MQTT module

### Phase 2 (Medium) - Integration
1. Add MQTT to dashboard (`src/gui/dash_app.py`)
2. Add MQTT to vibration detector
3. Add MQTT to frying data collector
4. Add MQTT to work scheduler
5. Implement status topic subscriptions

### Phase 3 (Low) - Enhancement
1. Add TLS/SSL support
2. Add authentication
3. Implement retained messages
4. Add cluster support

---

## File Paths (Absolute)

```
Main Project:          /home/dkutest/my_ai_project/
Auto-start Module:     /home/dkutest/my_ai_project/autostart_autodown/
Core Modules:          /home/dkutest/my_ai_project/src/core/
Monitoring Modules:    /home/dkutest/my_ai_project/src/monitoring/
GUI/Dashboard:         /home/dkutest/my_ai_project/src/gui/
Config Files:          /home/dkutest/my_ai_project/config/
Requirements:          /home/dkutest/my_ai_project/requirements_monitoring.txt
```

---

## Key Code Locations

| Component | File | Lines |
|-----------|------|-------|
| MQTT Setup (GUI) | JETSON1_INTEGRATED.py | 22, 52-58, 113, 145, 355-386 |
| MQTT Publish (GUI) | JETSON1_INTEGRATED.py | 539, 578, 692-702 |
| MQTT Setup (Headless) | ROBOTCAM_HEADLESS.py | 15, 61-67, 84-109 |
| MQTT Publish (Headless) | ROBOTCAM_HEADLESS.py | 132-142, 246, 277 |
| Monitoring System | dash_app.py | 104-294 |
| Vibration Detector | vibration_detector.py | Class VibrationDetector |
| Frying Collector | frying_data_collector.py | Class FryingDataCollector |
| Scheduler | work_scheduler.py | Class WorkScheduler |
| Service Manager | service_manager.py | Class ServiceManager |

---

## Quick Stats

| Metric | Value |
|--------|-------|
| Total Python Files | 20+ |
| Current MQTT Files | 2 |
| MQTT Code Lines | ~150 |
| Supported Messages | 2 ("ON", "OFF") |
| System Components | 5 (Camera, Vibration, Frying, Scheduler, Dashboard) |
| Configuration Files | 3 |
| Docker Containers | 1 |
| Network Mode | Host |
| Timezone | Asia/Seoul |
| Web Server Port | 5000 (Flask) / 8050 (Dash) |
| MQTT Port | 1883 (default) |

---

## Next Steps for Implementation

1. **Read the full analysis:** `/home/dkutest/my_ai_project/MQTT_CODEBASE_ANALYSIS.md`
2. **Understand current code:** Review the files listed in "Key Code Locations"
3. **Fix requirements:** Add `paho-mqtt` to requirements
4. **Design schema:** Decide on JSON message format (see example in section 10 of main analysis)
5. **Create modules:** Build system info collector and centralized MQTT client
6. **Integrate:** Add MQTT to each monitoring component
7. **Test:** Verify messages are published correctly to broker

