#!/usr/bin/env python3
import argparse
import os
import sys
import time

try:
    import serial
    from serial import SerialException
except Exception as exc:
    print(f"[ERROR] pySerial import failed: {exc}")
    print("Install: sudo apt-get install -y python3-serial")
    sys.exit(1)


DEFAULT_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
PORT = os.getenv("RELAY_PORT", DEFAULT_PORT)
BAUDRATE = 9600
TIMEOUT_S = 1.0
DEFAULT_WIRING = "nc"
DEFAULT_INIT_DELAY_S = 1.5
DEFAULT_COMMAND_RETRIES = 3
DEFAULT_RETRY_DELAY_S = 0.35
DEFAULT_POST_WRITE_DELAY_S = 0.1
DEFAULT_HOLD_S = 10.0

# Relay protocol (channel 1)
CMD_ON = bytes([0xA0, 0x01, 0x01, 0xA2])
CMD_OFF = bytes([0xA0, 0x01, 0x00, 0xA1])
CMD_STATUS = bytes([0xFF])


def open_serial(port: str) -> serial.Serial:
    ser = serial.Serial(
        port=port,
        baudrate=BAUDRATE,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=TIMEOUT_S,
    )
    try:
        ser.dtr = False
        ser.rts = False
    except Exception:
        pass
    return ser


def wait_for_relay_ready(ser: serial.Serial, init_delay_s: float) -> None:
    print(f"[INIT] Waiting {init_delay_s:.2f}s for relay controller to settle")
    time.sleep(init_delay_s)
    ser.reset_input_buffer()
    ser.reset_output_buffer()


def send_command(
    ser: serial.Serial,
    payload: bytes,
    label: str,
    retries: int,
    retry_delay_s: float,
    post_write_delay_s: float,
) -> None:
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            ser.reset_input_buffer()
            ser.write(payload)
            ser.flush()
            time.sleep(post_write_delay_s)
            print(f"[TX] {label} sent (attempt {attempt}/{retries})")
            return
        except SerialException as exc:
            last_error = exc
            print(f"[WARN] {label} send failed on attempt {attempt}/{retries}: {exc}")
            if attempt < retries:
                time.sleep(retry_delay_s)
    if last_error is not None:
        raise last_error


def relay_on(
    ser: serial.Serial,
    wiring: str,
    retries: int,
    retry_delay_s: float,
    post_write_delay_s: float,
) -> None:
    send_command(ser, CMD_ON, "relay ON", retries, retry_delay_s, post_write_delay_s)
    if wiring == "nc":
        print("[ACTION] Relay 1 ON command sent (NC wiring: DRIVER POWER OFF)")
    else:
        print("[ACTION] Relay 1 ON command sent (NO wiring: DRIVER POWER ON)")


def relay_off(
    ser: serial.Serial,
    wiring: str,
    retries: int,
    retry_delay_s: float,
    post_write_delay_s: float,
) -> None:
    send_command(ser, CMD_OFF, "relay OFF", retries, retry_delay_s, post_write_delay_s)
    if wiring == "nc":
        print("[ACTION] Relay 1 OFF command sent (NC wiring: DRIVER POWER ON)")
    else:
        print("[ACTION] Relay 1 OFF command sent (NO wiring: DRIVER POWER OFF)")


def read_status(
    ser: serial.Serial,
    retries: int,
    retry_delay_s: float,
    post_write_delay_s: float,
) -> str:
    ser.reset_input_buffer()
    send_command(ser, CMD_STATUS, "relay status query", retries, retry_delay_s, post_write_delay_s)
    print("[ACTION] Relay status query sent")
    time.sleep(0.2)

    raw = ser.read(ser.in_waiting or 1)
    if not raw:
        msg = "(no response)"
        print(f"[INFO] Status response: {msg}")
        return msg

    text = raw.decode("ascii", errors="replace").strip()
    if not text:
        text = raw.hex(" ")
        print(f"[INFO] Status response (hex): {text}")
    else:
        print(f"[INFO] Status response (ascii): {text}")
    return text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="USB relay serial test (Jetson Ubuntu 22.04)"
    )
    parser.add_argument(
        "--port",
        default=PORT,
        help=f"Serial port path (default: {PORT})",
    )
    parser.add_argument(
        "--mode",
        choices=["test", "on", "off", "status"],
        default="test",
        help="Operation mode (default: test)",
    )
    parser.add_argument(
        "--wiring",
        choices=["nc", "no"],
        default=DEFAULT_WIRING,
        help=f"Relay contact wiring type (default: {DEFAULT_WIRING})",
    )
    parser.add_argument(
        "--init-delay",
        type=float,
        default=DEFAULT_INIT_DELAY_S,
        help=f"Delay after opening the serial port before first command (default: {DEFAULT_INIT_DELAY_S}s)",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=DEFAULT_COMMAND_RETRIES,
        help=f"Command send retries for slow relay boards (default: {DEFAULT_COMMAND_RETRIES})",
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY_S,
        help=f"Delay between retries in seconds (default: {DEFAULT_RETRY_DELAY_S}s)",
    )
    parser.add_argument(
        "--post-write-delay",
        type=float,
        default=DEFAULT_POST_WRITE_DELAY_S,
        help=f"Short pause after each write in seconds (default: {DEFAULT_POST_WRITE_DELAY_S}s)",
    )
    parser.add_argument(
        "--hold",
        type=float,
        default=DEFAULT_HOLD_S,
        help=f"Test mode: seconds to keep relay ON before OFF (default: {DEFAULT_HOLD_S}s)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ser = None
    try:
        print(
            f"[INIT] Opening serial: {args.port} "
            f"({BAUDRATE} 8N1, timeout={TIMEOUT_S}s)"
        )
        print(f"[INIT] Wiring mode: {args.wiring.upper()}")
        ser = open_serial(args.port)
        print("[OK] Serial port opened")
        wait_for_relay_ready(ser, max(0.0, args.init_delay))

        if args.mode == "on":
            relay_on(ser, args.wiring, max(1, args.retries), max(0.0, args.retry_delay), max(0.0, args.post_write_delay))
        elif args.mode == "off":
            relay_off(ser, args.wiring, max(1, args.retries), max(0.0, args.retry_delay), max(0.0, args.post_write_delay))
        elif args.mode == "status":
            read_status(ser, max(1, args.retries), max(0.0, args.retry_delay), max(0.0, args.post_write_delay))
        else:
            print("[TEST] Note: ON/OFF power meaning follows selected wiring mode")
            relay_on(ser, args.wiring, max(1, args.retries), max(0.0, args.retry_delay), max(0.0, args.post_write_delay))
            hold_s = max(0.0, args.hold)
            print(f"[INFO] Waiting {hold_s:.1f} seconds")
            time.sleep(hold_s)
            relay_off(ser, args.wiring, max(1, args.retries), max(0.0, args.retry_delay), max(0.0, args.post_write_delay))
            time.sleep(0.2)
            read_status(ser, max(1, args.retries), max(0.0, args.retry_delay), max(0.0, args.post_write_delay))
            print("[TEST] Sequence completed")
        return 0
    except SerialException as exc:
        print(f"[ERROR] Serial communication error: {exc}")
        return 1
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        return 130
    finally:
        if ser and ser.is_open:
            ser.close()
            print("[CLEANUP] Serial port closed")


if __name__ == "__main__":
    raise SystemExit(main())
