#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight frying web for headless showcase.

Logic:
- Subscribe only to HR/Status
- Show current left/right pot state on a simple web page
- Treat ProcessType == "배출" as a complete event for display
- Allow manual trigger buttons for local preview without MQTT events
"""

import argparse
import json
import os
import sys
import threading
import time
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from socketserver import ThreadingMixIn
from urllib.parse import urlparse

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("paho-mqtt is required: pip install paho-mqtt", file=sys.stderr)
    sys.exit(1)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "jetson2_frying_ai", "config_jetson2_web.json")


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_time_text(value):
    if not value:
        return 0
    value = str(value).strip()
    if "분" in value or "초" in value:
        minutes = 0
        seconds = 0
        if "분" in value:
            left, right = value.split("분", 1)
            try:
                minutes = int(left.strip() or "0")
            except ValueError:
                minutes = 0
            value = right
        if "초" in value:
            sec_txt = value.split("초", 1)[0].strip()
            try:
                seconds = int(sec_txt or "0")
            except ValueError:
                seconds = 0
        return minutes * 60 + seconds

    parts = value.split(":")
    if len(parts) == 3:
        try:
            hours, minutes, seconds = [int(float(p)) for p in parts]
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return 0
    return 0


class DemoState:
    def __init__(self):
        self.lock = threading.Lock()
        self.started_at = time.time()
        self.mqtt_connected = False
        self.last_hr_status_at = None
        self.last_complete = None
        self.logs = deque(maxlen=80)
        self.pots = {
            "left": self._new_pot("left", "왼쪽"),
            "right": self._new_pot("right", "오른쪽"),
        }

    @staticmethod
    def _new_pot(key, label):
        return {
            "key": key,
            "label": label,
            "pt_num": "0" if key == "left" else "1",
            "process_type": "-",
            "now_recipe": "-",
            "target_time": "-",
            "running_time": "-",
            "oil_temp": None,
            "rb_status": "-",
            "mode": "-",
            "demo_complete_until": 0.0,
            "last_update": None,
        }

    def log(self, message):
        with self.lock:
            self.logs.append({
                "ts": now_str(),
                "message": message,
            })

    def set_mqtt(self, connected):
        with self.lock:
            self.mqtt_connected = connected

    def update_from_hr_status(self, payload):
        statuses = payload.get("Status", [])
        complete_events = []
        with self.lock:
            self.last_hr_status_at = now_str()
            for pot_data in statuses:
                pt_num = str(pot_data.get("PTNum", ""))
                side = "left" if pt_num == "0" else "right" if pt_num == "1" else None
                if side is None:
                    continue

                pot = self.pots[side]
                prev_process = pot["process_type"]
                process_type = str(pot_data.get("ProcessType", "") or "-")
                now_recipe = str(pot_data.get("NowRecipe", "") or "-")
                target_time = str(pot_data.get("TargetTime", "") or "-")
                running_time = str(pot_data.get("RunningTime", "") or "-")
                potstatus = pot_data.get("Potstatus") or {}

                pot["process_type"] = process_type
                pot["now_recipe"] = now_recipe
                pot["target_time"] = target_time
                pot["running_time"] = running_time
                pot["oil_temp"] = potstatus.get("PT_Temp")
                pot["rb_status"] = str(pot_data.get("RBstatus", "") or "-").replace("\n", " ")
                pot["mode"] = str(pot_data.get("Mode", "") or "-")
                pot["last_update"] = now_str()

                if prev_process != process_type:
                    self.logs.append({
                        "ts": now_str(),
                        "message": f"{pot['label']}솥 상태 변경: {prev_process} -> {process_type}",
                    })

                if process_type == "배출" and prev_process != "배출":
                    event = self.trigger_complete_locked(side, "배출 신호 수신")
                    complete_events.append(event)

        return complete_events

    def trigger_complete(self, side, reason="수동 완료"):
        with self.lock:
            return self.trigger_complete_locked(side, reason)

    def trigger_complete_locked(self, side, reason):
        pot = self.pots[side]
        pot["demo_complete_until"] = time.time() + 15.0
        event = {
            "ts": now_str(),
            "side": side,
            "label": pot["label"],
            "recipe": pot["now_recipe"],
            "running_time": pot["running_time"],
            "target_time": pot["target_time"],
            "oil_temp": pot["oil_temp"],
            "reason": reason,
        }
        self.last_complete = event
        self.logs.append({
            "ts": event["ts"],
            "message": (
                f"완료 표시: {pot['label']}솥 / 레시피={pot['now_recipe']} / "
                f"{reason} / RunningTime={pot['running_time']} / TargetTime={pot['target_time']}"
            ),
        })
        return event

    def snapshot(self):
        with self.lock:
            now = time.time()
            pots = []
            for key in ("left", "right"):
                pot = dict(self.pots[key])
                pot["complete_active"] = now < float(pot["demo_complete_until"])
                pot["running_sec"] = parse_time_text(pot["running_time"])
                pot["target_sec"] = parse_time_text(pot["target_time"])
                pots.append(pot)
            return {
                "server_time": now_str(),
                "uptime_sec": int(now - self.started_at),
                "mqtt_connected": self.mqtt_connected,
                "last_hr_status_at": self.last_hr_status_at,
                "last_complete": self.last_complete,
                "pots": pots,
                "logs": list(self.logs)[-20:],
            }


HTML = """<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Frying Dashboard</title>
  <style>
    :root {
      --bg: #0c1117;
      --panel: #151d26;
      --card: #1c2733;
      --line: #2a3a4b;
      --text: #eef3f8;
      --muted: #94a6b8;
      --ok: #21c97a;
      --warn: #ffb020;
      --hot: #ff6b57;
      --accent: #4cc9f0;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Malgun Gothic", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(76,201,240,0.10), transparent 26%),
        radial-gradient(circle at top right, rgba(255,107,87,0.14), transparent 24%),
        linear-gradient(180deg, #091019 0%, var(--bg) 100%);
      color: var(--text);
    }
    .wrap { max-width: 1400px; margin: 0 auto; padding: 24px; }
    .head {
      display: flex; justify-content: space-between; align-items: center; gap: 16px;
      margin-bottom: 18px; padding: 18px 20px; border: 1px solid var(--line);
      border-radius: 18px; background: rgba(21,29,38,0.88); backdrop-filter: blur(8px);
    }
    .title { font-size: 34px; font-weight: 800; letter-spacing: 0.5px; }
    .sub { color: var(--muted); margin-top: 6px; font-size: 14px; }
    .status { text-align: right; font-size: 14px; color: var(--muted); }
    .status strong { color: var(--text); }
    .banner {
      display: none; margin-bottom: 18px; padding: 18px 20px; border-radius: 18px;
      border: 2px solid rgba(33,201,122,0.55);
      background: linear-gradient(90deg, rgba(33,201,122,0.18), rgba(33,201,122,0.06));
    }
    .banner.active { display: block; }
    .banner .big { font-size: 34px; font-weight: 900; color: #dcffe9; }
    .banner .small { margin-top: 6px; color: #b5f5ce; font-size: 16px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
    .card {
      border: 1px solid var(--line); border-radius: 20px; padding: 20px;
      background: linear-gradient(180deg, rgba(28,39,51,0.98), rgba(17,24,31,0.96));
      min-height: 340px;
    }
    .card.complete {
      border-color: rgba(33,201,122,0.65);
      box-shadow: 0 0 0 2px rgba(33,201,122,0.12) inset;
    }
    .card-head { display: flex; justify-content: space-between; align-items: center; }
    .pot-name { font-size: 28px; font-weight: 800; }
    .pill {
      padding: 8px 14px; border-radius: 999px; font-weight: 800; font-size: 14px;
      border: 1px solid var(--line); background: #213140; color: #dce7f1;
    }
    .pill.complete { background: rgba(33,201,122,0.16); color: #cffff0; border-color: rgba(33,201,122,0.50); }
    .kv { margin-top: 18px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .item {
      background: rgba(10,15,22,0.32); border: 1px solid rgba(148,166,184,0.14);
      border-radius: 14px; padding: 14px 15px;
    }
    .k { font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: 0.7px; }
    .v { margin-top: 6px; font-size: 22px; font-weight: 800; }
    .v.small { font-size: 18px; font-weight: 700; }
    .progress-wrap { margin-top: 18px; }
    .progress-label { color: var(--muted); font-size: 13px; margin-bottom: 8px; }
    .bar { width: 100%; height: 18px; border-radius: 999px; background: #0e151c; border: 1px solid var(--line); overflow: hidden; }
    .bar > div { height: 100%; background: linear-gradient(90deg, var(--accent), var(--hot)); width: 0%; }
    .bottom { margin-top: 18px; display: grid; grid-template-columns: 1.15fr 0.85fr; gap: 18px; }
    .log-card, .done-card {
      border: 1px solid var(--line); border-radius: 20px; padding: 20px;
      background: linear-gradient(180deg, rgba(18,24,31,0.95), rgba(12,17,23,0.96));
    }
    .section-title { font-size: 20px; font-weight: 800; margin-bottom: 14px; }
    .log-list { display: grid; gap: 8px; max-height: 360px; overflow: auto; }
    .log {
      border-radius: 12px; padding: 10px 12px; background: rgba(255,255,255,0.03);
      border: 1px solid rgba(148,166,184,0.08); font-size: 14px;
    }
    .log .ts { color: var(--muted); margin-right: 10px; }
    .empty { color: var(--muted); }
    @media (max-width: 980px) {
      .grid, .bottom { grid-template-columns: 1fr; }
      .head { display: block; }
      .status { margin-top: 10px; text-align: left; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <div class="head">
      <div>
        <div class="title">Frying Dashboard</div>
        <div class="sub">HR/Status 기반 상태 화면. 배출 신호 수신 시 완료를 강조 표시합니다.</div>
      </div>
      <div class="status" id="topStatus">연결 대기중...</div>
    </div>
    <div class="banner" id="banner">
      <div class="big">AI COMPLETE</div>
      <div class="small" id="bannerText">최근 완료 이벤트 없음</div>
    </div>
    <div style="display:flex; gap:10px; margin-bottom:18px; flex-wrap:wrap;">
      <button onclick="triggerComplete('left')" style="padding:12px 16px;border-radius:12px;border:1px solid #2a3a4b;background:#1f8f62;color:#fff;font-weight:800;cursor:pointer;">왼쪽 완료 테스트</button>
      <button onclick="triggerComplete('right')" style="padding:12px 16px;border-radius:12px;border:1px solid #2a3a4b;background:#1f8f62;color:#fff;font-weight:800;cursor:pointer;">오른쪽 완료 테스트</button>
    </div>
    <div class="grid" id="potGrid"></div>
    <div class="bottom">
      <div class="log-card">
        <div class="section-title">Recent Events</div>
        <div class="log-list" id="logs"></div>
      </div>
      <div class="done-card">
        <div class="section-title">Last Complete</div>
        <div id="lastComplete" class="empty">최근 완료 이벤트 없음</div>
      </div>
    </div>
  </div>
  <script>
    function esc(value) {
      if (value === null || value === undefined) return "-";
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;");
    }

    function progressHtml(runSec, targetSec) {
      if (!targetSec || targetSec <= 0) return '<div class="progress-label">진행률 계산 불가</div><div class="bar"><div style="width:0%"></div></div>';
      const pct = Math.max(0, Math.min(100, (runSec / targetSec) * 100));
      return '<div class="progress-label">진행률 ' + pct.toFixed(0) + '%</div><div class="bar"><div style="width:' + pct.toFixed(1) + '%"></div></div>';
    }

    function render(data) {
      const top = document.getElementById('topStatus');
      top.innerHTML =
        'MQTT <strong>' + (data.mqtt_connected ? 'CONNECTED' : 'DISCONNECTED') + '</strong><br>' +
        '서버시각 <strong>' + esc(data.server_time) + '</strong><br>' +
        '최근 HR/Status <strong>' + esc(data.last_hr_status_at || '-') + '</strong>';

      const banner = document.getElementById('banner');
      const bannerText = document.getElementById('bannerText');
      const activeCompletePot = (data.pots || []).find(p => p.complete_active);
      if (activeCompletePot) {
        banner.classList.add('active');
        bannerText.innerHTML =
          esc(activeCompletePot.label) + '솥 / 레시피 ' + esc(activeCompletePot.now_recipe) +
          ' / 완료 표시 / RunningTime ' + esc(activeCompletePot.running_time);
      } else {
        banner.classList.remove('active');
      }

      const grid = document.getElementById('potGrid');
      grid.innerHTML = (data.pots || []).map(p => {
        const completeClass = p.complete_active ? 'complete' : '';
        const pillClass = p.complete_active ? 'pill complete' : 'pill';
        const pillText = p.complete_active ? 'COMPLETE' : esc(p.process_type);
        return `
          <div class="card ${completeClass}">
            <div class="card-head">
              <div class="pot-name">${esc(p.label)}솥</div>
              <div class="${pillClass}">${pillText}</div>
            </div>
            <div class="kv">
              <div class="item"><div class="k">Recipe</div><div class="v small">${esc(p.now_recipe)}</div></div>
              <div class="item"><div class="k">Oil Temp</div><div class="v">${esc(p.oil_temp ?? '-')}°C</div></div>
              <div class="item"><div class="k">RunningTime</div><div class="v small">${esc(p.running_time)}</div></div>
              <div class="item"><div class="k">TargetTime</div><div class="v small">${esc(p.target_time)}</div></div>
              <div class="item"><div class="k">Robot Status</div><div class="v small">${esc(p.rb_status)}</div></div>
              <div class="item"><div class="k">Mode</div><div class="v small">${esc(p.mode)}</div></div>
            </div>
            <div class="progress-wrap">${progressHtml(p.running_sec, p.target_sec)}</div>
          </div>`;
      }).join('');

      const logs = document.getElementById('logs');
      const logItems = data.logs || [];
      logs.innerHTML = logItems.length ? logItems.slice().reverse().map(entry =>
        `<div class="log"><span class="ts">${esc(entry.ts)}</span>${esc(entry.message)}</div>`
      ).join('') : '<div class="empty">로그 없음</div>';

      const lastComplete = document.getElementById('lastComplete');
      if (data.last_complete) {
        const e = data.last_complete;
        lastComplete.innerHTML =
          '<div class="log">' +
          '<div><strong>' + esc(e.label) + '솥</strong></div>' +
          '<div style="margin-top:8px;">시각: ' + esc(e.ts) + '</div>' +
          '<div>레시피: ' + esc(e.recipe) + '</div>' +
          '<div>RunningTime: ' + esc(e.running_time) + '</div>' +
          '<div>TargetTime: ' + esc(e.target_time) + '</div>' +
          '<div>Oil Temp: ' + esc(e.oil_temp ?? '-') + '°C</div>' +
          '<div style="margin-top:8px;color:#b5f5ce;">' + esc(e.reason || '완료 표시') + '</div>' +
          '</div>';
      } else {
        lastComplete.innerHTML = '<div class="empty">최근 완료 이벤트 없음</div>';
      }
    }

    async function triggerComplete(side) {
      try {
        await fetch('/api/trigger_complete?side=' + encodeURIComponent(side), { method: 'POST' });
        await tick();
      } catch (err) {
        console.error(err);
      }
    }

    async function tick() {
      try {
        const res = await fetch('/api/state?_=' + Date.now());
        const data = await res.json();
        render(data);
      } catch (err) {
        console.error(err);
      }
    }

    tick();
    setInterval(tick, 1000);
  </script>
</body>
</html>
"""


class DemoRequestHandler(BaseHTTPRequestHandler):
    state_ref = None

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, body, status=200):
        body_bytes = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body_bytes)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(HTML)
            return
        if parsed.path == "/api/state":
            self._send_json(self.state_ref.snapshot())
            return
        self._send_json({"error": "not found"}, status=404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/trigger_complete":
            qs = {}
            if parsed.query:
                for token in parsed.query.split("&"):
                    if "=" in token:
                        k, v = token.split("=", 1)
                        qs[k] = v
            side = qs.get("side", "left")
            if side not in ("left", "right"):
                self._send_json({"error": "invalid side"}, status=400)
                return
            event = self.state_ref.trigger_complete(side, "수동 버튼 테스트")
            self._send_json({"ok": True, "event": event})
            return
        self._send_json({"error": "not found"}, status=404)

    def log_message(self, fmt, *args):
        return


class DemoWebServer:
    def __init__(self, state, host, port):
        self.state = state
        self.host = host
        self.port = port
        DemoRequestHandler.state_ref = state
        self.httpd = ThreadingHTTPServer((host, port), DemoRequestHandler)

    def serve_forever(self):
        print(f"[DEMO] web server started: http://{self.host}:{self.port}")
        self.httpd.serve_forever()


class FryingDemoApp:
    def __init__(self, host, port):
        self.config = load_config()
        self.state = DemoState()
        self.host = host
        self.port = port
        self.topic_robot_status = self.config.get("mqtt_topic_robot_status", "HR/Status")
        self.mqtt_client = mqtt.Client(
            client_id=f"frying_demo_{int(time.time())}",
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
        )
        self.mqtt_client.on_connect = self.on_connect
        self.mqtt_client.on_disconnect = self.on_disconnect
        self.mqtt_client.on_message = self.on_message

    def on_connect(self, client, userdata, flags, rc):
        ok = (rc == 0)
        self.state.set_mqtt(ok)
        if ok:
            client.subscribe(self.topic_robot_status, qos=int(self.config.get("mqtt_qos", 1)))
            self.state.log(f"MQTT connected / subscribed: {self.topic_robot_status}")
            print(f"[DEMO] MQTT connected -> subscribe {self.topic_robot_status}")
        else:
            self.state.log(f"MQTT connect failed: rc={rc}")
            print(f"[DEMO] MQTT connect failed: rc={rc}")

    def on_disconnect(self, client, userdata, rc):
        self.state.set_mqtt(False)
        self.state.log(f"MQTT disconnected: rc={rc}")
        print(f"[DEMO] MQTT disconnected: rc={rc}")

    def on_message(self, client, userdata, msg):
        if msg.topic != self.topic_robot_status:
            return
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except Exception as exc:
            self.state.log(f"HR/Status parse error: {exc}")
            print(f"[DEMO] HR/Status parse error: {exc}")
            return

        complete_events = self.state.update_from_hr_status(payload)
        for event in complete_events:
            print(
                "[COMPLETE] "
                f"{event['label']}솥 / recipe={event['recipe']} / "
                f"running={event['running_time']} / target={event['target_time']}"
            )

    def run(self):
        broker = self.config.get("mqtt_broker", "localhost")
        port = int(self.config.get("mqtt_port", 1883))

        web = DemoWebServer(self.state, self.host, self.port)
        web_thread = threading.Thread(target=web.serve_forever, daemon=True)
        web_thread.start()

        self.state.log(f"Demo web ready: http://{self.host}:{self.port}")
        self.state.log(f"MQTT target: {broker}:{port} / topic={self.topic_robot_status}")

        print(f"[DEMO] MQTT connect start: {broker}:{port}")
        self.mqtt_client.connect(broker, port, 60)
        self.mqtt_client.loop_start()

        try:
            while True:
                time.sleep(1.0)
        except KeyboardInterrupt:
            print("\n[DEMO] shutdown requested")
        finally:
            try:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()
            except Exception:
                pass


def parse_args():
    parser = argparse.ArgumentParser(description="Headless frying demo web")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8010)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    FryingDemoApp(args.host, args.port).run()
