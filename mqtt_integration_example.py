#!/usr/bin/env python3
"""
MQTT Integration Example
Shows how to integrate MQTT with system info into any monitoring component
"""

import sys
import os
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.communication.mqtt_client import MQTTClient
from src.core.system_info import SystemInfo

# Example 1: Simple usage
def example_simple():
    """Simple MQTT publish example"""
    print("=== Example 1: Simple Usage ===\n")

    # Create system info
    system_info = SystemInfo(device_name="Jetson1", location="Kitchen")

    # Create MQTT client
    mqtt_client = MQTTClient(
        broker="localhost",
        port=1883,
        client_id="example_simple",
        topic_prefix="frying_ai/jetson1",
        system_info=system_info.to_dict()
    )

    # Connect
    if mqtt_client.connect(blocking=True, timeout=5.0):
        print("Connected to MQTT broker\n")

        # Publish a message
        payload = {
            "sensor": "temperature",
            "value": 75.5,
            "unit": "celsius",
            "status": "normal"
        }

        mqtt_client.publish("sensors/temperature", payload)
        print(f"Published: {payload}\n")

        time.sleep(1)
        mqtt_client.disconnect()
        print("Disconnected\n")
    else:
        print("Failed to connect\n")


# Example 2: Context manager
def example_context_manager():
    """Using context manager for automatic cleanup"""
    print("=== Example 2: Context Manager ===\n")

    system_info = SystemInfo(device_name="Jetson1", location="Kitchen")

    # Context manager automatically connects and disconnects
    with MQTTClient(
        broker="localhost",
        port=1883,
        client_id="example_context",
        topic_prefix="frying_ai/jetson1",
        system_info=system_info.to_dict()
    ) as mqtt_client:
        # Publish multiple messages
        for i in range(3):
            payload = {
                "message_number": i + 1,
                "data": f"Test message {i + 1}"
            }
            mqtt_client.publish(f"test/message_{i+1}", payload)
            print(f"Published message {i + 1}")
            time.sleep(0.5)

    print("Automatically disconnected\n")


# Example 3: Vibration sensor integration
def example_vibration_sensor():
    """Example: Integrating with vibration sensor"""
    print("=== Example 3: Vibration Sensor Integration ===\n")

    system_info = SystemInfo(device_name="Jetson1", location="Kitchen")

    with MQTTClient(
        broker="localhost",
        port=1883,
        client_id="vibration_monitor",
        topic_prefix="frying_ai/jetson1",
        system_info=system_info.to_dict()
    ) as mqtt_client:

        # Simulate vibration sensor readings
        for i in range(5):
            # Simulated vibration data
            vibration_data = {
                "x_axis": 0.5 + (i * 0.1),
                "y_axis": 0.3 + (i * 0.05),
                "z_axis": 0.8 + (i * 0.15),
                "magnitude": 1.0 + (i * 0.2),
                "temperature": 25.0 + i,
                "status": "normal" if i < 3 else "warning"
            }

            mqtt_client.publish("vibration/data", vibration_data)
            print(f"Published vibration reading {i + 1}: magnitude={vibration_data['magnitude']:.2f}")
            time.sleep(1)

    print("Vibration monitoring stopped\n")


# Example 4: Frying session monitoring
def example_frying_session():
    """Example: Integrating with frying monitoring"""
    print("=== Example 4: Frying Session Monitoring ===\n")

    system_info = SystemInfo(device_name="Jetson1", location="Kitchen")

    with MQTTClient(
        broker="localhost",
        port=1883,
        client_id="frying_monitor",
        topic_prefix="frying_ai/jetson1",
        system_info=system_info.to_dict()
    ) as mqtt_client:

        # Session start
        session_data = {
            "event": "session_start",
            "session_id": f"session_{int(time.time())}",
            "food_type": "stir_fry",
            "estimated_duration_min": 10
        }
        mqtt_client.publish("frying/session", session_data)
        print(f"Session started: {session_data['session_id']}")

        # Simulated temperature readings during cooking
        for i in range(5):
            temp_data = {
                "event": "temperature_reading",
                "session_id": session_data['session_id'],
                "temperature": 150 + (i * 10),
                "duration_seconds": i * 30,
                "phase": "heating" if i < 2 else "cooking"
            }
            mqtt_client.publish("frying/temperature", temp_data)
            print(f"Temperature: {temp_data['temperature']}°C - Phase: {temp_data['phase']}")
            time.sleep(1)

        # Session end
        session_data.update({
            "event": "session_end",
            "duration_seconds": 150,
            "status": "completed"
        })
        mqtt_client.publish("frying/session", session_data)
        print(f"Session completed: {session_data['session_id']}\n")


# Example 5: Full system status
def example_full_system_status():
    """Example: Publishing full system status with dynamic metrics"""
    print("=== Example 5: Full System Status ===\n")

    system_info = SystemInfo(device_name="Jetson1", location="Kitchen")

    with MQTTClient(
        broker="localhost",
        port=1883,
        client_id="system_monitor",
        topic_prefix="frying_ai/jetson1",
        system_info=system_info.to_dict()
    ) as mqtt_client:

        # Get full system info (static + dynamic)
        full_info = system_info.get_full_info()

        # Publish system status
        status_payload = {
            "status": "online",
            "services": {
                "camera_monitoring": "active",
                "vibration_sensor": "active",
                "frying_detection": "active"
            },
            "metrics": system_info.get_dynamic_info()
        }

        mqtt_client.publish("system/status", status_payload)

        print("System Status Published:")
        print(f"  CPU: {status_payload['metrics'].get('cpu_percent', 'N/A')}%")
        print(f"  Memory: {status_payload['metrics'].get('memory', {}).get('percent', 'N/A')}%")
        print(f"  Disk: {status_payload['metrics'].get('disk', {}).get('percent', 'N/A')}%")
        if 'gpu' in status_payload['metrics']:
            gpu_temp = status_payload['metrics']['gpu'].get('temperature_c')
            if gpu_temp:
                print(f"  GPU Temp: {gpu_temp}°C")
        print()


def main():
    """Run all examples"""
    print("=" * 60)
    print("MQTT Integration Examples")
    print("=" * 60)
    print()

    try:
        example_simple()
        time.sleep(1)

        example_context_manager()
        time.sleep(1)

        example_vibration_sensor()
        time.sleep(1)

        example_frying_session()
        time.sleep(1)

        example_full_system_status()

        print("=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\nExamples interrupted by user")
    except Exception as e:
        print(f"\n\nError running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
