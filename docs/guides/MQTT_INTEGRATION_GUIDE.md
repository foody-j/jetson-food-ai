# MQTT Integration Guide

Complete guide for integrating MQTT with system information into your monitoring components.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Integration Examples](#integration-examples)
5. [Message Format](#message-format)
6. [Topic Structure](#topic-structure)
7. [Best Practices](#best-practices)

---

## Overview

The MQTT integration system provides:
- **Centralized MQTT client** (`src/communication/mqtt_client.py`)
- **System information collector** (`src/core/system_info.py`)
- **Automatic metadata injection** (timestamp, device info, system metrics)
- **Structured message format** with JSON

### Benefits
✅ No more simple "ON"/"OFF" messages
✅ Rich metadata (IP address, hostname, system metrics)
✅ Standardized message format across all components
✅ Easy debugging and monitoring
✅ Better integration with external systems

---

## Installation

### 1. Install Requirements

```bash
pip3 install -r requirements_monitoring.txt
```

This installs:
- `paho-mqtt>=1.6.1` - MQTT client library
- `psutil>=5.8.0` - System information collection

### 2. Start MQTT Broker

If you don't have mosquitto running:

```bash
# On host Jetson (recommended)
sudo apt install mosquitto mosquitto-clients
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

---

## Quick Start

### Basic Usage

```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.communication.mqtt_client import MQTTClient
from src.core.system_info import SystemInfo

# 1. Create system info
system_info = SystemInfo(
    device_name="Jetson1",
    location="Kitchen"
)

# 2. Create MQTT client
mqtt_client = MQTTClient(
    broker="localhost",
    port=1883,
    client_id="my_component",
    topic_prefix="frying_ai/jetson1",
    system_info=system_info.to_dict()
)

# 3. Connect
if mqtt_client.connect(blocking=True, timeout=5.0):
    print("Connected!")

    # 4. Publish data
    payload = {
        "temperature": 75.5,
        "status": "normal"
    }

    mqtt_client.publish("sensors/temperature", payload)

    # 5. Disconnect
    mqtt_client.disconnect()
```

### Using Context Manager (Recommended)

```python
with MQTTClient(
    broker="localhost",
    port=1883,
    client_id="my_component",
    topic_prefix="frying_ai/jetson1",
    system_info=system_info.to_dict()
) as mqtt_client:

    # Publish messages
    mqtt_client.publish("topic", {"data": "value"})

# Automatically disconnects
```

---

## Integration Examples

### Example 1: Vibration Sensor

```python
#!/usr/bin/env python3
"""Vibration sensor with MQTT integration"""

from src.communication.mqtt_client import MQTTClient
from src.core.system_info import SystemInfo
import time

def main():
    system_info = SystemInfo(device_name="Jetson1", location="Kitchen")

    with MQTTClient(
        broker="localhost",
        port=1883,
        client_id="vibration_monitor",
        topic_prefix="frying_ai/jetson1",
        system_info=system_info.to_dict()
    ) as mqtt:

        while True:
            # Read sensor (example)
            vibration_data = {
                "x_axis": read_x_axis(),
                "y_axis": read_y_axis(),
                "z_axis": read_z_axis(),
                "magnitude": calculate_magnitude(),
                "temperature": read_temperature(),
                "status": "normal" or "warning"
            }

            # Publish
            mqtt.publish("vibration/data", vibration_data)

            time.sleep(1)

if __name__ == "__main__":
    main()
```

### Example 2: Frying Monitoring

```python
#!/usr/bin/env python3
"""Frying session monitoring with MQTT"""

from src.communication.mqtt_client import MQTTClient
from src.core.system_info import SystemInfo
import time

class FryingMonitor:
    def __init__(self):
        self.system_info = SystemInfo(device_name="Jetson1", location="Kitchen")
        self.mqtt = MQTTClient(
            broker="localhost",
            port=1883,
            client_id="frying_monitor",
            topic_prefix="frying_ai/jetson1",
            system_info=self.system_info.to_dict()
        )
        self.mqtt.connect(blocking=True)

    def start_session(self, food_type):
        """Start cooking session"""
        session_data = {
            "event": "session_start",
            "session_id": f"session_{int(time.time())}",
            "food_type": food_type
        }
        self.mqtt.publish("frying/session", session_data)
        return session_data['session_id']

    def update_temperature(self, session_id, temperature):
        """Update cooking temperature"""
        temp_data = {
            "session_id": session_id,
            "temperature": temperature,
            "timestamp": time.time()
        }
        self.mqtt.publish("frying/temperature", temp_data)

    def end_session(self, session_id, status="completed"):
        """End cooking session"""
        session_data = {
            "event": "session_end",
            "session_id": session_id,
            "status": status
        }
        self.mqtt.publish("frying/session", session_data)

    def cleanup(self):
        """Cleanup"""
        self.mqtt.disconnect()

# Usage
monitor = FryingMonitor()
session_id = monitor.start_session("stir_fry")
monitor.update_temperature(session_id, 150)
monitor.end_session(session_id)
monitor.cleanup()
```

### Example 3: Camera Monitoring

```python
#!/usr/bin/env python3
"""Camera monitoring with MQTT"""

from src.communication.mqtt_client import MQTTClient
from src.core.system_info import SystemInfo
import cv2

class CameraMonitor:
    def __init__(self):
        self.system_info = SystemInfo(device_name="Jetson1", location="Kitchen")
        self.mqtt = MQTTClient(
            broker="localhost",
            port=1883,
            client_id="camera_monitor",
            topic_prefix="frying_ai/jetson1",
            system_info=self.system_info.to_dict()
        )
        self.mqtt.connect(blocking=True)

    def on_person_detected(self, confidence):
        """Called when person is detected"""
        detection_data = {
            "event": "person_detected",
            "confidence": confidence,
            "camera_id": 0
        }
        self.mqtt.publish("camera/detection", detection_data)

    def on_motion_detected(self, area):
        """Called when motion is detected"""
        motion_data = {
            "event": "motion_detected",
            "area": area,
            "camera_id": 0
        }
        self.mqtt.publish("camera/motion", motion_data)
```

---

## Message Format

### Automatic Metadata Injection

When you publish a message, the system **automatically adds**:

```json
{
  "timestamp": "2025-10-30T10:30:45.123456",
  "device": {
    "hostname": "jetson1",
    "device_name": "Jetson1",
    "location": "Kitchen",
    "ip_addresses": [
      {"interface": "eth0", "address": "192.168.1.100"}
    ],
    "mac_address": "00:11:22:33:44:55",
    "platform": "Linux",
    "architecture": "aarch64",
    "cpu_count": 6
  },
  "data": {
    // Your payload goes here
  }
}
```

### Your Payload

You only need to provide the data:

```python
payload = {
    "temperature": 75.5,
    "status": "normal"
}

mqtt_client.publish("sensors/temperature", payload)
```

### Disable Metadata (if needed)

```python
mqtt_client.publish(
    "topic",
    payload,
    include_metadata=False  # Just send raw payload
)
```

---

## Topic Structure

### Recommended Topic Hierarchy

```
frying_ai/
├── jetson1/
│   ├── robot/
│   │   └── control          # Robot control commands
│   ├── camera/
│   │   ├── detection        # Person detection events
│   │   └── motion           # Motion detection events
│   ├── vibration/
│   │   └── data             # Vibration sensor readings
│   ├── frying/
│   │   ├── session          # Cooking session events
│   │   └── temperature      # Temperature readings
│   └── system/
│       └── status           # System health status
├── jetson2/
│   └── ...
└── central/
    └── commands             # Central commands to devices
```

### Topic Prefix

The topic prefix is set when creating the MQTT client:

```python
mqtt_client = MQTTClient(
    topic_prefix="frying_ai/jetson1",  # Prefix
    ...
)

# Publish to: frying_ai/jetson1/sensors/temperature
mqtt_client.publish("sensors/temperature", data)
```

---

## Best Practices

### 1. Use Context Manager

```python
# ✅ Good - Automatic cleanup
with MQTTClient(...) as mqtt:
    mqtt.publish("topic", data)

# ❌ Bad - Manual cleanup required
mqtt = MQTTClient(...)
mqtt.connect()
mqtt.publish("topic", data)
mqtt.disconnect()  # Easy to forget!
```

### 2. Check Connection

```python
if mqtt_client.is_connected():
    mqtt_client.publish("topic", data)
else:
    print("Not connected to MQTT broker")
```

### 3. Include System Metrics for Important Events

```python
# For critical events, include system health
payload = {
    "event": "critical_temperature",
    "temperature": 200,
    "system_metrics": system_info.get_dynamic_info()
}
```

### 4. Use Meaningful Topic Names

```python
# ✅ Good
mqtt.publish("vibration/error", data)
mqtt.publish("frying/session_start", data)

# ❌ Bad
mqtt.publish("data", data)
mqtt.publish("msg", data)
```

### 5. QoS Levels

```python
# QoS 0: At most once (fastest, may lose messages)
mqtt.publish("logs", data, qos=0)

# QoS 1: At least once (default, reliable)
mqtt.publish("sensors/temperature", data, qos=1)

# QoS 2: Exactly once (slowest, guaranteed)
mqtt.publish("critical/alarm", data, qos=2)
```

---

## Testing

### Run the Example Script

```bash
# Terminal 1: Subscribe to all messages
python3 test_mqtt_subscriber.py

# Terminal 2: Run integration examples
python3 mqtt_integration_example.py
```

### Test with mosquitto_sub

```bash
# Subscribe to all topics
mosquitto_sub -h localhost -t "frying_ai/#" -v

# Subscribe to specific topic
mosquitto_sub -h localhost -t "frying_ai/jetson1/vibration/data" -v
```

---

## Troubleshooting

### Connection Refused

```
Error: [Errno 111] Connection refused
```

**Solution**: Make sure mosquitto is running:
```bash
sudo systemctl status mosquitto
sudo systemctl start mosquitto
```

### Import Error

```
ImportError: No module named 'src.communication'
```

**Solution**: Add parent directory to path:
```python
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Messages Not Received

1. Check broker is running: `sudo systemctl status mosquitto`
2. Check topic name matches subscription
3. Check QoS level
4. Test with mosquitto_sub: `mosquitto_sub -h localhost -t "#" -v`

---

## Real-World Integration

### Updated Files

The following files have been updated to use the new MQTT system:

1. **autostart_autodown/JETSON1_INTEGRATED.py** - Integrated GUI system
2. **autostart_autodown/ROBOTCAM_HEADLESS.py** - Headless monitoring

### What Changed

**Before:**
```python
import paho.mqtt.client as mqtt
mqtt_client = mqtt.Client()
mqtt_client.publish("robot/control", "ON")
```

**After:**
```python
from src.communication.mqtt_client import MQTTClient
from src.core.system_info import SystemInfo

system_info = SystemInfo(device_name="Jetson1", location="Kitchen")
mqtt_client = MQTTClient(
    broker="localhost",
    topic_prefix="frying_ai/jetson1",
    system_info=system_info.to_dict()
)
mqtt_client.publish("robot/control", {
    "command": "ON",
    "person_detected": True,
    "system_metrics": system_info.get_dynamic_info()
})
```

---

## Next Steps

1. **Add to vibration monitoring**: Integrate MQTT into `src/monitoring/vibration_sensor.py`
2. **Add to frying monitoring**: Integrate MQTT into `src/monitoring/frying_monitor.py`
3. **Dashboard integration**: Display MQTT messages in Dash dashboard
4. **Multi-device**: Set up MQTT on Jetson 2, 3, etc.
5. **Cloud integration**: Forward messages to cloud MQTT broker

---

## Support

- Run examples: `python3 mqtt_integration_example.py`
- Check test scripts: `test_mqtt_publisher.py`, `test_mqtt_subscriber.py`
- Review code: `src/communication/mqtt_client.py`, `src/core/system_info.py`
