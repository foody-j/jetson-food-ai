#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
과제보고서용 이벤트 시뮬레이터
Jetson #1 / #2 GUI에 야간 감시, 진동센서 이벤트를 띄우기 위한 테스트 도구
"""

import tkinter as tk
from tkinter import ttk
import paho.mqtt.client as mqtt
import json
import time
from datetime import datetime

# MQTT 설정
MQTT_BROKER = "192.168.0.100"
MQTT_PORT = 1883

class EventSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎬 과제보고서용 이벤트 시뮬레이터")
        self.root.geometry("600x700")
        self.root.configure(bg="white")

        # MQTT 클라이언트
        self.mqtt_client = None
        self.mqtt_connected = False

        self.setup_gui()
        self.connect_mqtt()

    def setup_gui(self):
        """GUI 구성"""
        # 제목
        title = tk.Label(
            self.root,
            text="🎬 과제보고서용 이벤트 시뮬레이터",
            font=("맑은 고딕", 18, "bold"),
            bg="white",
            fg="#2C3E50"
        )
        title.pack(pady=20)

        # MQTT 상태
        self.mqtt_status = tk.Label(
            self.root,
            text="MQTT: 연결 중...",
            font=("맑은 고딕", 12),
            bg="white",
            fg="#E74C3C"
        )
        self.mqtt_status.pack(pady=5)

        # 구분선
        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=20)

        # ====================
        # Jetson #1 이벤트
        # ====================
        j1_frame = tk.LabelFrame(
            self.root,
            text="📟 Jetson #1 (사람 감지 + 볶음)",
            font=("맑은 고딕", 14, "bold"),
            bg="white",
            fg="#3498DB",
            padx=20,
            pady=15
        )
        j1_frame.pack(fill='x', padx=20, pady=10)

        # 야간 감시 이벤트
        tk.Label(
            j1_frame,
            text="🌙 야간 감시 모션 감지",
            font=("맑은 고딕", 12),
            bg="white"
        ).pack(anchor='w', pady=(0, 5))

        tk.Button(
            j1_frame,
            text="야간 모션 감지 시뮬레이션",
            font=("맑은 고딕", 11),
            bg="#9B59B6",
            fg="white",
            padx=15,
            pady=8,
            command=self.trigger_night_motion
        ).pack(fill='x', pady=5)

        # 진동 이벤트
        tk.Label(
            j1_frame,
            text="📳 진동센서 이벤트",
            font=("맑은 고딕", 12),
            bg="white"
        ).pack(anchor='w', pady=(15, 5))

        btn_frame = tk.Frame(j1_frame, bg="white")
        btn_frame.pack(fill='x')

        tk.Button(
            btn_frame,
            text="진동 측정 시작",
            font=("맑은 고딕", 10),
            bg="#3498DB",
            fg="white",
            padx=10,
            pady=6,
            command=self.trigger_vibration_start
        ).pack(side='left', expand=True, fill='x', padx=(0, 5))

        tk.Button(
            btn_frame,
            text="진동 정상",
            font=("맑은 고딕", 10),
            bg="#27AE60",
            fg="white",
            padx=10,
            pady=6,
            command=lambda: self.trigger_vibration_result("NORMAL")
        ).pack(side='left', expand=True, fill='x', padx=5)

        tk.Button(
            btn_frame,
            text="진동 이상!",
            font=("맑은 고딕", 10),
            bg="#E74C3C",
            fg="white",
            padx=10,
            pady=6,
            command=lambda: self.trigger_vibration_result("ABNORMAL")
        ).pack(side='left', expand=True, fill='x', padx=(5, 0))

        # 볶음 투입 이벤트
        tk.Label(
            j1_frame,
            text="🍳 볶음 투입 알림",
            font=("맑은 고딕", 12),
            bg="white"
        ).pack(anchor='w', pady=(15, 5))

        stir_frame = tk.Frame(j1_frame, bg="white")
        stir_frame.pack(fill='x')

        tk.Button(
            stir_frame,
            text="POT1 투입",
            font=("맑은 고딕", 10),
            bg="#F39C12",
            fg="white",
            padx=10,
            pady=6,
            command=lambda: self.trigger_stirfry("POT1")
        ).pack(side='left', expand=True, fill='x', padx=(0, 5))

        tk.Button(
            stir_frame,
            text="POT2 투입",
            font=("맑은 고딕", 10),
            bg="#F39C12",
            fg="white",
            padx=10,
            pady=6,
            command=lambda: self.trigger_stirfry("POT2")
        ).pack(side='left', expand=True, fill='x', padx=(5, 0))

        # ====================
        # Jetson #2 이벤트
        # ====================
        j2_frame = tk.LabelFrame(
            self.root,
            text="📟 Jetson #2 (튀김 AI + 바켓)",
            font=("맑은 고딕", 14, "bold"),
            bg="white",
            fg="#E67E22",
            padx=20,
            pady=15
        )
        j2_frame.pack(fill='x', padx=20, pady=10)

        # 튀김 상태 이벤트
        tk.Label(
            j2_frame,
            text="🍤 튀김 상태 알림",
            font=("맑은 고딕", 12),
            bg="white"
        ).pack(anchor='w', pady=(0, 5))

        fry_frame = tk.Frame(j2_frame, bg="white")
        fry_frame.pack(fill='x')

        tk.Button(
            fry_frame,
            text="튀김 완료",
            font=("맑은 고딕", 10),
            bg="#27AE60",
            fg="white",
            padx=10,
            pady=6,
            command=lambda: self.trigger_frying_status("DONE")
        ).pack(side='left', expand=True, fill='x', padx=(0, 5))

        tk.Button(
            fry_frame,
            text="과조리 경고",
            font=("맑은 고딕", 10),
            bg="#E74C3C",
            fg="white",
            padx=10,
            pady=6,
            command=lambda: self.trigger_frying_status("OVERCOOKED")
        ).pack(side='left', expand=True, fill='x', padx=(5, 0))

        # 로그 영역
        ttk.Separator(self.root, orient='horizontal').pack(fill='x', pady=20)

        tk.Label(
            self.root,
            text="📋 실행 로그",
            font=("맑은 고딕", 12, "bold"),
            bg="white"
        ).pack(anchor='w', padx=20)

        log_frame = tk.Frame(self.root, bg="white")
        log_frame.pack(fill='both', expand=True, padx=20, pady=(5, 20))

        scrollbar = tk.Scrollbar(log_frame)
        scrollbar.pack(side='right', fill='y')

        self.log_text = tk.Text(
            log_frame,
            height=8,
            font=("맑은 고딕", 9),
            bg="#ECF0F1",
            fg="#2C3E50",
            yscrollcommand=scrollbar.set
        )
        self.log_text.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.log_text.yview)

    def log(self, message):
        """로그 출력"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')
        print(f"[{timestamp}] {message}")

    def connect_mqtt(self):
        """MQTT 연결"""
        try:
            self.mqtt_client = mqtt.Client()
            self.mqtt_client.on_connect = self.on_mqtt_connect
            self.mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
            self.mqtt_client.loop_start()
        except Exception as e:
            self.log(f"❌ MQTT 연결 실패: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """MQTT 연결 콜백"""
        if rc == 0:
            self.mqtt_connected = True
            self.mqtt_status.config(text=f"MQTT: ✅ 연결됨 ({MQTT_BROKER})", fg="#27AE60")
            self.log(f"✅ MQTT 브로커 연결 성공: {MQTT_BROKER}")
        else:
            self.mqtt_status.config(text=f"MQTT: ❌ 연결 실패 (code {rc})", fg="#E74C3C")
            self.log(f"❌ MQTT 연결 실패: code {rc}")

    def publish_mqtt(self, topic, payload):
        """MQTT 메시지 발행"""
        if not self.mqtt_connected:
            self.log("⚠ MQTT 연결 안 됨")
            return False

        try:
            msg = json.dumps(payload, ensure_ascii=False)
            self.mqtt_client.publish(topic, msg)
            self.log(f"📤 발행: {topic}")
            self.log(f"   └─ {msg}")
            return True
        except Exception as e:
            self.log(f"❌ 발행 실패: {e}")
            return False

    # ====================
    # 이벤트 트리거 함수들
    # ====================

    def trigger_night_motion(self):
        """야간 모션 감지 시뮬레이션"""
        self.log("🌙 야간 모션 감지 이벤트 발생")
        # Jetson #1은 자체적으로 motion detection을 하므로
        # 직접 트리거할 수 없음. 안내 메시지만 표시
        self.log("   ⚠ 실제로는 카메라 앞에서 움직여야 합니다")
        self.log("   💡 또는 개발자 모드에서 스냅샷 저장 버튼 사용")

    def trigger_vibration_start(self):
        """진동 측정 시작"""
        payload = {
            "timestamp": datetime.now().isoformat(),
            "DeviceNum": 1,
            "ChkVibration": True,
            "command": "start"
        }
        if self.publish_mqtt("jetson1/vibration/command", payload):
            self.log("📳 진동 측정 시작 명령 전송 완료")

    def trigger_vibration_result(self, status):
        """진동 측정 결과 시뮬레이션"""
        if status == "NORMAL":
            vel_mag_max = 45.0
            threshold = 100.0
        else:  # ABNORMAL
            vel_mag_max = 150.0
            threshold = 100.0

        payload = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "vel_mag_max": vel_mag_max,
            "threshold": threshold
        }

        # Jetson #1이 직접 결과를 처리하도록 내부 토픽으로 전송
        # (실제로는 진동센서 스크립트가 파일로 저장하고 읽음)
        self.log(f"📳 진동 결과 시뮬레이션: {status}")
        self.log(f"   └─ 최대진동: {vel_mag_max:.1f} mm/s (임계값: {threshold:.1f})")
        self.log("   ⚠ 실제 GUI에 표시하려면 JETSON1_INTEGRATED.py에서")
        self.log("      show_toast() 함수를 직접 호출해야 합니다")

    def trigger_stirfry(self, pot_name):
        """볶음 투입 이벤트"""
        payload = {
            "timestamp": datetime.now().isoformat(),
            "pot": pot_name,
            "StRecipe_Left": "짜장" if pot_name == "POT1" else "짬뽕",
            "ChkAutoStart": True
        }

        topic = "jetson1/stirfry/event" if pot_name == "POT1" else "jetson1/stirfry/event"
        if self.publish_mqtt(topic, payload):
            self.log(f"🍳 {pot_name} 투입 이벤트 전송 완료")

    def trigger_frying_status(self, status):
        """튀김 상태 이벤트 (Jetson #2)"""
        payload = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "message": "튀김 완료!" if status == "DONE" else "과조리 주의!"
        }

        if self.publish_mqtt("jetson2/frying/status", payload):
            self.log(f"🍤 튀김 상태 이벤트 전송: {status}")

    def run(self):
        """메인 루프 실행"""
        self.root.mainloop()

    def __del__(self):
        """종료 시 MQTT 연결 해제"""
        if self.mqtt_client:
            self.mqtt_client.loop_stop()
            self.mqtt_client.disconnect()

if __name__ == "__main__":
    print("=" * 60)
    print("과제보고서용 이벤트 시뮬레이터 시작")
    print("=" * 60)

    app = EventSimulator()
    app.run()
