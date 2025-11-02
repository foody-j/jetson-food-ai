# MQTT Test Scripts

Quick test scripts to verify MQTT communication with system information.

## Setup

1. **Install MQTT broker** (if not already installed):
   ```bash
   sudo apt update
   sudo apt install mosquitto mosquitto-clients
   sudo systemctl start mosquitto
   sudo systemctl enable mosquitto
   ```

2. **Install Python dependencies**:
   ```bash
   pip3 install paho-mqtt
   # OR
   pip3 install -r requirements_monitoring.txt
   ```

## Quick Test

### Option 1: Test with local broker (localhost)

1. **Terminal 1** - Start subscriber:
   ```bash
   python3 test_mqtt_subscriber.py
   ```

2. **Terminal 2** - Send test message:
   ```bash
   python3 test_mqtt_publisher.py
   ```

### Option 2: Test with command-line tools

1. **Subscribe** (Terminal 1):
   ```bash
   mosquitto_sub -h localhost -t "frying_ai/#" -v
   ```

2. **Publish** (Terminal 2):
   ```bash
   python3 test_mqtt_publisher.py
   ```

## Configuration

Edit the scripts to change broker settings:

```python
BROKER = "localhost"  # Change to broker IP (e.g., "192.168.1.100")
PORT = 1883
```

## Expected Output

### Publisher:
```
=== MQTT Publisher Test ===
Broker: localhost:1883
Topic: frying_ai/test/system_info

Connecting to broker...
✓ Connected to MQTT broker at localhost:1883

Publishing message:
{
  "timestamp": "2025-10-30T10:30:45.123456",
  "device": {
    "hostname": "jetson1",
    "ip_addresses": ["192.168.1.100"],
    "platform": "Linux",
    ...
  },
  "test_data": {
    "message": "Hello from MQTT test",
    "counter": 1
  }
}

✓ Message published
✓ Test completed successfully!
```

### Subscriber:
```
=== MQTT Subscriber Test ===
Broker: localhost:1883
Topic: frying_ai/#

Connecting to broker...
✓ Connected to MQTT broker
✓ Subscribed to topic: frying_ai/#

Waiting for messages...

============================================================
Topic: frying_ai/test/system_info
QoS: 1
Payload:
{
  "timestamp": "2025-10-30T10:30:45.123456",
  "device": { ... },
  "test_data": { ... }
}
============================================================
```

## Troubleshooting

- **Connection refused**: Make sure mosquitto is running: `sudo systemctl status mosquitto`
- **No module 'paho'**: Install with `pip3 install paho-mqtt`
- **No messages received**: Check firewall, broker IP, and topic name

## Next Steps

Once testing works:
1. Integrate into main monitoring system
2. Add more device information (CPU, GPU, temperature)
3. Implement structured topics for different data types
4. Add message persistence and QoS handling
