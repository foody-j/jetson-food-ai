#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
과제보고서용 토스트 오버레이 시뮬레이터
실제 GUI 위에 이벤트 토스트를 직접 띄우는 도구
"""

import tkinter as tk
from datetime import datetime
import time

class ToastOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎬 토스트 오버레이")
        self.root.geometry("400x600")
        self.root.configure(bg="white")

        # 항상 최상위에 표시
        self.root.attributes('-topmost', True)

        self.setup_gui()

    def setup_gui(self):
        """GUI 구성"""
        # 제목
        title = tk.Label(
            self.root,
            text="🎬 토스트 오버레이",
            font=("맑은 고딕", 16, "bold"),
            bg="white",
            fg="#2C3E50"
        )
        title.pack(pady=15)

        info = tk.Label(
            self.root,
            text="버튼을 클릭하면 화면에 토스트가 표시됩니다\n(1.5초 후 자동으로 사라집니다)",
            font=("맑은 고딕", 9),
            bg="white",
            fg="#7F8C8D",
            justify='center'
        )
        info.pack(pady=(0, 20))

        # 버튼들
        button_config = [
            ("🌙 야간 모션 감지", "#9B59B6", "야간 모션 감지 - 스냅샷 저장"),
            ("📳 진동 측정 시작", "#3498DB", "진동 측정 시작"),
            ("✅ 진동 정상", "#27AE60", "진동 정상 (45/100 mm/s)"),
            ("⚠️ 진동 이상!", "#E74C3C", "진동 이상! (150/100 mm/s)"),
            ("🍳 볶음 POT1 투입", "#F39C12", "볶음 POT1: 짜장"),
            ("🍳 볶음 POT2 투입", "#F39C12", "볶음 POT2: 짬뽕"),
            ("🍤 튀김 완료", "#27AE60", "튀김 완료 - 건져주세요"),
            ("🔥 과조리 경고", "#E74C3C", "과조리 주의!"),
        ]

        for text, color, toast_msg in button_config:
            btn = tk.Button(
                self.root,
                text=text,
                font=("맑은 고딕", 11, "bold"),
                bg=color,
                fg="white",
                padx=15,
                pady=10,
                command=lambda msg=toast_msg: self.show_toast(msg)
            )
            btn.pack(fill='x', padx=20, pady=5)

        # 커스텀 메시지
        tk.Label(
            self.root,
            text="💬 커스텀 메시지",
            font=("맑은 고딕", 11, "bold"),
            bg="white",
            fg="#34495E"
        ).pack(pady=(20, 5))

        self.custom_entry = tk.Entry(
            self.root,
            font=("맑은 고딕", 11),
            bg="#ECF0F1"
        )
        self.custom_entry.pack(fill='x', padx=20, pady=5)
        self.custom_entry.insert(0, "원하는 메시지 입력")

        tk.Button(
            self.root,
            text="커스텀 토스트 표시",
            font=("맑은 고딕", 10),
            bg="#34495E",
            fg="white",
            padx=15,
            pady=8,
            command=self.show_custom_toast
        ).pack(fill='x', padx=20, pady=5)

        # 위치 조정 프레임
        position_frame = tk.LabelFrame(
            self.root,
            text="토스트 위치",
            font=("맑은 고딕", 10, "bold"),
            bg="white",
            padx=10,
            pady=10
        )
        position_frame.pack(fill='x', padx=20, pady=(15, 10))

        self.position_var = tk.StringVar(value="center")

        positions = [
            ("상단 중앙", "top"),
            ("중앙", "center"),
            ("하단 중앙", "bottom")
        ]

        for text, value in positions:
            tk.Radiobutton(
                position_frame,
                text=text,
                variable=self.position_var,
                value=value,
                font=("맑은 고딕", 9),
                bg="white"
            ).pack(anchor='w')

    def show_custom_toast(self):
        """커스텀 메시지 토스트 표시"""
        msg = self.custom_entry.get()
        if msg and msg != "원하는 메시지 입력":
            self.show_toast(msg)

    def show_toast(self, message, duration_ms=1500):
        """토스트 메시지 표시"""
        # 기존 토스트 제거
        if hasattr(self, '_toast_window') and self._toast_window:
            try:
                self._toast_window.destroy()
            except:
                pass
            self._toast_window = None

        # 새 토스트 창 생성 (독립 Toplevel)
        toast = tk.Toplevel(self.root)
        toast.withdraw()  # 먼저 숨김

        # 창 설정
        toast.overrideredirect(True)  # 테두리 제거
        toast.attributes('-topmost', True)  # 항상 최상위

        # 배경 투명도 (Linux에서는 제한적)
        try:
            toast.attributes('-alpha', 0.95)
        except:
            pass

        # 토스트 내용
        label = tk.Label(
            toast,
            text=message,
            font=("맑은 고딕", 20, "bold"),
            fg="white",
            bg="#E74C3C",  # 빨간색 배경 (실제 JETSON GUI와 동일)
            padx=30,
            pady=15,
            relief='raised',
            borderwidth=2
        )
        label.pack()

        # 화면 크기 가져오기
        screen_width = toast.winfo_screenwidth()
        screen_height = toast.winfo_screenheight()

        # 토스트 크기 업데이트
        toast.update_idletasks()
        toast_width = label.winfo_reqwidth()
        toast_height = label.winfo_reqheight()

        # 위치 계산
        x = (screen_width - toast_width) // 2

        position = self.position_var.get()
        if position == "top":
            y = int(screen_height * 0.15)
        elif position == "center":
            y = (screen_height - toast_height) // 2
        else:  # bottom
            y = int(screen_height * 0.75)

        # 위치 설정 및 표시
        toast.geometry(f"+{x}+{y}")
        toast.deiconify()  # 표시

        # 로그 출력
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 토스트 표시: {message}")

        # 자동 제거 타이머
        self._toast_window = toast
        toast.after(duration_ms, lambda: self._hide_toast(toast))

    def _hide_toast(self, toast_window):
        """토스트 제거"""
        try:
            toast_window.destroy()
        except:
            pass

    def run(self):
        """메인 루프"""
        self.root.mainloop()

if __name__ == "__main__":
    print("=" * 60)
    print("과제보고서용 토스트 오버레이 시작")
    print("=" * 60)
    print("사용법:")
    print("1. 실제 Jetson GUI (JETSON1/2_INTEGRATED.py)를 실행")
    print("2. 이 스크립트를 실행하여 토스트 버튼 클릭")
    print("3. GUI 화면을 캡쳐하여 보고서에 사용")
    print("=" * 60)

    app = ToastOverlay()
    app.run()
