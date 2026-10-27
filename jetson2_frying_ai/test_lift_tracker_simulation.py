#!/usr/bin/env python3
"""
LiftEventTracker 시뮬레이션 테스트
- 기존 수집 데이터로 YOLO segmentation + 탈탈 감지 테스트
- 색상 변화 추적 검증
- 완료 판단 검증
"""

import os
import sys
import glob
import json
import cv2
import argparse
from datetime import datetime

from frying_segmenter import FoodSegmenter
from lift_event_tracker import LiftEventTracker


def simulate_session(session_dir: str, camera_idx: int = 0):
    """
    세션 시뮬레이션

    Args:
        session_dir: 세션 디렉토리 경로 (예: ~/AI_Data/FryingData/session_xxx)
        camera_idx: 카메라 번호 (0 또는 1)
    """
    print("=" * 80)
    print(f"🔍 세션 시뮬레이션 시작: {os.path.basename(session_dir)}")
    print("=" * 80)

    # 이미지 파일 목록
    camera_dir = os.path.join(session_dir, f"camera_{camera_idx}")
    if not os.path.exists(camera_dir):
        print(f"❌ 카메라 디렉토리 없음: {camera_dir}")
        return

    image_files = sorted(glob.glob(os.path.join(camera_dir, "*.jpg")))
    if len(image_files) == 0:
        print(f"❌ 이미지 파일 없음: {camera_dir}")
        return

    print(f"📁 카메라 디렉토리: {camera_dir}")
    print(f"📸 총 이미지 수: {len(image_files)}")

    # session_info.json 로드
    session_info_path = os.path.join(session_dir, "session_info.json")
    session_info = {}
    if os.path.exists(session_info_path):
        with open(session_info_path, 'r') as f:
            session_info = json.load(f)
        print(f"📋 세션 정보: {session_info.get('food_type', 'unknown')}")

    # Config 로드
    config_path = os.path.join(os.path.dirname(__file__), "config_jetson2.json")
    with open(config_path, 'r') as f:
        config = json.load(f)

    # FoodSegmenter 초기화
    print("\n🔧 FoodSegmenter 초기화 중...")
    segmenter = FoodSegmenter(model_path="frying_seg.pt")
    print(f"   YOLO 사용: {segmenter.use_yolo}")

    # LiftEventTracker 초기화
    print("🔧 LiftEventTracker 초기화 중...")
    pot_name = f"POT{camera_idx + 1}"
    tracker = LiftEventTracker(pot_name, config)

    # 세션 시작
    session_id = os.path.basename(session_dir)
    food_type = session_info.get('food_type', 'unknown')
    target_time = 180  # 기본 180초

    tracker.start_session(session_id, food_type, target_time)

    # 이미지별 처리
    print(f"\n🚀 이미지 처리 시작 (총 {len(image_files)}장)...\n")

    lift_detected_count = 0

    for i, img_path in enumerate(image_files):
        # 이미지 로드
        image = cv2.imread(img_path)
        if image is None:
            print(f"⚠ 이미지 로드 실패: {img_path}")
            continue

        # Segmentation
        try:
            seg_result = segmenter.segment(image, visualize=False)
        except Exception as e:
            print(f"⚠ Segmentation 오류 [{i+1}/{len(image_files)}]: {e}")
            continue

        # Lift event tracking
        lift_status = tracker.process_frame(seg_result)

        # 결과 출력
        if lift_status['lift_detected']:
            lift_detected_count += 1
            print(f"[{i+1:3d}/{len(image_files)}] 🟢 탈탈 감지 #{lift_status['lift_count']} | "
                  f"시간={lift_status['running_time']:.1f}초, "
                  f"색변화={lift_status['color_delta']:.1f}, "
                  f"area_ratio={seg_result.food_area_ratio:.3f}")
        elif seg_result.food_area_ratio > 0.05:
            # 튀김은 보이지만 탈탈로 감지 안 된 경우
            print(f"[{i+1:3d}/{len(image_files)}] 🔵 튀김 보임 (탈탈X) | "
                  f"area_ratio={seg_result.food_area_ratio:.3f}")

        # 완료 감지 시
        if lift_status['completion_detected']:
            print(f"\n{'=' * 80}")
            print(f"✅ 완료 감지! (이미지 {i+1}/{len(image_files)})")
            print(f"   탈탈 횟수: {lift_status['lift_count']}회")
            print(f"   경과 시간: {lift_status['running_time']:.1f}초 (목표: {target_time}초)")
            print(f"   색상 변화: {lift_status['color_delta']:.1f} (임계값: {tracker.color_change_threshold})")
            print(f"{'=' * 80}\n")

    # 세션 종료
    tracker.stop_session()

    # 결과 요약
    print("\n" + "=" * 80)
    print("📊 시뮬레이션 결과")
    print("=" * 80)
    print(f"총 이미지 수: {len(image_files)}")
    print(f"탈탈 감지 횟수: {lift_detected_count}")
    print(f"완료 감지 여부: {'✅ YES' if lift_status['completion_detected'] else '❌ NO'}")

    status = tracker.get_status()
    if status['active']:
        print(f"마지막 색상 변화: {status['last_color_delta']:.1f}")

    # 데이터 저장 테스트
    print("\n💾 탈탈 데이터 저장 테스트...")
    output_dir = os.path.join(session_dir, "simulation_output")
    os.makedirs(output_dir, exist_ok=True)

    saved_path = tracker.save_session_data(output_dir)
    if saved_path:
        print(f"   저장 완료: {saved_path}")

        # 저장된 데이터 확인
        with open(saved_path, 'r') as f:
            saved_data = json.load(f)

        print(f"\n📋 저장된 데이터:")
        print(f"   세션 ID: {saved_data['session_id']}")
        print(f"   음식 종류: {saved_data['food_type']}")
        print(f"   탈탈 횟수: {saved_data['lift_count']}")
        print(f"   완료 감지: {saved_data['completion_detected']}")

        if saved_data['lift_events']:
            print(f"\n   탈탈 이벤트:")
            for i, event in enumerate(saved_data['lift_events'], 1):
                print(f"      #{i}: 시간={event['running_time']:.1f}초, "
                      f"색변화={event['color_delta']:.1f}, "
                      f"brown={event['brown_ratio']:.2f}, "
                      f"golden={event['golden_ratio']:.2f}")

    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="LiftEventTracker 시뮬레이션 테스트")
    parser.add_argument("session_dir", help="세션 디렉토리 경로")
    parser.add_argument("--camera", type=int, default=0, choices=[0, 1],
                       help="카메라 번호 (0=왼쪽, 1=오른쪽)")

    args = parser.parse_args()

    # 경로 확장
    session_dir = os.path.expanduser(args.session_dir)

    if not os.path.exists(session_dir):
        print(f"❌ 세션 디렉토리 없음: {session_dir}")
        return

    simulate_session(session_dir, args.camera)


if __name__ == "__main__":
    # 기본 테스트 (인자 없이 실행 시)
    if len(sys.argv) == 1:
        print("사용법:")
        print("  python test_lift_tracker_simulation.py <session_dir> [--camera 0|1]")
        print("\n예시:")
        print("  python test_lift_tracker_simulation.py ~/AI_Data/FryingData/session_20251217_141907")
        print("  python test_lift_tracker_simulation.py ~/AI_Data/FryingData/session_20251217_141907 --camera 1")
        print("\n사용 가능한 세션:")

        data_dir = os.path.expanduser("~/AI_Data/FryingData")
        if os.path.exists(data_dir):
            sessions = sorted(glob.glob(os.path.join(data_dir, "session_*")))
            for session in sessions[-5:]:  # 최근 5개
                session_name = os.path.basename(session)
                img_count_0 = len(glob.glob(os.path.join(session, "camera_0", "*.jpg")))
                img_count_1 = len(glob.glob(os.path.join(session, "camera_1", "*.jpg")))
                print(f"  - {session_name} (cam0: {img_count_0}장, cam1: {img_count_1}장)")
    else:
        main()
