#!/usr/bin/env python3
"""
Jetson Orin Nano Super GPIO 전체 핀 상태 확인 스크립트
libgpiod 사용 (Jetson.GPIO 대체)
쇼트 발생 후 핀 상태 점검용
"""

import gpiod
import time

# Jetson Orin Nano 40핀 헤더 매핑 (BOARD 모드 기준)
# 물리적 핀 번호 -> (chip, line, 설명)
gpio_pin_mapping = {
    7: (0, 216, "GPIO216 (AUDIO_MCLK)"),
    11: (0, 112, "GPIO112 (UART1_RTS)"),
    12: (0, 113, "GPIO113 (I2S0_SCLK)"),
    13: (0, 114, "GPIO114 (SPI1_SCK)"),
    15: (0, 115, "GPIO115 (GPIO_DIS5)"),
    16: (0, 116, "GPIO116 (SPI1_CS1)"),
    18: (0, 117, "GPIO117 (SPI1_CS0)"),
    19: (0, 118, "GPIO118 (SPI0_MOSI)"),
    21: (0, 119, "GPIO119 (SPI0_MISO)"),
    22: (0, 120, "GPIO120 (SPI1_MISO)"),
    23: (0, 121, "GPIO121 (SPI0_SCK)"),
    24: (0, 122, "GPIO122 (SPI0_CS0)"),
    26: (0, 123, "GPIO123 (SPI0_CS1)"),
    29: (0, 124, "GPIO124 (GPIO01)"),
    31: (0, 125, "GPIO125 (GPIO02)"),
    32: (0, 126, "GPIO126 (GPIO03)"),
    33: (0, 127, "GPIO127 (GPIO04)"),
    35: (0, 128, "GPIO128 (I2S0_FS)"),
    36: (0, 129, "GPIO129 (UART1_CTS)"),
    37: (0, 130, "GPIO130 (SPI1_MOSI)"),
    38: (0, 131, "GPIO131 (I2S0_SDIN)"),
    40: (0, 132, "GPIO132 (I2S0_SDOUT)")
}

print("=" * 70)
print("Jetson Orin Nano Super GPIO 핀 상태 확인 (libgpiod)")
print("=" * 70)
print(f"확인 시각: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)
print(f"{'핀 번호':<8} {'GPIO 이름':<35} {'상태':<10}")
print("-" * 70)

error_pins = []
high_pins = []
low_pins = []

# GPIO chip 열기
try:
    chip0 = gpiod.Chip('gpiochip0')
    chip1 = gpiod.Chip('gpiochip1')
    chips = {0: chip0, 1: chip1}
except Exception as e:
    print(f"❌ GPIO chip 열기 실패: {e}")
    print("sudo 권한이 필요하거나 gpio 그룹에 속해야 합니다:")
    print("  sudo usermod -a -G gpio $USER")
    print("  (재로그인 필요)")
    exit(1)

for pin, (chip_num, line_num, description) in sorted(gpio_pin_mapping.items()):
    try:
        chip = chips[chip_num]
        line = chip.get_line(line_num)

        # 입력 모드로 설정하고 값 읽기
        line.request(consumer="gpio_check", type=gpiod.LINE_REQ_DIR_IN)
        state = line.get_value()
        line.release()

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
print(f"  정상 핀: {len(gpio_pin_mapping) - len(error_pins)}개")
print(f"  HIGH 상태: {len(high_pins)}개 - {high_pins}")
print(f"  LOW 상태: {len(low_pins)}개 - {low_pins}")

if error_pins:
    print(f"  ⚠️  오류 핀: {len(error_pins)}개 - {error_pins}")
    print("\n⚠️  경고: 일부 핀에서 오류 발생! 하드웨어 점검 필요!")
else:
    print("\n✓ 모든 핀 정상 읽기 완료")

print("=" * 70)

# Chip 닫기
chip0.close()
chip1.close()
print("\nGPIO cleanup 완료")
