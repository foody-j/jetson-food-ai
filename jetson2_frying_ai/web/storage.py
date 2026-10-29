"""대시보드 '데이터 저장 위치' 패널용 경로 목록.

경로는 Jetson2Web 이 실제로 쓰는 값(state 의 *_dir 속성)을 읽고, 없으면 같은 규칙으로 계산.
폴더 크기는 계산하지 않음 (AI_Data 사진이 많아 느림) → 존재 여부와 오늘 파일·진행 중 세션만 표시.
"""

import os
from datetime import datetime
from pathlib import Path

from . import camera_recovery, settings
from .auto_recovery import HISTORY_FILE

SCRIPT_DIR = Path(__file__).resolve().parent.parent


def _entry(group: str, label: str, path, desc: str, current=None, kind: str = "today") -> dict:
    path = str(path)
    current = str(current) if current else None
    return {
        "group": group,
        "label": label,
        "path": path,
        "desc": desc,
        "current": current,  # 오늘 파일 또는 지금 기록 중인 세션 폴더
        "current_kind": kind if current else None,  # today | session
        "exists": os.path.exists(current or path),
    }


def storage_paths(state=None) -> list:
    home = Path.home()
    ai_data = home / "AI_Data"
    today = datetime.now().strftime("%Y-%m-%d")

    def log_dir(attr: str, name: str) -> Path:
        value = getattr(state, attr, None) if state is not None else None
        return Path(value) if value else SCRIPT_DIR / name

    def session_dir(prefix: str):
        if state is None or not getattr(state, f"{prefix}_collecting", False):
            return None
        return getattr(state, f"{prefix}_session_dir", None)

    legacy = None
    if state is not None and getattr(state, "data_collection_active", False):
        legacy = getattr(state, "frying_session_dir", None)

    ops = log_dir("ops_log_dir", "ops_logs")
    fry = log_dir("frying_event_log_dir", "frying_event_logs")
    app = log_dir("app_log_dir", "app_logs")
    mqtt = log_dir("mqtt_log_dir", "mqtt_logs")
    relay = log_dir("relay_log_dir", "relay_logs")

    return [
        _entry("조리 데이터", "POT1 (왼쪽)", ai_data / "pot1",
               "세션/음식/ 아래 camera_0(튀김)·camera_2(바켓) 사진, meta/(사진별 AI 값), "
               "session_info.json, *_lift_events.json(탈탈·완료)", session_dir("pot1"), "session"),
        _entry("조리 데이터", "POT2 (오른쪽)", ai_data / "pot2",
               "세션/음식/ 아래 camera_1(튀김)·camera_3(바켓) 사진, meta/, session_info.json, "
               "*_lift_events.json", session_dir("pot2"), "session"),
        _entry("조리 데이터", "전체 수집 (ALL START)", ai_data,
               "FryingData/세션(튀김 카메라), BucketData/세션(바켓 카메라)", legacy, "session"),
        _entry("AI·운영 로그", "AI·운영 이벤트", ops,
               "탈탈·완료 감지, 바켓·사람 판정 변화, 투입 차단, 설정 변경, 릴레이 (날짜별 .jsonl)",
               ops / f"ops_{today}.jsonl"),
        _entry("AI·운영 로그", "투입·배출 기록", fry,
               "투입·배출 시 온도·레시피·바켓·사람 상태 (날짜별 .jsonl)",
               fry / f"frying_events_{today}.jsonl"),
        _entry("AI·운영 로그", "실행 로그", app,
               "프로그램 출력 전체: 튀김 AI 수치(10초마다), 카메라 멈춤, 자동 복구 (날짜별 .jsonl)",
               app / f"app_{today}.jsonl"),
        _entry("AI·운영 로그", "MQTT 메시지", mqtt, "받은 MQTT 원문 (날짜별 .log)",
               mqtt / f"mqtt_{today}.log"),
        _entry("AI·운영 로그", "릴레이", relay, "릴레이 ON/OFF (날짜별 .log)",
               relay / f"relay_{today}.log"),
        _entry("AI·운영 로그", "진동 이벤트", home / "data" / "vibration_events" / "jetson2",
               "진동 점검 때 저장된 측정 데이터"),
        _entry("시스템", "칩 리셋 로그", camera_recovery.STATE_DIR,
               "리셋 종류별 .log, 마지막 1회분만 남고 재부팅하면 지워짐"),
        _entry("시스템", "자동 복구 기록", HISTORY_FILE, "자동 리셋 실행 시각 (시간당·일당 한도 계산용)"),
        _entry("시스템", "이 장비 설정", settings.LOCAL_FILE,
               "설정 화면에서 바꾼 값 (기본값은 config_jetson2_web.json)"),
    ]
