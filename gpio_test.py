import Jetson.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7, GPIO.OUT)

print("Pin 7 HIGH")
GPIO.output(7, GPIO.HIGH)

input("멀티미터로 측정 후 엔터...")

GPIO.output(7, GPIO.LOW)
print("Pin 7 LOW")
GPIO.cleanup()