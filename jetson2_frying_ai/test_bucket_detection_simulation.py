#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bucket detection simulation (segmentation + classification) on saved images.
- Supports both direct and nested session folders.
- Uses web-like observe pipeline (ROI + in-class bbox + inner crop + square cls crop).
"""

import os
import json
import glob
import argparse
from collections import deque
from datetime import datetime

import cv2
import numpy as np
from ultralytics import YOLO

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def load_config(config_path: str):
    config_full = config_path
    if not os.path.isabs(config_full):
        config_full = os.path.join(SCRIPT_DIR, config_path)
    with open(config_full, "r", encoding="utf-8") as f:
        return json.load(f)


def resolve_model_path(path_str: str) -> str:
    if not path_str:
        return ""
    if os.path.isabs(path_str):
        return path_str
    return os.path.join(SCRIPT_DIR, path_str)


def list_images(folder: str):
    exts = {".jpg", ".jpeg", ".png", ".bmp"}
    files = []
    for p in sorted(glob.glob(os.path.join(folder, "*"))):
        if os.path.splitext(p)[1].lower() in exts:
            files.append(p)
    return files


def resolve_camera_dir(session_dir: str, camera_idx: int):
    """
    Resolve camera folder from either:
    1) <session_dir>/camera_2 (old style)
    2) <session_dir>/<food_type>/camera_2 (pot1/pot2 style)
    Returns: (resolved_session_dir, camera_dir)
    """
    direct = os.path.join(session_dir, f"camera_{camera_idx}")
    if os.path.isdir(direct):
        return session_dir, direct

    matches = []
    for name in sorted(os.listdir(session_dir)):
        child = os.path.join(session_dir, name)
        if not os.path.isdir(child):
            continue
        cam_dir = os.path.join(child, f"camera_{camera_idx}")
        if os.path.isdir(cam_dir):
            matches.append((child, cam_dir))

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        # Pick the newest sub-session if multiple matches are present.
        matches.sort(key=lambda x: os.path.getmtime(x[0]), reverse=True)
        picked = matches[0]
        print(f"⚠ camera_{camera_idx} 경로가 여러 개여서 최신 폴더 선택: {picked[0]}")
        return picked

    return None, None


def _clamp_int(value: float, lo: int, hi: int) -> int:
    return max(lo, min(int(value), hi))


def _square_crop(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    side = min(h, w)
    x1 = (w - side) // 2
    y1 = (h - side) // 2
    return img[y1:y1 + side, x1:x1 + side].copy()


def _apply_roi(frame: np.ndarray, roi) -> np.ndarray:
    if frame is None or roi is None:
        return frame
    try:
        x, y, w, h = roi
    except Exception:
        return frame
    if w <= 1 or h <= 1:
        return frame
    fh, fw = frame.shape[:2]
    x1 = max(0, min(int(x), fw - 1))
    y1 = max(0, min(int(y), fh - 1))
    x2 = max(0, min(int(x + w), fw))
    y2 = max(0, min(int(y + h), fh))
    if x2 <= x1 or y2 <= y1:
        return frame
    return frame[y1:y2, x1:x2].copy()


def log_signal(side: str, state: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] 바켓 {side} -> {state}")


def is_in_class_name(name: str, target_name: str = "in") -> bool:
    """
    Match Observe web logic:
    - exact 'in'
    - contains 'in' (for label variants)
    """
    name_lower = (name or "").lower()
    target_lower = (target_name or "in").lower()
    if not name_lower:
        return False
    if name_lower == target_lower:
        return True
    return target_lower in name_lower


def get_model_paths(config, side: str):
    base_seg = config.get("observe_seg_model", "")
    base_cls = config.get("observe_cls_model", "")
    left_seg = config.get("observe_left_seg_model") or base_seg
    right_seg = config.get("observe_right_seg_model") or base_seg or left_seg
    left_cls = config.get("observe_left_cls_model") or base_cls
    right_cls = config.get("observe_right_cls_model") or base_cls or left_cls

    if side == "right":
        return resolve_model_path(right_seg), resolve_model_path(right_cls)
    return resolve_model_path(left_seg), resolve_model_path(left_cls)


def simulate_session(session_dir: str, camera_idx: int, side: str, args):
    print("=" * 80)
    print(f"🔍 바켓 감지 시뮬레이션 시작: {os.path.basename(session_dir)}")
    print("=" * 80)

    resolved_session_dir, camera_dir = resolve_camera_dir(session_dir, camera_idx)
    if not camera_dir:
        print(f"❌ camera_{camera_idx} 디렉토리를 찾지 못함: {session_dir}")
        return

    image_files = list_images(camera_dir)
    if not image_files:
        print(f"❌ 이미지 파일 없음: {camera_dir}")
        return
    if args.max_images and args.max_images > 0:
        image_files = image_files[:args.max_images]

    if resolved_session_dir != session_dir:
        print(f"📁 세션 하위 폴더 자동 선택: {resolved_session_dir}")
    print(f"📁 카메라 디렉토리: {camera_dir}")
    print(f"📸 총 이미지 수: {len(image_files)}")

    config = load_config(args.config)
    img_size_seg = config.get("observe_img_size_seg", config.get("img_size_seg", 640))
    img_size_cls = config.get("observe_img_size_cls", config.get("img_size_cls", 224))
    conf_seg = config.get("observe_conf_seg", config.get("conf_seg", 0.5))
    vote_n = config.get("vote_n", 7)
    positive_label = config.get("positive_label", "filled")
    target_seg_class = config.get("observe_target_seg_class", "in")
    inner_margin = float(config.get("observe_inner_margin", 0.15))
    bbox_pad = int(config.get("observe_bbox_pad", 10))
    roi = config.get("observe_roi_cam2") if side == "left" else config.get("observe_roi_cam3")

    seg_path, cls_path = get_model_paths(config, side)
    if not seg_path or not os.path.exists(seg_path):
        raise SystemExit(f"Seg model not found: {seg_path}")
    if not cls_path or not os.path.exists(cls_path):
        raise SystemExit(f"Cls model not found: {cls_path}")

    print(f"🔧 Seg model: {seg_path}")
    print(f"🔧 Cls model: {cls_path}")

    seg_model = YOLO(seg_path)
    cls_model = YOLO(cls_path)

    votes = deque(maxlen=vote_n)
    last_state = None
    detected_count = 0
    filled_count = 0
    class_names_logged = False

    if args.display:
        cv2.namedWindow("Bucket Simulation", cv2.WINDOW_NORMAL)
    paused = False

    for i, img_path in enumerate(image_files, 1):
        image = cv2.imread(img_path)
        if image is None:
            print(f"⚠ 이미지 로드 실패: {img_path}")
            continue
        image = _apply_roi(image, roi)
        vis = image.copy()
        H, W = image.shape[:2]

        r = seg_model.predict(image, imgsz=img_size_seg, conf=conf_seg, verbose=False, device=args.device)[0]
        if not class_names_logged:
            try:
                print(f"🧾 Seg classes: {r.names}")
            except Exception:
                pass
            class_names_logged = True

        detected = False
        is_filled_frame = False
        top1_name = None
        prob = 0.0

        if r.boxes is not None and len(r.boxes) > 0:
            boxes_xyxy = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            cls_ids = r.boxes.cls.cpu().numpy().astype(int)
            names = r.names

            in_indices = [j for j in range(len(cls_ids)) if is_in_class_name(names[int(cls_ids[j])], target_name=target_seg_class)]
            if in_indices:
                best_in = max(in_indices, key=lambda j: confs[j])
                x1, y1, x2, y2 = boxes_xyxy[best_in]
                x1 = _clamp_int(x1 - bbox_pad, 0, W - 1)
                y1 = _clamp_int(y1 - bbox_pad, 0, H - 1)
                x2 = _clamp_int(x2 + bbox_pad, 0, W - 1)
                y2 = _clamp_int(y2 + bbox_pad, 0, H - 1)
                if x2 > x1 and y2 > y1:
                    bw = x2 - x1
                    bh = y2 - y1
                    mx = int(bw * inner_margin)
                    my = int(bh * inner_margin)
                    ix1 = _clamp_int(x1 + mx, 0, W - 1)
                    iy1 = _clamp_int(y1 + my, 0, H - 1)
                    ix2 = _clamp_int(x2 - mx, 0, W - 1)
                    iy2 = _clamp_int(y2 - my, 0, H - 1)
                    if ix2 > ix1 and iy2 > iy1:
                        detected = True
                        detected_count += 1
                        inner = image[iy1:iy2, ix1:ix2].copy()
                        inner_sq = _square_crop(inner)
                        inner_sq = cv2.resize(inner_sq, (img_size_cls, img_size_cls), interpolation=cv2.INTER_AREA)
                        cls_res = cls_model.predict(inner_sq, imgsz=img_size_cls, conf=0.0, verbose=False, device=args.device)[0]
                        top1_idx = int(cls_res.probs.top1)
                        top1_name = cls_res.names[top1_idx]
                        prob = float(cls_res.probs.top1conf)
                        is_filled_frame = (top1_name.lower() == positive_label.lower())
                        cv2.rectangle(vis, (x1, y1), (x2, y2), (255, 128, 0), 2)
                        cv2.rectangle(vis, (ix1, iy1), (ix2, iy2), (0, 255, 255), 2)
                        cv2.putText(vis, f"{top1_name} ({prob:.2f})", (x1, max(20, y1 - 10)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        if detected:
            votes.append(is_filled_frame)
            filled_stable = (sum(votes) >= (len(votes) // 2 + 1))
            state_txt = "FILLED" if filled_stable else "EMPTY"
            color = (0, 0, 255) if filled_stable else (200, 200, 200)
            if filled_stable:
                filled_count += 1

            cv2.putText(vis, f"STATUS: {state_txt}", (16, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

            if state_txt != last_state:
                log_signal("오른쪽" if side == "right" else "왼쪽", state_txt)
                last_state = state_txt

            print(f"[{i:4d}/{len(image_files)}] ✅ DETECT | cls={top1_name} ({prob:.2f})")
        else:
            votes.clear()
            cv2.putText(vis, "Basket Not Found", (16, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            if last_state is not None:
                log_signal("오른쪽" if side == "right" else "왼쪽", "NO_BASKET")
                last_state = None
            print(f"[{i:4d}/{len(image_files)}] ❌ NO_BASKET")

        if args.save_vis:
            os.makedirs(args.save_vis, exist_ok=True)
            out_name = os.path.basename(img_path)
            out_path = os.path.join(args.save_vis, out_name)
            cv2.imwrite(out_path, vis)

        if args.display:
            cv2.imshow("Bucket Simulation", vis)
            delay_ms = 1
            if args.display_fps > 0:
                delay_ms = max(1, int(1000 / args.display_fps))
            key = cv2.waitKey(0 if paused else delay_ms) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord(" "):
                paused = not paused
            if paused and key == ord("n"):
                paused = True

    if args.display:
        cv2.destroyAllWindows()

    print("\n" + "=" * 80)
    print("📊 시뮬레이션 결과")
    print("=" * 80)
    print(f"총 이미지 수: {len(image_files)}")
    print(f"바켓 감지 프레임: {detected_count}")
    print(f"FILLED 프레임(다수결): {filled_count}")
    return {
        "session_dir": session_dir,
        "side": side,
        "camera_idx": camera_idx,
        "total_images": len(image_files),
        "detected_count": detected_count,
        "filled_count": filled_count,
    }


def get_sessions(base_dir: str):
    base_dir = os.path.expanduser(base_dir)
    if not os.path.exists(base_dir):
        return []
    return [s for s in sorted(glob.glob(os.path.join(base_dir, "session_*"))) if os.path.isdir(s)]


def list_recent_sessions(base_dir: str, limit: int = 8):
    base_dir = os.path.expanduser(base_dir)
    if not os.path.exists(base_dir):
        print(f"❌ base_dir 없음: {base_dir}")
        return
    candidates = get_sessions(base_dir)
    sessions = []
    for s in candidates:
        cam2 = os.path.join(s, "camera_2")
        cam3 = os.path.join(s, "camera_3")
        has_direct = os.path.isdir(cam2) or os.path.isdir(cam3)
        has_nested = False
        if not has_direct:
            for child_name in os.listdir(s):
                child = os.path.join(s, child_name)
                if not os.path.isdir(child):
                    continue
                if os.path.isdir(os.path.join(child, "camera_2")) or os.path.isdir(os.path.join(child, "camera_3")):
                    has_nested = True
                    break
        if has_direct or has_nested:
            sessions.append(s)
    if not sessions:
        print(f"❌ 세션 없음: {base_dir}")
        return
    print("사용 가능한 세션 (최근 기준):")
    for s in sessions[-limit:]:
        name = os.path.basename(s)
        c2 = 0
        c3 = 0
        if os.path.isdir(os.path.join(s, "camera_2")):
            c2 = len(list_images(os.path.join(s, "camera_2")))
        if os.path.isdir(os.path.join(s, "camera_3")):
            c3 = len(list_images(os.path.join(s, "camera_3")))
        if c2 == 0 and c3 == 0:
            for child_name in os.listdir(s):
                child = os.path.join(s, child_name)
                if not os.path.isdir(child):
                    continue
                if os.path.isdir(os.path.join(child, "camera_2")):
                    c2 += len(list_images(os.path.join(child, "camera_2")))
                if os.path.isdir(os.path.join(child, "camera_3")):
                    c3 += len(list_images(os.path.join(child, "camera_3")))
        print(f"  - {name} (cam2: {c2}장, cam3: {c3}장)")


def main():
    parser = argparse.ArgumentParser(description="Bucket detection simulation")
    parser.add_argument("session_dir", nargs="?", default=None,
                        help="세션 디렉토리 경로 (camera_2/3 폴더 포함)")
    parser.add_argument("--camera", type=int, default=None, help="카메라 인덱스 (예: 2 또는 3)")
    parser.add_argument("--side", choices=["left", "right"], default=None, help="바켓 위치 (left/right)")
    parser.add_argument("--config", default="config_jetson2_web.json", help="Config JSON path")
    parser.add_argument("--device", default="cuda", help="Ultralytics device (cuda/cpu/0)")
    parser.add_argument("--display", action="store_true", help="Show visualization window")
    parser.add_argument("--display-fps", type=float, default=10.0,
                        help="Display playback FPS when --display is enabled")
    parser.add_argument("--save-vis", default=None, help="Save visualized frames to folder")
    parser.add_argument("--max-images", type=int, default=0, help="Run only first N images (0=all)")
    parser.add_argument("--base-dir", default="~/AI_Data/pot1",
                        help="세션 자동 목록 기준 경로 (기본: ~/AI_Data/pot1)")
    parser.add_argument("--auto-all", action="store_true", help="Run all sessions under --base-dir")
    parser.add_argument("--auto-sides", choices=["both", "left", "right"], default="both",
                        help="When --auto-all, choose sides to run")
    args = parser.parse_args()

    if args.session_dir is None and not args.auto_all:
        print("사용법:")
        print("  python test_bucket_detection_simulation.py <session_dir> [--side left|right]")
        print("  python test_bucket_detection_simulation.py --auto-all --base-dir ~/AI_Data/pot1")
        print("\n예시:")
        print("  python test_bucket_detection_simulation.py ~/AI_Data/session_20260130_123456 --side left")
        print("\n최근 세션:")
        list_recent_sessions(args.base_dir)
        return

    config = load_config(args.config)
    left_cam = config.get("observe_left_camera_index", 2)
    right_cam = config.get("observe_right_camera_index", 3)

    if args.auto_all:
        sessions = get_sessions(args.base_dir)
        if not sessions:
            print(f"❌ 세션 없음: {os.path.expanduser(args.base_dir)}")
            return
        all_results = []
        for s in sessions:
            run_sides = []
            if args.auto_sides in ("both", "left"):
                run_sides.append("left")
            if args.auto_sides in ("both", "right"):
                run_sides.append("right")
            for side in run_sides:
                cam_idx = left_cam if side == "left" else right_cam
                resolved_session_dir, camera_dir = resolve_camera_dir(s, cam_idx)
                if not camera_dir:
                    print(f"[SKIP] {os.path.basename(s)} side={side} camera_{cam_idx} 없음")
                    continue
                result = simulate_session(s, cam_idx, side, args)
                if result:
                    all_results.append(result)
        if all_results:
            print("\n" + "#" * 80)
            print("AUTO RUN SUMMARY")
            print("#" * 80)
            for r in all_results:
                print(
                    f"- {os.path.basename(r['session_dir'])} side={r['side']} "
                    f"detected={r['detected_count']}/{r['total_images']} "
                    f"filled={r['filled_count']}"
                )
        return

    session_dir = os.path.expanduser(args.session_dir)
    if not os.path.exists(session_dir):
        print(f"❌ 세션 디렉토리 없음: {session_dir}")
        return

    if args.side is None and args.camera is None:
        args.side = "left"

    if args.side is not None:
        camera_idx = left_cam if args.side == "left" else right_cam
        side = args.side
    else:
        camera_idx = args.camera
        side = "right" if camera_idx == right_cam else "left"

    simulate_session(session_dir, camera_idx, side, args)


if __name__ == "__main__":
    main()
