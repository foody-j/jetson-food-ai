"""웹 설정 화면용 설정 읽기/저장.

- 기본 설정: config_jetson2_web.json (git 관리, 모든 장비 공통)
- 장비별 변경: config_jetson2_web.local.json (git 미관리) — 설정 화면에서 바꾼 값만 저장하고,
  시작할 때 기본 설정 위에 덮어 읽음 → git pull 과 충돌하지 않음
- 실행 중에 계속 읽는 항목(LIVE_KEYS)과 실행 중 전환 함수가 있는 항목(HOOK_KEYS)은 저장 즉시 적용,
  나머지는 재시작해야 적용
"""

import json
import shutil
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BASE_FILE = BASE_DIR / "config_jetson2_web.json"
LOCAL_FILE = BASE_DIR / "config_jetson2_web.local.json"

# 워커 루프/화면 갱신마다 config 를 다시 읽는 항목 → 저장 즉시 적용
LIVE_KEYS = {
    "device_label", "camera_stale_log_sec", "frying_log_interval_sec",
    "observe_img_size_seg", "observe_img_size_cls", "observe_conf_seg", "observe_inner_margin",
    "observe_bbox_pad", "observe_filled_prob_min", "observe_vote_min_samples",
    "observe_cam3_right_min_ratio", "observe_투입_temp_threshold",
    "img_size_seg", "img_size_cls", "conf_seg", "positive_label",
    "web_use_roi_cam2", "web_use_roi_cam3", "show_human_zone_overlay",
    "web_preview_fps", "web_preview_quality", "web_preview_width", "overlay_fps",
    "camera_auto_recovery_enabled", "camera_auto_recovery_stall_sec",
    "camera_auto_recovery_max_per_hour", "camera_auto_recovery_max_per_day",
}
# Jetson2Web.apply_live_setting() 으로 실행 중에 켜고 끄는 항목
HOOK_KEYS = {"frying_enabled", "observe_enabled", "human_safety_enabled", "overlay_enabled"}

# 설정 화면 상단 스위치 (key, 이름, 설명)
SWITCHES = [
    ("frying_enabled", "튀김 AI", "튀김 상태 분석. 끄면 바로 멈추고, 켜면 다음 조리부터 동작"),
    ("frying_left_enabled", "튀김 AI 왼쪽", "왼쪽 튀김 카메라/AI 사용"),
    ("frying_right_enabled", "튀김 AI 오른쪽", "오른쪽 튀김 카메라/AI 사용"),
    ("observe_enabled", "바켓 감지 AI", "바켓 채움/투입 판정"),
    ("observe_left_enabled", "바켓 감지 왼쪽", "왼쪽 바켓 카메라/AI 사용"),
    ("observe_right_enabled", "바켓 감지 오른쪽", "오른쪽 바켓 카메라/AI 사용"),
    ("human_safety_enabled", "사람 안전 감지", "바켓 주변에 사람이 있으면 투입 차단"),
    ("overlay_enabled", "AI 결과 화면 표시", "대시보드 영상에 AI 판정 그리기"),
    ("camera_auto_recovery_enabled", "카메라 자동 복구", "프레임이 끊기면 칩 리셋 자동 실행"),
    ("mqtt_enabled", "MQTT 통신", "로봇/서버와 통신"),
]

# 주요 설정 (key, 이름, 설명, 최소, 최대, 단계)
IMPORTANT = [
    ("device_label", "장비 이름표", "헤더 제목 옆에 작게 표시 (예: 울산 #2). 비우면 숨김 — 화면 새로고침 시 반영", None, None, None),
    ("observe_conf_seg", "바켓 감지 신뢰도 기준", "낮추면 더 잘 잡지만 오탐 증가", 0.05, 0.95, 0.05),
    ("observe_filled_prob_min", "바켓 '채워짐' 판정 확률", "이 확률 이상이어야 채워짐으로 판정", 0.5, 1.0, 0.01),
    ("observe_vote_min_samples", "바켓 판정 최소 표본 수", "판정 전에 모을 프레임 수", 1, 20, 1),
    ("observe_투입_temp_threshold", "투입 판정 기름 온도 (℃)", "이 온도 이상이면 투입으로 판정", 100, 220, 1),
    ("observe_infer_fps", "바켓 AI 추론 속도 (초당)", "높일수록 GPU 사용 증가", 0.2, 10, 0.1),
    ("frying_seg_conf", "튀김 세그멘테이션 신뢰도", "튀김 영역 검출 기준", 0.01, 0.9, 0.01),
    ("frying_infer_fps", "튀김 AI 추론 속도 (초당)", "높일수록 GPU 사용 증가", 0.2, 10, 0.1),
    ("target_probe_temp", "목표 심부 온도 (℃)", "튀김 완료 기준 온도", 40, 120, 0.5),
    ("human_conf_min", "사람 감지 신뢰도 기준", "낮추면 더 민감하게 차단", 0.1, 0.95, 0.05),
    ("human_fail_safe_block", "사람 감지 실패 시 차단", "모델 오류 때 안전하게 차단", None, None, None),
    ("camera_auto_recovery_stall_sec", "자동 복구: 프레임 없음 기준 (초)", "이 시간 넘게 프레임이 없으면 칩 리셋", 20, 600, 5),
    ("camera_auto_recovery_max_per_hour", "자동 복구: 1시간 최대 횟수", "넘으면 자동 실행 멈추고 경고", 1, 10, 1),
    ("web_preview_fps", "대시보드 영상 갱신 (초당)", "높이면 화면이 부드럽지만 부하 증가", 0.5, 15, 0.5),
    ("web_preview_quality", "대시보드 영상 화질 (JPEG)", "10~95", 10, 95, 5),
    ("data_collection_interval_normal", "데이터 수집 간격 (초)", "조리 중 이미지 저장 간격", 0.2, 10, 0.1),
    ("mqtt_broker", "MQTT 브로커 주소", "로봇/서버 MQTT 주소", None, None, None),
    ("debug_print_enabled", "디버그 로그 출력", "로그가 많아짐", None, None, None),
]

_lock = threading.Lock()
_pending_restart = {}  # 이 프로세스가 시작된 뒤 저장됐지만 재시작해야 적용되는 항목 {key: 새 값}
_startup_values = {}   # 이 프로세스가 시작할 때 읽은 값 (원래 값으로 되돌리면 재시작 대기에서 뺌)


def remember_startup(config: dict) -> None:
    _startup_values.clear()
    _startup_values.update(json.loads(json.dumps(config)))


def _read(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return data if isinstance(data, dict) else {}


def _read_local(path: Path = None) -> dict:
    """장비별 설정. 깨져 있으면 무시 (다음 저장 때 .bak 으로 남기고 새로 씀)."""
    try:
        return _read(path or LOCAL_FILE)
    except Exception as exc:
        print(f"[Settings] 장비별 설정 파일 읽기 실패 — 무시: {exc}")
        return {}


def load_merged(base_path: Path = None, local_path: Path = None) -> dict:
    """기본 설정 + 장비별 변경. 장비별 파일이 깨져 있으면 무시하고 기본 설정으로 시작."""
    base = _read(base_path or BASE_FILE)
    local = _read_local(local_path)
    for key, value in local.items():
        if key in base and not key.startswith("//"):
            base[key] = value
    return base


def apply_mode(key: str) -> str:
    return "live" if key in LIVE_KEYS or key in HOOK_KEYS else "restart"


def _value_type(value) -> str:
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "str"
    return "json"


def _item(key, config, base, local, label=None, help_text="", vmin=None, vmax=None, step=None):
    return {
        "key": key,
        "label": label or key,
        "help": help_text,
        "type": _value_type(base[key]),
        "value": config.get(key, base[key]),
        "default": base[key],
        "overridden": key in local,
        "apply": apply_mode(key),
        "min": vmin, "max": vmax, "step": step,
    }


def get_settings(config: dict) -> dict:
    base = _read(BASE_FILE)
    local = _read_local()
    shown = set()
    switches = []
    for key, label, help_text in SWITCHES:
        if key in base:
            switches.append(_item(key, config, base, local, label, help_text))
            shown.add(key)
    important = []
    for key, label, help_text, vmin, vmax, step in IMPORTANT:
        if key in base:
            important.append(_item(key, config, base, local, label, help_text, vmin, vmax, step))
            shown.add(key)
    # 나머지는 설정 파일의 "// 섹션" 주석 기준으로 묶어서 원래 이름 그대로
    groups, current = [], {"title": "기타", "items": []}
    for key in base:
        if key.startswith("//"):
            if base[key] == "" and ":" not in key:  # 섹션 제목 ("// 카메라": ""), "// NOTE: …" 같은 설명은 제외
                if current["items"]:
                    groups.append(current)
                current = {"title": key[2:].strip(), "items": []}
            continue
        if key not in shown:
            current["items"].append(_item(key, config, base, local))
    if current["items"]:
        groups.append(current)
    return {"switches": switches, "important": important, "groups": groups,
            "pending_restart": sorted(_pending_restart)}


def _coerce(key: str, value, base_value, limits):
    """설정 화면에서 온 값을 기본 설정과 같은 타입으로 검사/변환. 잘못되면 ValueError."""
    vtype = _value_type(base_value)
    if vtype == "bool":
        if not isinstance(value, bool):
            raise ValueError("켜기/끄기 값이어야 함")
        return value
    if vtype in ("int", "float"):
        if isinstance(value, bool):
            raise ValueError("숫자여야 함")
        try:
            num = float(value)
        except (TypeError, ValueError):
            raise ValueError("숫자여야 함")
        if num != num or num in (float("inf"), float("-inf")):
            raise ValueError("숫자여야 함")
        vmin, vmax = limits
        if vmin is not None and num < vmin:
            raise ValueError(f"{vmin} 이상이어야 함")
        if vmax is not None and num > vmax:
            raise ValueError(f"{vmax} 이하여야 함")
        if vtype == "int":
            if num != int(num):
                raise ValueError("정수여야 함")
            return int(num)
        return num
    if vtype == "str":
        if not isinstance(value, str):
            raise ValueError("문자열이어야 함")
        return value.strip()
    # 리스트/객체: 같은 종류여야 함
    if type(value) is not type(base_value):
        raise ValueError("목록/객체 형식이 기본값과 다름")
    return value


def save_changes(config: dict, changes: dict, apply_hook=None) -> dict:
    """변경값 검사 → 장비별 파일 저장 → 실행 중 config 갱신 → 즉시 적용 가능한 항목 반영."""
    if not isinstance(changes, dict) or not changes:
        return {"ok": False, "errors": {"_": "변경 내용 없음"}}
    limits = {k: (vmin, vmax) for k, _, _, vmin, vmax, _ in IMPORTANT}
    with _lock:
        base = _read(BASE_FILE)
        local = _read_local()
        errors, coerced = {}, {}
        for key, value in changes.items():
            if key.startswith("//") or key not in base:
                errors[key] = "알 수 없는 설정"
                continue
            try:
                coerced[key] = _coerce(key, value, base[key], limits.get(key, (None, None)))
            except ValueError as exc:
                errors[key] = str(exc)
        if errors:
            return {"ok": False, "errors": errors}

        new_local = dict(local)
        for key, value in coerced.items():
            if value == base[key]:
                new_local.pop(key, None)  # 기본값으로 돌아가면 장비별 기록 삭제
            else:
                new_local[key] = value
        if LOCAL_FILE.exists():
            shutil.copy2(LOCAL_FILE, LOCAL_FILE.with_suffix(".json.bak"))
        tmp = LOCAL_FILE.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(new_local, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(LOCAL_FILE)

        results = []
        for key, value in coerced.items():
            old = config.get(key, base[key])
            config[key] = value  # 워커들이 같은 dict 를 보므로 LIVE_KEYS 는 바로 반영됨
            mode = apply_mode(key)
            if key in HOOK_KEYS and old != value:
                applied = False
                if apply_hook is not None:
                    try:
                        applied = bool(apply_hook(key, value))
                    except Exception as exc:
                        print(f"[Settings] {key} 실행 중 적용 실패: {exc}")
                if not applied:
                    mode = "restart"
            if mode == "restart" and value != _startup_values.get(key, old):
                _pending_restart[key] = value
            else:
                _pending_restart.pop(key, None)
            results.append({"key": key, "old": old, "new": value, "apply": mode})
    for r in results:
        print(f"[Settings] {r['key']}: {r['old']!r} → {r['new']!r} ({'즉시 적용' if r['apply'] == 'live' else '재시작 후 적용'})")
    return {"ok": True, "results": results, "pending_restart": sorted(_pending_restart)}
