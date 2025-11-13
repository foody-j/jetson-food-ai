#!/usr/bin/env python3
"""Simple GPIO test without Jetson.GPIO library"""
import time
import os

# GPIO Pin 7 = GPIO 144 (PA.04)
GPIO_NUM = 144
GPIO_PATH = f"/sys/class/gpio/gpio{GPIO_NUM}"

def gpio_export():
    if not os.path.exists(GPIO_PATH):
        with open("/sys/class/gpio/export", "w") as f:
            f.write(str(GPIO_NUM))
        time.sleep(0.1)
    print(f"GPIO {GPIO_NUM} exported")

def gpio_set_direction(direction):
    with open(f"{GPIO_PATH}/direction", "w") as f:
        f.write(direction)
    print(f"GPIO direction set to {direction}")

def gpio_set_value(value):
    with open(f"{GPIO_PATH}/value", "w") as f:
        f.write(str(value))
    print(f"GPIO value set to {value}")

def gpio_unexport():
    if os.path.exists(GPIO_PATH):
        with open("/sys/class/gpio/unexport", "w") as f:
            f.write(str(GPIO_NUM))
    print(f"GPIO {GPIO_NUM} unexported")

try:
    print("=== GPIO Pin 7 Test (sysfs method) ===")

    gpio_export()
    gpio_set_direction("out")

    print("\n[1] Setting Pin 7 HIGH (3.3V)")
    gpio_set_value(1)
    input("멀티미터로 Pin 7 측정 후 엔터를 누르세요...")

    print("\n[2] Setting Pin 7 LOW (0V)")
    gpio_set_value(0)
    time.sleep(1)

    print("\n테스트 완료!")

except PermissionError:
    print("권한 오류: sudo로 실행하세요")
    print("sudo python3 gpio_test_simple.py")
except Exception as e:
    print(f"에러: {e}")
finally:
    gpio_unexport()
