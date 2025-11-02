#!/usr/bin/env python3
"""
MQTT Subscriber Test - Receives and displays messages
Usage: python3 test_mqtt_subscriber.py
"""

import paho.mqtt.client as mqtt
import json

# MQTT Configuration
BROKER = "localhost"  # Change to your MQTT broker IP
PORT = 1883
TOPIC = "frying_ai/#"  # Subscribe to all frying_ai topics

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        print(f"✓ Subscribed to topic: {TOPIC}")
        print("\nWaiting for messages... (Press Ctrl+C to stop)\n")
    else:
        print(f"✗ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    print(f"{'='*60}")
    print(f"Topic: {msg.topic}")
    print(f"QoS: {msg.qos}")
    print(f"Payload:")

    try:
        # Try to parse as JSON
        payload = json.loads(msg.payload.decode())
        print(json.dumps(payload, indent=2))
    except:
        # If not JSON, print as string
        print(msg.payload.decode())

    print(f"{'='*60}\n")

def main():
    print("=== MQTT Subscriber Test ===")
    print(f"Broker: {BROKER}:{PORT}")
    print(f"Topic: {TOPIC}\n")

    # Create MQTT client
    client = mqtt.Client(client_id="test_subscriber")
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        # Connect to broker
        print("Connecting to broker...")
        client.connect(BROKER, PORT, 60)

        # Start loop (blocking)
        client.loop_forever()

    except KeyboardInterrupt:
        print("\n\n✓ Stopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        client.disconnect()
        print("Disconnected from broker")

if __name__ == "__main__":
    main()
