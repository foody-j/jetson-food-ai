#!/usr/bin/env python3
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import font_manager, rcParams
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch


def add_box(ax, xy, wh, title, lines, fc="#f5f7fb", ec="#1f2937"):
    x, y = xy
    w, h = wh
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.02,rounding_size=0.02",
        linewidth=1.8,
        edgecolor=ec,
        facecolor=fc,
    )
    ax.add_patch(patch)
    ax.text(x + w / 2, y + h * 0.72, title, ha="center", va="center", fontsize=15, fontweight="bold")
    ax.text(x + w / 2, y + h * 0.40, "\n".join(lines), ha="center", va="center", fontsize=11)
    return patch


def add_arrow(ax, start, end, text=""):
    arrow = FancyArrowPatch(
        start,
        end,
        arrowstyle="-|>",
        mutation_scale=18,
        linewidth=1.8,
        color="#374151",
    )
    ax.add_patch(arrow)
    if text:
        mx = (start[0] + end[0]) / 2
        my = (start[1] + end[1]) / 2
        ax.text(mx, my + 0.035, text, ha="center", va="bottom", fontsize=10, color="#374151")


def main():
    out = Path("reports/figures/vibration_svm_pipeline.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    font_candidates = [
        "Noto Sans CJK JP",
        "NanumGothic",
        "Malgun Gothic",
        "AppleGothic",
    ]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in font_candidates:
        if name in available:
            rcParams["font.family"] = name
            break
    rcParams["axes.unicode_minus"] = False

    fig, ax = plt.subplots(figsize=(16, 8), dpi=180)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    fig.patch.set_facecolor("white")

    ax.text(
        0.5,
        0.94,
        "USB-RS485 / Modbus RTU 기반 진동 모니터링 파이프라인",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color="#111827",
    )
    ax.text(
        0.5,
        0.90,
        "이벤트 구간 FFT 시계열 생성 및 1D CNN 기반 정상/이상 판정 흐름",
        ha="center",
        va="center",
        fontsize=12,
        color="#4b5563",
    )

    add_box(
        ax,
        (0.04, 0.56),
        (0.14, 0.20),
        "진동 센서",
        ["모터 / 프레임", "진동 신호", "취득"],
        fc="#e5f4ff",
    )
    add_box(
        ax,
        (0.23, 0.56),
        (0.16, 0.20),
        "USB-RS485",
        ["시리얼 브리지", "Modbus RTU", "패킷 전송"],
        fc="#eef2ff",
    )
    add_box(
        ax,
        (0.44, 0.56),
        (0.16, 0.20),
        "PME 노드",
        ["Jetson 노드", "연속 수집", "데이터 처리"],
        fc="#ecfeef",
    )
    add_box(
        ax,
        (0.65, 0.56),
        (0.14, 0.20),
        "이벤트 구간 추출",
        ["트리거 기반", "구간 분리", "분석 입력 구성"],
        fc="#fff7e8",
    )
    add_box(
        ax,
        (0.84, 0.56),
        (0.12, 0.20),
        "FFT 시계열 생성",
        ["주파수 특징", "시계열 정규화"],
        fc="#fff1f2",
    )

    add_box(
        ax,
        (0.24, 0.18),
        (0.18, 0.20),
        "1D CNN 모델",
        ["시간축 패턴 학습", "정상/이상 분류"],
        fc="#f3e8ff",
    )
    add_box(
        ax,
        (0.49, 0.18),
        (0.20, 0.20),
        "판정 엔진",
        ["정상 / 이상", "오탐 억제", "연속 운영"],
        fc="#ede9fe",
    )
    add_box(
        ax,
        (0.76, 0.18),
        (0.18, 0.20),
        "출력 / 로깅",
        ["대시보드", "이벤트 로그", "유지보수 알림"],
        fc="#fef3c7",
    )

    add_arrow(ax, (0.18, 0.66), (0.23, 0.66), "센서 스트림")
    add_arrow(ax, (0.39, 0.66), (0.44, 0.66), "Modbus RTU")
    add_arrow(ax, (0.60, 0.66), (0.65, 0.66), "이벤트 시계열")
    add_arrow(ax, (0.79, 0.66), (0.84, 0.66), "FFT 시계열")
    add_arrow(ax, (0.90, 0.56), (0.90, 0.38), "추론 입력")
    add_arrow(ax, (0.84, 0.28), (0.69, 0.28))
    add_arrow(ax, (0.42, 0.28), (0.49, 0.28), "분류 결과")
    add_arrow(ax, (0.69, 0.28), (0.76, 0.28), "판정 결과")

    ax.text(
        0.5,
        0.06,
        "그림. USB-RS485 Modbus RTU 기반 진동 데이터 수집, 이벤트 구간 FFT 시계열 생성, 1D CNN 기반 정상/이상 판정 개념도.",
        ha="center",
        va="center",
        fontsize=11,
        color="#374151",
    )

    plt.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    print(out)


if __name__ == "__main__":
    main()
