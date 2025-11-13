import Jetson.GPIO as GPIO

GPIO.setmode(GPIO.BOARD)
GPIO.setup(11, GPIO.OUT)

print("Pin 11 HIGH")
GPIO.output(11, GPIO.HIGH)

input("멀티미터로 Pin 11 측정 후 엔터...")

GPIO.output(11, GPIO.LOW)
print("Pin 11 LOW")
GPIO.cleanup()
