"""카메라 멈춤 자동 복구.

프레임이 들어오지 않는 카메라가 있으면 칩 리셋(deser-control@<action>)을 자동으로 시작한다.
울산 Jetson #2 에서 멈춤은 스스로 풀리지 않았고(2~8시간 지속) 칩 리셋으로만 복구됐음.

- 판정: 내용이 바뀐 프레임이 stall_sec 넘게 없고, 그동안 들어온 같은 프레임도 초당
  MIN_DUP_FPS 미만일 때만 멈춤 → 불 꺼진 밤처럼 화면이 안 변해도 프레임이 계속 들어오면 멈춤 아님
- 시작 재시도에 실패한 카메라(스레드 종료)는 대상 아님 → 연결 안 된 카메라로 리셋이 반복되지 않게
- 리셋하면 이 웹도 재시작되므로 실행 기록은 HISTORY_FILE 에 남겨 시간당/일당 한도를 지킴
"""

import json
import threading
import time
from pathlib import Path

from . import camera_recovery

HISTORY_FILE = Path.home() / ".cache" / "jetson2_auto_recovery.json"
MIN_DUP_FPS = 5.0
CHECK_INTERVAL_SEC = 5.0
DAY_SEC = 86400


class AutoRecovery:
    def __init__(self, cameras: dict, config: dict, log_event=None):
        self.cameras = cameras
        self.config = config  # 켜기/끄기·기준·한도는 웹 설정 화면에서 바꾸면 바로 적용되도록 매번 읽음
        self.action = str(config.get("camera_auto_recovery_action", "reset-skip-relay"))
        self.grace_sec = float(config.get("camera_auto_recovery_grace_sec", 30))
        self.cooldown_sec = int(config.get("camera_recovery_cooldown_sec", 300))
        self.log_event = log_event
        self.started = time.time()
        self.message = "대기"
        self.limited = False
        self._retry_after = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = None

    @property
    def enabled(self) -> bool:
        return (bool(self.config.get("camera_auto_recovery_enabled", False))
                and self.action in camera_recovery.RESET_ACTIONS)

    @property
    def stall_sec(self) -> float:
        return float(self.config.get("camera_auto_recovery_stall_sec", 60))

    @property
    def max_per_hour(self) -> int:
        return int(self.config.get("camera_auto_recovery_max_per_hour", 3))

    @property
    def max_per_day(self) -> int:
        return int(self.config.get("camera_auto_recovery_max_per_day", 6))

    # ---- 실행 기록 (웹 재시작 후에도 유지) ----
    def _history(self, now: float) -> list:
        try:
            data = json.loads(HISTORY_FILE.read_text())
            items = [float(t) for t in data.get("triggers", [])]
        except Exception:
            items = []
        # 하루 넘은 기록과, 시계가 뒤로 가서 미래가 된 기록은 버림
        return [t for t in items if 0 <= now - t < DAY_SEC]

    def _save_history(self, items: list) -> None:
        try:
            HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp = HISTORY_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps({"triggers": items[-50:]}))
            tmp.replace(HISTORY_FILE)
        except Exception as exc:
            print(f"[AutoRecovery] 실행 기록 저장 실패: {exc}")

    # ---- 판정 ----
    def _stalled_cameras(self, now: float) -> list:
        base = self.started + self.grace_sec
        stalled = []
        for cam_id, cam in self.cameras.items():
            if cam is None:
                continue
            is_alive = getattr(cam, "is_alive", None)
            if callable(is_alive) and not is_alive():
                continue
            gst = getattr(cam, "camera", None)
            last_unique = float(getattr(gst, "last_unique_frame_ts", 0) or 0)
            dup_count = int(getattr(gst, "same_frame_count", 0) or 0)
            stale = now - max(last_unique, base)
            if stale < self.stall_sec:
                continue
            dup_window = max(1.0, now - (last_unique or self.started))
            if dup_count / dup_window >= MIN_DUP_FPS:
                continue  # 같은 화면이지만 프레임은 계속 들어옴 (정지 장면)
            stalled.append((cam_id, int(now - (last_unique or self.started))))
        return stalled

    def _limit_reason(self, now: float, history: list):
        hour = sum(1 for t in history if now - t < 3600)
        if hour >= self.max_per_hour:
            return f"1시간 {self.max_per_hour}회 한도 도달"
        if len(history) >= self.max_per_day:
            return f"24시간 {self.max_per_day}회 한도 도달"
        return None

    def check_once(self, now: float = None) -> None:
        now = time.time() if now is None else now
        if not self.enabled or now < self._retry_after:
            return
        stalled = self._stalled_cameras(now)
        if not stalled:
            with self._lock:
                self.limited = False
                self.message = "대기"
            return

        desc = ", ".join(f"CAM{cid} {sec}초" for cid, sec in stalled)
        history = self._history(now)
        reason = self._limit_reason(now, history)
        if reason:
            with self._lock:
                if not self.limited:
                    print(f"[AutoRecovery] 프레임 없음({desc}) — {reason}, 자동 리셋 안 함 (수동 점검 필요)")
                    self._log("WARNING", "Camera auto recovery limited", cameras=desc, reason=reason)
                self.limited = True
                self.message = f"{reason} — 수동 점검 필요"
            return

        result = camera_recovery.start_action(self.action, self.cooldown_sec)
        if result.get("ok"):
            history.append(now)
            self._save_history(history)
            print(f"[AutoRecovery] 프레임 없음({desc}) → {self.action} 자동 실행")
            self._log("WARNING", "Camera auto recovery started", cameras=desc, action=self.action)
            with self._lock:
                self.message = f"자동 리셋 실행 ({desc})"
            self._retry_after = now + 60  # 리셋이 이 웹을 중지할 때까지 중복 요청 방지
            return

        error = result.get("error")
        with self._lock:
            if error in ("busy", "cooldown"):
                self.message = f"리셋 대기 ({result.get('message', error)})"
                return
            # not_installed / sudo_failed 등: 같은 오류를 5초마다 반복하지 않게 10분 쉼
            self.message = f"자동 리셋 시작 실패: {result.get('message') or error}"
        print(f"[AutoRecovery] 프레임 없음({desc}) — 자동 리셋 시작 실패: {result}")
        self._log("ERROR", "Camera auto recovery start failed", cameras=desc, error=error)
        self._retry_after = now + 600

    def _log(self, level: str, message: str, **fields) -> None:
        if self.log_event is None:
            return
        try:
            self.log_event(level, message, **fields)
        except Exception:
            pass

    # ---- 스레드 ----
    def _run(self) -> None:
        while not self._stop.wait(CHECK_INTERVAL_SEC):
            try:
                self.check_once()
            except Exception as exc:
                print(f"[AutoRecovery] 점검 오류: {exc}")

    def start(self) -> None:
        # 꺼진 채 시작해도 스레드는 돌림 (설정 화면에서 켜면 바로 동작) — 판정은 check_once 에서 enabled 확인
        if self.action not in camera_recovery.RESET_ACTIONS or self._thread is not None:
            return
        if not self.enabled:
            print("[AutoRecovery] 꺼짐 (설정 화면에서 켤 수 있음)")
        else:
            print(f"[AutoRecovery] 켜짐: 프레임 {self.stall_sec:.0f}초 없으면 {self.action} "
                  f"(1시간 {self.max_per_hour}회, 24시간 {self.max_per_day}회 한도)")
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def status(self, now: float = None) -> dict:
        now = time.time() if now is None else now
        history = self._history(now) if self.enabled else []
        with self._lock:
            return {
                "enabled": self.enabled,
                "action": self.action,
                "stall_sec": self.stall_sec,
                "recent_hour": sum(1 for t in history if now - t < 3600),
                "max_per_hour": self.max_per_hour,
                "recent_day": len(history),
                "max_per_day": self.max_per_day,
                "last_trigger": history[-1] if history else 0,
                "limited": self.limited,
                "message": self.message,
            }
