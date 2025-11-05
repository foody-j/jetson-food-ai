# Stir-Fry Monitoring System Design

## 📋 Analysis of Existing MQTT Protocol

Based on the C# example code from `comm_protocol/MQTTexample/`:

### MQTT Topics
```
AI/RBSensorInfo      → Robot sensor information (published by AI)
AI/RBProcessInfo     → Robot process information (published by AI)
AI/FryInfo           → Fryer/stir-fry information (published by AI)
HR/Status            → Status messages (subscribed by AI)
```

### Message Format
- **Encoding**: UTF-8
- **Format**: JSON (using Newtonsoft.Json)
- **Structure**: `{"FieldName": "value"}`
- **QoS**: 2 (Exactly Once)
- **Retain**: False
- **Port**: 1883 (standard MQTT)
- **Protocol**: MQTT v3.1.1

### Example Messages
```csharp
// Fryer Info
{"FryInfo": "temperature:180,time:5,food:볶음밥"}

// Robot Sensor Info
{"RBSensorInfo": "sensor_data_here"}

// Robot Process Info
{"RBProcessInfo": "process_data_here"}
```

---

## 🎯 Stir-Fry Monitoring Requirements

### What We Need to Receive (via MQTT):

**Topic: `HR/FryControl` or `HR/FryRecipe`** (to be confirmed)
Expected data:
- Food type (음식 종류): String
- Target temperature (설정 온도): Integer (°C)
- Cooking time (설정 시간): Integer (minutes)
- Current fryer temperature (현재 온도): Integer (°C)
- Fryer state (상태): String ("idle", "preheating", "cooking", "done")

**Possible Message Format:**
```json
{
  "FryRecipe": {
    "food_type": "볶음밥",
    "target_temp": 180,
    "cook_time": 5
  }
}
```

**Or:**
```json
{
  "FryStatus": {
    "current_temp": 175,
    "state": "cooking",
    "elapsed_time": 120
  }
}
```

### What We Publish (via MQTT):

**Topic: `AI/FryInfo`** (already defined in their protocol)
We send AI detection/monitoring data:
```json
{
  "FryInfo": {
    "snapshot_count": 25,
    "recording_duration": 150,
    "ai_status": "monitoring",
    "device": "Jetson1"
  }
}
```

---

## 📊 Data Capture Strategy

### Option A: Time-Based Snapshots (RECOMMENDED)

**Trigger**: Automatic when MQTT state = "cooking"

**Frequency**: Every 10 seconds

**Storage**: Images only (NOT video)

**Why Images, Not Video?**
| Metric | Images (10s interval) | Video (30fps) |
|--------|----------------------|---------------|
| 5-min cook | 30 images × 1MB = 30MB | ~500-800MB |
| 100 sessions | 3GB | 50-80GB |
| AI Training | ✅ Easier to label | ❌ Must extract frames |
| Storage Cost | ✅ Minimal | ❌ Very high |
| Processing | ✅ Fast | ❌ Slow decode |

**Calculation:**
- 5-minute cooking session
- 1 snapshot every 10 seconds
- 300 seconds ÷ 10 = **30 snapshots**
- 1MB per JPEG × 30 = **~30MB per session**
- 100 cooking sessions = **~3GB total**

### Snapshot Events:

**Start Capture When:**
- MQTT message: `state = "cooking"` OR
- MQTT message: `current_temp > 50°C` (if no state field)

**Stop Capture When:**
- MQTT message: `state = "done"` OR `state = "idle"` OR
- No MQTT updates for 60 seconds (timeout)

**During Capture:**
- Save image every 10 seconds
- Log MQTT data (temperature, time) with each snapshot
- Update GUI with current stats

---

## 💾 Storage Format

### Directory Structure:
```
/data/stirfry_sessions/
├── session_20251031_143022/
│   ├── metadata.json              ← Session info + all MQTT data
│   ├── frame_0000.jpg             ← t=0s
│   ├── frame_0010.jpg             ← t=10s
│   ├── frame_0020.jpg             ← t=20s
│   └── ...
├── session_20251031_150145/
│   └── ...
└── index.json                     ← Quick lookup of all sessions
```

### metadata.json Format:
```json
{
  "session_id": "20251031_143022",
  "start_time": "2025-10-31T14:30:22",
  "end_time": "2025-10-31T14:35:22",
  "duration_seconds": 300,

  "recipe": {
    "food_type": "볶음밥",
    "target_temp": 180,
    "cook_time": 5
  },

  "snapshots": [
    {
      "seq": 0,
      "timestamp": "2025-10-31T14:30:22",
      "filename": "frame_0000.jpg",
      "fryer_temp": 25,
      "elapsed_seconds": 0,
      "mqtt_data": {
        "state": "preheating",
        "current_temp": 25
      }
    },
    {
      "seq": 1,
      "timestamp": "2025-10-31T14:30:32",
      "filename": "frame_0010.jpg",
      "fryer_temp": 85,
      "elapsed_seconds": 10,
      "mqtt_data": {
        "state": "cooking",
        "current_temp": 85
      }
    }
  ],

  "device_info": {
    "device_name": "Jetson1",
    "location": "Kitchen",
    "camera_index": 1,
    "ip_address": "192.168.1.100"
  },

  "statistics": {
    "total_snapshots": 30,
    "min_temp": 25,
    "max_temp": 185,
    "avg_temp": 175
  }
}
```

### index.json Format:
```json
{
  "sessions": [
    {
      "session_id": "20251031_143022",
      "food_type": "볶음밥",
      "start_time": "2025-10-31T14:30:22",
      "duration": 300,
      "snapshot_count": 30
    },
    {
      "session_id": "20251031_150145",
      "food_type": "야채볶음",
      "start_time": "2025-10-31T15:01:45",
      "duration": 420,
      "snapshot_count": 42
    }
  ],
  "total_sessions": 2,
  "total_snapshots": 72,
  "total_size_mb": 72
}
```

---

## 🎨 GUI Changes

### Current GUI (with Start/Stop buttons):
```
┌──────────────────────────┐
│  볶음 모니터링            │
├──────────────────────────┤
│  [Camera Preview]        │
├──────────────────────────┤
│ 녹화: OFF                │
│ 저장: 0장                │
│ [ 시작 ]  [ 중지 ]       │ ← Remove these
└──────────────────────────┘
```

### New GUI (MQTT-driven):
```
┌────────────────────────────┐
│  볶음 모니터링              │
├────────────────────────────┤
│  [Camera Preview]          │
│  (or hidden when idle)     │
├────────────────────────────┤
│ 음식: 볶음밥                │ ← From MQTT
│ 설정: 180°C / 5분          │ ← From MQTT
│ 현재: 175°C ⬆ (조리 중)    │ ← From MQTT
│ 경과: 2분 30초              │ ← Calculated
│ 저장: 15장                  │ ← Local count
├────────────────────────────┤
│ MQTT: 연결됨 ✓             │ ← Connection status
└────────────────────────────┘
```

### Developer Mode (for testing):
```
┌────────────────────────────┐
│  볶음 모니터링 (개발자)     │
├────────────────────────────┤
│  [Camera Preview]          │
├────────────────────────────┤
│ 음식: 볶음밥                │
│ 현재: 175°C (조리 중)       │
│ 저장: 15장 (2분 30초)       │
├────────────────────────────┤
│ [ 수동 시작 ]  [ 수동 중지 ] │ ← Only in dev mode
│ [ 테스트 MQTT 전송 ]        │ ← For testing
└────────────────────────────┘
```

---

## 🔧 Implementation Plan

### 1. MQTT Subscriber Module

**File**: `src/communication/stirfry_mqtt_subscriber.py`

```python
import json
from datetime import datetime
from src.communication.mqtt_client import MQTTClient

class StirFryMQTTSubscriber:
    def __init__(self, broker, port, callback):
        self.client = MQTTClient(
            broker=broker,
            port=port,
            client_id="Jetson1_StirFry",
            topic_prefix="AI"
        )
        self.callback = callback
        self.current_recipe = None
        self.current_status = None

    def start(self):
        """Start MQTT subscriber"""
        self.client.connect()

        # Subscribe to fryer control topics
        self.client.subscribe("HR/FryRecipe", self.on_recipe_received)
        self.client.subscribe("HR/FryStatus", self.on_status_received)

    def on_recipe_received(self, topic, payload):
        """Handle recipe data"""
        try:
            data = json.loads(payload)
            self.current_recipe = data.get("FryRecipe", {})
            self.callback("recipe", self.current_recipe)
        except Exception as e:
            print(f"[MQTT] Recipe parse error: {e}")

    def on_status_received(self, topic, payload):
        """Handle status updates"""
        try:
            data = json.loads(payload)
            self.current_status = data.get("FryStatus", {})

            # Trigger snapshot if cooking
            if self.current_status.get("state") == "cooking":
                self.callback("status_cooking", self.current_status)
            elif self.current_status.get("state") == "done":
                self.callback("status_done", self.current_status)
            else:
                self.callback("status_idle", self.current_status)
        except Exception as e:
            print(f"[MQTT] Status parse error: {e}")

    def publish_ai_status(self, snapshot_count, duration):
        """Publish AI monitoring status"""
        payload = {
            "FryInfo": {
                "snapshot_count": snapshot_count,
                "recording_duration": duration,
                "ai_status": "monitoring",
                "device": "Jetson1",
                "timestamp": datetime.now().isoformat()
            }
        }
        self.client.publish("AI/FryInfo", payload)
```

### 2. Session Manager

**File**: `src/stirfry/session_manager.py`

```python
import os
import json
import cv2
from datetime import datetime
from pathlib import Path

class StirFrySessionManager:
    def __init__(self, base_path="/data/stirfry_sessions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        self.current_session = None
        self.session_dir = None
        self.snapshot_count = 0

    def start_session(self, recipe_data):
        """Start new cooking session"""
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_dir = self.base_path / f"session_{session_id}"
        self.session_dir.mkdir(exist_ok=True)

        self.current_session = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "recipe": recipe_data,
            "snapshots": [],
            "device_info": self.get_device_info()
        }

        self.snapshot_count = 0
        print(f"[Session] Started: {session_id}")

    def save_snapshot(self, frame, mqtt_data):
        """Save snapshot and metadata"""
        if not self.current_session:
            return

        # Save image
        filename = f"frame_{self.snapshot_count:04d}.jpg"
        filepath = self.session_dir / filename
        cv2.imwrite(str(filepath), frame, [cv2.IMWRITE_JPEG_QUALITY, 90])

        # Add to metadata
        snapshot_meta = {
            "seq": self.snapshot_count,
            "timestamp": datetime.now().isoformat(),
            "filename": filename,
            "fryer_temp": mqtt_data.get("current_temp", 0),
            "elapsed_seconds": self.snapshot_count * 10,
            "mqtt_data": mqtt_data
        }
        self.current_session["snapshots"].append(snapshot_meta)

        self.snapshot_count += 1
        print(f"[Session] Snapshot {self.snapshot_count} saved")

    def end_session(self):
        """Finalize and save session metadata"""
        if not self.current_session:
            return

        self.current_session["end_time"] = datetime.now().isoformat()
        self.current_session["duration_seconds"] = self.snapshot_count * 10

        # Calculate statistics
        temps = [s["fryer_temp"] for s in self.current_session["snapshots"]]
        self.current_session["statistics"] = {
            "total_snapshots": self.snapshot_count,
            "min_temp": min(temps) if temps else 0,
            "max_temp": max(temps) if temps else 0,
            "avg_temp": sum(temps) // len(temps) if temps else 0
        }

        # Save metadata.json
        meta_path = self.session_dir / "metadata.json"
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_session, f, ensure_ascii=False, indent=2)

        print(f"[Session] Ended: {self.current_session['session_id']}")

        # Update index
        self.update_index()

        self.current_session = None
        self.snapshot_count = 0

    def get_device_info(self):
        """Get device information"""
        from src.core.system_info import SystemInfo
        sys_info = SystemInfo(device_name="Jetson1", location="Kitchen")
        return sys_info.get_static_info()

    def update_index(self):
        """Update session index file"""
        index_path = self.base_path / "index.json"

        # Load existing index
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {"sessions": [], "total_sessions": 0, "total_snapshots": 0}

        # Add current session summary
        if self.current_session:
            index["sessions"].append({
                "session_id": self.current_session["session_id"],
                "food_type": self.current_session["recipe"].get("food_type", "Unknown"),
                "start_time": self.current_session["start_time"],
                "duration": self.current_session.get("duration_seconds", 0),
                "snapshot_count": self.snapshot_count
            })
            index["total_sessions"] += 1
            index["total_snapshots"] += self.snapshot_count

        # Save index
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
```

### 3. Integration into JETSON1_INTEGRATED.py

**Key changes:**

1. **Initialize MQTT subscriber** for stir-fry
2. **Auto-start/stop** snapshot capture based on MQTT state
3. **Update GUI** with MQTT data
4. **Hide/show start/stop buttons** based on developer mode

```python
# In __init__
self.stirfry_mqtt = StirFryMQTTSubscriber(
    broker=MQTT_BROKER,
    port=MQTT_PORT,
    callback=self.handle_stirfry_mqtt
)
self.stirfry_session_manager = StirFrySessionManager()
self.stirfry_mqtt.start()

# Snapshot timer
self.stirfry_snapshot_timer = None
self.stirfry_last_snapshot = None

def handle_stirfry_mqtt(self, event_type, data):
    """Handle MQTT events for stir-fry"""
    if event_type == "recipe":
        # Update GUI with recipe data
        food = data.get("food_type", "Unknown")
        temp = data.get("target_temp", 0)
        time_min = data.get("cook_time", 0)
        self.stirfry_recipe_label.config(
            text=f"음식: {food} | 설정: {temp}°C / {time_min}분"
        )

    elif event_type == "status_cooking":
        # Start session if not already started
        if not self.stirfry_session_manager.current_session:
            self.stirfry_session_manager.start_session(self.current_recipe)
            self.start_stirfry_snapshot_timer()

        # Update GUI
        temp = data.get("current_temp", 0)
        state = data.get("state", "idle")
        self.stirfry_status_label.config(
            text=f"현재: {temp}°C ({state})"
        )

    elif event_type == "status_done":
        # Stop session
        if self.stirfry_session_manager.current_session:
            self.stop_stirfry_snapshot_timer()
            self.stirfry_session_manager.end_session()

def start_stirfry_snapshot_timer(self):
    """Start 10-second snapshot timer"""
    if self.stirfry_snapshot_timer:
        return

    def capture():
        if self.stirfry_cap and self.stirfry_cap.isOpened():
            ok, frame = self.stirfry_cap.read()
            if ok:
                self.stirfry_session_manager.save_snapshot(
                    frame,
                    self.current_mqtt_status
                )

        # Schedule next capture in 10 seconds
        self.stirfry_snapshot_timer = self.root.after(10000, capture)

    capture()  # First capture immediately

def stop_stirfry_snapshot_timer(self):
    """Stop snapshot timer"""
    if self.stirfry_snapshot_timer:
        self.root.after_cancel(self.stirfry_snapshot_timer)
        self.stirfry_snapshot_timer = None
```

---

## 🧪 Testing Strategy

### 1. Test MQTT Connection
```bash
# Subscribe to test topic
mosquitto_sub -h localhost -t "HR/#" -v

# Publish test recipe
mosquitto_pub -h localhost -t "HR/FryRecipe" \
  -m '{"FryRecipe":{"food_type":"볶음밥","target_temp":180,"cook_time":5}}'

# Publish test status
mosquitto_pub -h localhost -t "HR/FryStatus" \
  -m '{"FryStatus":{"current_temp":175,"state":"cooking"}}'
```

### 2. Test Snapshot Capture
1. Start GUI
2. Send cooking MQTT message
3. Verify snapshots saved every 10 seconds
4. Send done MQTT message
5. Check `/data/stirfry_sessions/` for session folder
6. Verify `metadata.json` contains all data

### 3. Developer Mode Testing
- Enable developer mode
- Use manual start/stop buttons
- Verify MQTT still works
- Test without MQTT connection

---

## 📝 Questions to Confirm

Before implementation, please confirm:

1. **MQTT Topic Names** - Are these correct?
   - Subscribe: `HR/FryRecipe`, `HR/FryStatus`
   - Publish: `AI/FryInfo`

2. **Message Fields** - What exact fields will be in messages?
   - Food type field name?
   - Temperature field name?
   - State field name?

3. **Snapshot Interval** - Is 10 seconds good, or different frequency?

4. **Storage Location** - Is `/data/stirfry_sessions/` okay?

5. **Start/Stop Buttons** - Should they:
   - Be hidden completely (MQTT only)?
   - Visible only in developer mode?
   - Always visible (manual override)?

6. **Auto-Start Trigger** - What triggers snapshot capture?
   - `state == "cooking"`?
   - `current_temp > 50`?
   - Both?

---

## 🚀 Next Steps

Once you confirm the above questions, I'll:

1. Create the Python modules
2. Update JETSON1_INTEGRATED.py
3. Test with your MQTT broker
4. Document the final protocol

Ready to proceed when you are! 🎯
