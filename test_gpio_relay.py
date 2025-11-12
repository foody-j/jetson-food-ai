#!/usr/bin/env python3
"""
GPIO Relay Test Script for Jetson Orin Nano
SSR 릴레이 테스트용 스크립트
"""

import Jetson.GPIO as GPIO
import time
import sys

# GPIO 핀 설정 (BOARD 모드 - 물리적 핀 번호 사용)
RELAY_PIN = 7  # 물리적 7번 핀 (GPIO492)
# 다른 추천 핀: 11, 13, 15, 16, 18

def setup_gpio():
    """GPIO 초기화"""
    print("[GPIO] 초기화 중...")
    GPIO.setmode(GPIO.BOARD)  # BOARD 모드 사용 (물리적 핀 번호)
    GPIO.setup(RELAY_PIN, GPIO.OUT, initial=GPIO.LOW)
    print(f"[GPIO] 핀 {RELAY_PIN} 출력 모드로 설정 완료")

def cleanup_gpio():
    """GPIO 정리"""
    print("[GPIO] GPIO 정리 중...")
    GPIO.cleanup()
    print("[GPIO] GPIO 정리 완료")

def test_relay():
    """릴레이 ON/OFF 테스트"""
    try:
        setup_gpio()

        print("\n" + "="*50)
        print("릴레이 테스트 시작")
        print(f"사용 핀: 물리적 {RELAY_PIN}번 핀")
        print("="*50 + "\n")

        # 5번 ON/OFF 반복
        for i in range(5):
            print(f"[{i+1}/5] 릴레이 ON (3.3V 출력)")
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            time.sleep(2)

            print(f"[{i+1}/5] 릴레이 OFF (0V 출력)")
            GPIO.output(RELAY_PIN, GPIO.LOW)
            time.sleep(2)

        print("\n[완료] 테스트 완료!")
        print("멀티미터로 전압 확인:")
        print(f"  - 7번 핀 (GPIO)과 GND(6번 핀) 사이 전압 측정")
        print("  - HIGH일 때: 약 3.3V")
        print("  - LOW일 때: 약 0V")

    except KeyboardInterrupt:
        print("\n\n[중단] 사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n[오류] {e}")
        print("\nGPIO 사용 권한이 필요합니다:")
        print("  sudo python3 test_gpio_relay.py")
    finally:
        cleanup_gpio()

def manual_control():
    """수동 제어 모드"""
    try:
        setup_gpio()

        print("\n" + "="*50)
        print("수동 제어 모드")
        print("="*50)
        print("명령:")
        print("  1 또는 on  : 릴레이 ON")
        print("  0 또는 off : 릴레이 OFF")
        print("  q 또는 quit: 종료")
        print("="*50 + "\n")

        while True:
            cmd = input("명령 입력: ").strip().lower()

            if cmd in ['q', 'quit', 'exit']:
                print("종료합니다.")
                break
            elif cmd in ['1', 'on']:
                GPIO.output(RELAY_PIN, GPIO.HIGH)
                print("✓ 릴레이 ON (3.3V)")
            elif cmd in ['0', 'off']:
                GPIO.output(RELAY_PIN, GPIO.LOW)
                print("✓ 릴레이 OFF (0V)")
            else:
                print("❌ 잘못된 명령입니다.")

    except KeyboardInterrupt:
        print("\n\n[중단] 사용자가 중단했습니다.")
    except Exception as e:
        print(f"\n[오류] {e}")
    finally:
        cleanup_gpio()

if __name__ == "__main__":
    print("="*50)
    print("Jetson Orin Nano GPIO 릴레이 테스트")
    print("="*50)
    print("\n모드 선택:")
    print("  1. 자동 테스트 (5번 ON/OFF 반복)")
    print("  2. 수동 제어")

    if len(sys.argv) > 1:
        mode = sys.argv[1]
    else:
        mode = input("\n선택 (1 또는 2): ").strip()

    if mode == '1':
        test_relay()
    elif mode == '2':
        manual_control()
    else:
        print("잘못된 선택입니다.")
        sys.exit(1)
