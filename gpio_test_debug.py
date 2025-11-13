#!/usr/bin/env python3
# GPIO 출력 디버그 - 레벨 시프터 문제 진단

import gpiod
import time

CHIP = "gpiochip0"
LINE = 8  # 물리적 핀 12번

def main():
    chip = gpiod.Chip(CHIP)
    line = chip.get_line(LINE)
    line.request(consumer="gpio_debug", type=gpiod.LINE_REQ_DIR_OUT, default_vals=[0])

    print("=" * 60)
    print("GPIO 출력 디버그 테스트")
    print("=" * 60)
    print(f"핀: gpiochip0 line {LINE} (물리적 12번)")
    print("")
    print("레벨 시프터 연결 확인:")
    print("  Jetson 3.3V (1번) → 레벨시프터 LV")
    print("  Jetson 5V (2번)   → 레벨시프터 HV")
    print("  Jetson GND (6번)  → 레벨시프터 GND")
    print("  Jetson 12번 핀    → 레벨시프터 LV1")
    print("")
    print("측정:")
    print("  1) 12번 핀 직접: 멀티미터 빨간색 → 12번 핀, 검은색 → GND")
    print("  2) LV1 핀:       멀티미터 빨간색 → LV1, 검은색 → GND")
    print("  3) HV1 핀:       멀티미터 빨간색 → HV1, 검은색 → GND")
    print("=" * 60)
    print("")

    try:
        while True:
            # LOW 출력
            line.set_value(0)
            print("▼ LOW 출력 (5초간)")
            print("  12번 핀: 0V 예상")
            print("  LV1: 0V 예상")
            print("  HV1: 0V 예상")
            time.sleep(5)

            # HIGH 출력
            line.set_value(1)
            print("▲ HIGH 출력 (5초간)")
            print("  12번 핀: 3.3V 예상")
            print("  LV1: 3.3V 예상")
            print("  HV1: 5V 예상")
            time.sleep(5)
            print("")

    except KeyboardInterrupt:
        print("\n종료 중...")
    finally:
        line.release()
        print("완료")

if __name__ == '__main__':
    main()
