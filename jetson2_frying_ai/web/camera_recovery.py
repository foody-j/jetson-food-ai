"""카메라 복구(디시리얼라이저 칩 리셋 / USB 릴레이 상태) 제어.

실제 작업은 root 로 도는 deser-control@<action>.service 가 수행한다
(install_deser_control.sh 로 설치). 웹은 sudoers 에 허용된
`systemctl start --no-block` 만 호출하고, 결과는 /run/deser-control/ 파일로 읽는다.
리셋 중에는 이 웹 서비스도 중지됐다가 다시 시작된다.
"""

import json
import subprocess
import time
from pathlib import Path
from typing import Optional

STATE_DIR = Path("/run/deser-control")
STATE_FILE = STATE_DIR / "state.json"
UNIT_TEMPLATE = "deser-control@{}.service"
ACTIONS = ("reset", "reset-skip-relay", "relay-status")
RESET_ACTIONS = ("reset", "reset-skip-relay")
LOG_TAIL_LINES = 60


def _systemctl() -> str:
    # install_deser_control.sh 의 sudoers 와 같은 절대경로여야 sudo -n 이 허용됨
    return "/usr/bin/systemctl"


def is_installed() -> bool:
    return Path("/etc/systemd/system/deser-control@.service").exists()


def _running_action() -> Optional[str]:
    """실행 중인(activating) 복구 작업 이름. 없으면 None."""
    for action in ACTIONS:
        try:
            res = subprocess.run(
                [_systemctl(), "is-active", UNIT_TEMPLATE.format(action)],
                capture_output=True, text=True, timeout=3,
            )
        except Exception:
            continue
        if res.stdout.strip() in ("activating", "active", "reloading"):
            return action
    return None


def _read_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def _read_log_tail(action: str) -> str:
    try:
        lines = (STATE_DIR / f"{action}.log").read_text(errors="replace").splitlines()
    except Exception:
        return ""
    return "\n".join(lines[-LOG_TAIL_LINES:])


def get_status(cooldown_sec: int) -> dict:
    state = _read_state()
    running = _running_action()
    last_action = state.get("action")
    now = time.time()

    cooldown_left = 0
    if state.get("action") in RESET_ACTIONS and state.get("finished"):
        cooldown_left = max(0, int(cooldown_sec - (now - float(state["finished"]))))

    return {
        "installed": is_installed(),
        "running": running,
        "last": state,
        "log": _read_log_tail(running or last_action) if (running or last_action) else "",
        "cooldown_left": cooldown_left,
        "timestamp": now,
    }


def start_action(action: str, cooldown_sec: int) -> dict:
    if action not in ACTIONS:
        return {"ok": False, "error": "invalid_action"}
    if not is_installed():
        return {"ok": False, "error": "not_installed",
                "message": "install_deser_control.sh 를 먼저 실행하세요"}

    running = _running_action()
    if running:
        return {"ok": False, "error": "busy", "message": f"{running} 실행 중"}

    if action in RESET_ACTIONS:
        cooldown_left = get_status(cooldown_sec)["cooldown_left"]
        if cooldown_left > 0:
            return {"ok": False, "error": "cooldown",
                    "message": f"직전 리셋 후 {cooldown_left}초 뒤에 다시 시도하세요"}

    cmd = ["sudo", "-n", _systemctl(), "start", "--no-block", UNIT_TEMPLATE.format(action)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception as exc:
        return {"ok": False, "error": "exec_failed", "message": str(exc)}
    if res.returncode != 0:
        return {"ok": False, "error": "sudo_failed",
                "message": (res.stderr or res.stdout).strip()[:300]}
    return {"ok": True, "action": action}
