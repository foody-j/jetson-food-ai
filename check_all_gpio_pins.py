#!/usr/bin/env python3
"""
Jetson Orin Nano GPIO 전체 핀 상태 확인 스크립트
쇼트 발생 후 핀 상태 점검용
"""

import Jetson.GPIO as GPIO
import time

# BOARD 모드로 설정
GPIO.setmode(GPIO.BOARD)

# 40핀 헤더의 GPIO 핀들 (전원/접지 제외)
gpio_pins = {
    7: "GPIO216 (AUDIO_MCLK)",
    11: "GPIO112 (UART1_RTS)",
    12: "GPIO113 (I2S0_SCLK)",
    13: "GPIO114 (SPI1_SCK)",
    15: "GPIO115 (GPIO_DIS5)",
    16: "GPIO116 (SPI1_CS1)",
    18: "GPIO117 (SPI1_CS0)",
    19: "GPIO118 (SPI0_MOSI)",
    21: "GPIO119 (SPI0_MISO)",
    22: "GPIO120 (SPI1_MISO)",
    23: "GPIO121 (SPI0_SCK)",
    24: "GPIO122 (SPI0_CS0)",
    26: "GPIO123 (SPI0_CS1)",
    29: "GPIO124 (GPIO01)",
    31: "GPIO125 (GPIO02)",
    32: "GPIO126 (GPIO03)",
    33: "GPIO127 (GPIO04)",
    35: "GPIO128 (I2S0_FS)",
    36: "GPIO129 (UART1_CTS)",
    37: "GPIO130 (SPI1_MOSI)",
    38: "GPIO131 (I2S0_SDIN)",
    40: "GPIO132 (I2S0_SDOUT)"
}

print("=" * 70)
print("Jetson Orin Nano GPIO 핀 상태 확인")
print("=" * 70)
print(f"확인 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print(f"{'핀 번호':<8} {'GPIO 이름':<35} {'상태':<10}")
print("-" * 70)

error_pins = []
high_pins = []
low_pins = []

for pin, description in sorted(gpio_pins.items()):
    try:
        GPIO.setup(pin, GPIO.IN)
        state = GPIO.input(pin)
        state_str = "HIGH (1)" if state else "LOW (0)"

        if state:
            high_pins.append(pin)
        else:
            low_pins.append(pin)

        print(f"{pin:<8} {description:<35} {state_str:<10}")

    except Exception as e:
        error_pins.append(pin)
        print(f"{pin:<8} {description:<35} ERROR: {str(e)}")

print("=" * 70)
print("\n요약:")
print(f"  정상 핀: {len(gpio_pins) - len(error_pins)}개")
print(f"  HIGH 상태: {len(high_pins)}개 - {high_pins}")
print(f"  LOW 상태: {len(low_pins)}개 - {low_pins}")

if error_pins:
    print(f"  ⚠️  오류 핀: {len(error_pins)}개 - {error_pins}")
    print("\n⚠️  경고: 일부 핀에서 오류 발생! 하드웨어 점검 필요!")
else:
    print("\n✓ 모든 핀 정상 읽기 완료")

print("=" * 70)

# 정리
GPIO.cleanup()
print("\nGPIO cleanup 완료")
