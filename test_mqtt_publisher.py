#!/usr/bin/env python3
"""
MQTT Publisher Test - Sends system information
Usage: python3 test_mqtt_publisher.py
"""

import paho.mqtt.client as mqtt
import json
import socket
import time
from datetime import datetime
import platform

# MQTT Configuration
BROKER = "localhost"  # Change to your MQTT broker IP
PORT = 1883
TOPIC = "frying_ai/test/system_info"

def get_system_info():
    """Collect system information"""
    hostname = socket.gethostname()

    # Get all IP addresses
    ip_addresses = []
    try:
        # Get all network interfaces
        addrs = socket.getaddrinfo(hostname, None)
        for addr in addrs:
            ip = addr[4][0]
            if ip not in ip_addresses and not ip.startswith('127.'):
                ip_addresses.append(ip)
    except:
        ip_addresses = ['unknown']

    return {
        "hostname": hostname,
        "ip_addresses": ip_addresses,
        "platform": platform.system(),
        "platform_release": platform.release(),
        "architecture": platform.machine(),
        "python_version": platform.python_version()
    }

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {BROKER}:{PORT}")
    else:
        print(f"✗ Connection failed with code {rc}")

def on_publish(client, userdata, mid):
    print(f"✓ Message published (mid: {mid})")

def main():
    print("=== MQTT Publisher Test ===")
    print(f"Broker: {BROKER}:{PORT}")
    print(f"Topic: {TOPIC}\n")

    # Create MQTT client
    client = mqtt.Client(client_id="test_publisher")
    client.on_connect = on_connect
    client.on_publish = on_publish

    try:
        # Connect to broker
        print("Connecting to broker...")
        client.connect(BROKER, PORT, 60)
        client.loop_start()

        time.sleep(1)  # Wait for connection

        # Collect system info
        system_info = get_system_info()

        # Create message with metadata
        message = {
            "timestamp": datetime.now().isoformat(),
            "device": system_info,
            "test_data": {
                "message": "Hello from MQTT test",
                "counter": 1
            }
        }

        # Publish message
        print("\nPublishing message:")
        print(json.dumps(message, indent=2))

        result = client.publish(TOPIC, json.dumps(message), qos=1)
        result.wait_for_publish()

        time.sleep(1)

        print("\n✓ Test completed successfully!")

    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print("Disconnected from broker")

if __name__ == "__main__":
    main()
