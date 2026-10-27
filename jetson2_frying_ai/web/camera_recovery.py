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
LAST_RESET_FILE = STATE_DIR / "last_reset.json"  # 마지막으로 성공한 리셋 (쿨다운 기준)
UNIT_TEMPLATE = "deser-control@{}.service"
ACTIONS = ("reset", "reset-skip-relay", "relay-status")
RESET_ACTIONS = ("reset", "reset-skip-relay")
# deactivating: 중단 신호를 받은 리셋 스크립트가 원상복구 중인 상태
RUNNING_STATES = ("activating", "active", "reloading", "deactivating")
LOG_TAIL_LINES = 60


def _systemctl() -> str:
    # install_deser_control.sh 의 sudoers 와 같은 절대경로여야 sudo -n 이 허용됨
    return "/usr/bin/systemctl"


def is_installed() -> bool:
    return Path("/etc/systemd/system/deser-control@.service").exists()


def _running_action() -> Optional[str]:
    """실행 중인 복구 작업 이름. 없으면 None."""
    for action in ACTIONS:
        try:
            res = subprocess.run(
                [_systemctl(), "is-active", UNIT_TEMPLATE.format(action)],
                capture_output=True, text=True, timeout=3,
            )
        except Exception:
            continue
        if res.stdout.strip() in RUNNING_STATES:
            return action
    return None


def _read_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text())
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _read_log_tail(action: str) -> str:
    try:
        lines = (STATE_DIR / f"{action}.log").read_text(errors="replace").splitlines()
    except Exception:
        return ""
    return "\n".join(lines[-LOG_TAIL_LINES:])


def _cooldown_left(cooldown_sec: int, now: float) -> int:
    """마지막 성공 리셋 후 남은 쿨다운(초). 중단/실패한 리셋과 relay-status 는 영향 없음."""
    try:
        finished = float(_read_json(LAST_RESET_FILE)["finished"])
    except Exception:
        return 0
    elapsed = now - finished
    if elapsed < -5:
        # 기록 시각이 미래 = 시계가 뒤로 감(NTP/수동 보정) → 실제 경과를 알 수 없으므로 쿨다운 해제
        return 0
    return min(cooldown_sec, max(0, int(cooldown_sec - elapsed)))


def get_status(cooldown_sec: int) -> dict:
    # systemd 를 먼저 확인한 뒤 상태 파일을 읽어야, '실행 중 아님'일 때 읽은 상태가 최종 결과임
    running = _running_action()
    state = _read_json(STATE_FILE)
    now = time.time()
    log_action = running or state.get("action")

    return {
        "installed": is_installed(),
        "running": running,
        "last": state,
        "log": _read_log_tail(log_action) if log_action in ACTIONS else "",
        "cooldown_left": _cooldown_left(cooldown_sec, now),
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
        cooldown_left = _cooldown_left(cooldown_sec, time.time())
        if cooldown_left > 0:
            return {"ok": False, "error": "cooldown",
                    "message": f"직전 리셋 후 {cooldown_left}초 뒤에 다시 시도하세요"}

    # 대시보드가 이 시각 이후에 시작된 실행 결과만 이번 요청의 결과로 인정 (시작 실패 감지용)
    requested_at = time.time()
    cmd = ["sudo", "-n", _systemctl(), "start", "--no-block", UNIT_TEMPLATE.format(action)]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except Exception as exc:
        return {"ok": False, "error": "exec_failed", "message": str(exc)}
    if res.returncode != 0:
        return {"ok": False, "error": "sudo_failed",
                "message": (res.stderr or res.stdout).strip()[:300]}
    return {"ok": True, "action": action, "requested_at": requested_at}
