"""
Face Recognition Desktop App — PyQt6 GUI

Architecture:
  - CaptureThread: reads camera frames, sends them to the API via WebSocket,
    emits (frame, results) for display.
  - MainWindow:    renders frames with overlaid bounding boxes/names,
                   provides controls for camera, inference, and enroll.
"""
import base64
import json
import logging
import sys
import time
import threading
from typing import List, Dict

import cv2
import numpy as np
import requests
import websocket  # websocket-client

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

API_BASE = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/video"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Background thread: capture + WebSocket
# ---------------------------------------------------------------------------


class CaptureThread(QThread):
    """
    Reads camera frames and forwards them to the backend WS for inference.
    Emits: frame_ready(np.ndarray, list[dict])
    """

    frame_ready = pyqtSignal(np.ndarray, list)

    SEND_EVERY = 3   # send every N-th frame for inference
    JPEG_QUALITY = 70

    def __init__(self, camera_id: int = 0):
        super().__init__()
        self.camera_id = camera_id
        self._running = False
        self._ws: websocket.WebSocket | None = None
        self._latest_results: List[Dict] = []
        self._lock = threading.Lock()

    def run(self):
        self._running = True
        cap = cv2.VideoCapture(self.camera_id)
        if not cap.isOpened():
            logger.error("Cannot open camera %d", self.camera_id)
            return

        # Try to connect WebSocket
        try:
            self._ws = websocket.WebSocket()
            self._ws.connect(WS_URL, timeout=3)
            logger.info("WebSocket connected")
        except Exception as e:
            logger.warning("WebSocket unavailable: %s", e)
            self._ws = None

        frame_idx = 0
        while self._running:
            ok, frame = cap.read()
            if not ok:
                break

            results = []

            if self._ws and frame_idx % self.SEND_EVERY == 0:
                try:
                    _, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, self.JPEG_QUALITY])
                    b64 = base64.b64encode(buf).decode()
                    self._ws.send(json.dumps({"type": "frame", "data": b64}))
                    resp = json.loads(self._ws.recv())
                    if resp.get("type") == "result":
                        with self._lock:
                            self._latest_results = resp.get("faces", [])
                except Exception as e:
                    logger.warning("WS error: %s", e)
                    self._reconnect()

            with self._lock:
                results = list(self._latest_results)

            self.frame_ready.emit(frame.copy(), results)
            frame_idx += 1

        cap.release()
        self._close_ws()

    def stop(self):
        self._running = False

    def _reconnect(self):
        self._close_ws()
        try:
            self._ws = websocket.WebSocket()
            self._ws.connect(WS_URL, timeout=3)
        except Exception:
            self._ws = None

    def _close_ws(self):
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
            self._ws = None


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Recognition System — AI VIET NAM")
        self.setMinimumSize(1060, 680)

        self._capture: CaptureThread | None = None
        self._inference_on = False
        self._fps_count = 0
        self._fps_ts = time.time()

        self._build_ui()
        self._apply_dark_style()

        self._stats_timer = QTimer(self)
        self._stats_timer.timeout.connect(self._refresh_stats)
        self._stats_timer.start(5_000)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # ── Left: video ──────────────────────────────────────────────
        left = QFrame()
        left.setObjectName("panel")
        lv = QVBoxLayout(left)
        lv.setContentsMargins(8, 8, 8, 8)

        top = QHBoxLayout()
        self.fps_lbl = QLabel("FPS: --")
        self.fps_lbl.setFont(QFont("Consolas", 11))
        self.inf_badge = QLabel("● Inference: OFF")
        self.inf_badge.setFont(QFont("Consolas", 10))
        self.inf_badge.setStyleSheet("color:#ef5350;")
        top.addWidget(self.fps_lbl)
        top.addStretch()
        top.addWidget(self.inf_badge)
        lv.addLayout(top)

        self.video_lbl = QLabel("Camera not started")
        self.video_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_lbl.setMinimumSize(640, 480)
        self.video_lbl.setStyleSheet("background:#0d0d1a; border-radius:6px;")
        lv.addWidget(self.video_lbl)

        layout.addWidget(left, stretch=3)

        # ── Right: controls ──────────────────────────────────────────
        right = QFrame()
        right.setObjectName("panel")
        right.setFixedWidth(260)
        rv = QVBoxLayout(right)
        rv.setContentsMargins(12, 12, 12, 12)
        rv.setSpacing(10)

        title = QLabel("Face Recognition")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rv.addWidget(title)

        sub = QLabel("AI VIET NAM — AIO2025")
        sub.setFont(QFont("Arial", 9))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rv.addWidget(sub)
        rv.addSpacing(6)

        rv.addWidget(self._sep("Camera"))
        self.cam_btn = QPushButton("▶  Start Camera")
        self.cam_btn.clicked.connect(self._toggle_camera)
        rv.addWidget(self.cam_btn)

        self.inf_btn = QPushButton("⚡  Start Inference")
        self.inf_btn.clicked.connect(self._toggle_inference)
        self.inf_btn.setEnabled(False)
        rv.addWidget(self.inf_btn)
        rv.addSpacing(6)

        rv.addWidget(self._sep("Enroll"))
        self.enroll_cam_btn = QPushButton("📷  Enroll from Camera")
        self.enroll_cam_btn.clicked.connect(self._enroll_camera)
        self.enroll_cam_btn.setEnabled(False)
        rv.addWidget(self.enroll_cam_btn)

        self.enroll_file_btn = QPushButton("🖼  Enroll from File")
        self.enroll_file_btn.clicked.connect(self._enroll_file)
        rv.addWidget(self.enroll_file_btn)
        rv.addSpacing(6)

        rv.addWidget(self._sep("Stats"))
        self.stats_lbl = QLabel("–")
        self.stats_lbl.setFont(QFont("Consolas", 10))
        rv.addWidget(self.stats_lbl)

        rv.addStretch()

        self.status_lbl = QLabel("Ready")
        self.status_lbl.setFont(QFont("Arial", 9))
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_lbl.setWordWrap(True)
        rv.addWidget(self.status_lbl)

        layout.addWidget(right)

    @staticmethod
    def _sep(text: str) -> QLabel:
        lbl = QLabel(f"── {text} ──")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#888; font-size:10px;")
        return lbl

    def _apply_dark_style(self):
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background:#12122a; color:#e0e0e0; }
            QFrame#panel { background:#1a1a3e; border-radius:8px; }
            QPushButton {
                background:#0f3460; color:#fff; border:none;
                border-radius:6px; padding:8px 14px;
                font-size:13px; font-weight:bold;
            }
            QPushButton:hover   { background:#1565c0; }
            QPushButton:pressed { background:#0d47a1; }
            QPushButton:disabled{ background:#2a2a4a; color:#555; }
            QLabel              { background:transparent; }
            """
        )

    # ------------------------------------------------------------------
    # Camera / inference controls
    # ------------------------------------------------------------------

    def _toggle_camera(self):
        if self._capture is None:
            self._capture = CaptureThread(camera_id=0)
            self._capture.frame_ready.connect(self._on_frame)
            self._capture.start()
            self.cam_btn.setText("■  Stop Camera")
            self.inf_btn.setEnabled(True)
            self.enroll_cam_btn.setEnabled(True)
            self._set_status("Camera running")
        else:
            self._capture.stop()
            self._capture.wait()
            self._capture = None
            self.cam_btn.setText("▶  Start Camera")
            self.inf_btn.setEnabled(False)
            self.enroll_cam_btn.setEnabled(False)
            self.video_lbl.setText("Camera stopped")
            self._set_status("Camera stopped")

    def _toggle_inference(self):
        try:
            if not self._inference_on:
                requests.post(f"{API_BASE}/inference/start", timeout=2)
                self._inference_on = True
                self.inf_btn.setText("⛔  Stop Inference")
                self.inf_badge.setText("● Inference: ON")
                self.inf_badge.setStyleSheet("color:#66bb6a;")
            else:
                requests.post(f"{API_BASE}/inference/stop", timeout=2)
                self._inference_on = False
                self.inf_btn.setText("⚡  Start Inference")
                self.inf_badge.setText("● Inference: OFF")
                self.inf_badge.setStyleSheet("color:#ef5350;")
        except requests.RequestException as e:
            self._set_status(f"API error: {e}")

    # ------------------------------------------------------------------
    # Frame display
    # ------------------------------------------------------------------

    def _on_frame(self, frame: np.ndarray, results: list):
        disp = frame.copy()

        for face in results:
            x1, y1, x2, y2 = face["bbox"]
            name = face.get("name", "unknown")
            sim = face.get("similarity", 0.0)

            color = (0, 200, 0) if name != "unknown" else (0, 60, 200)
            cv2.rectangle(disp, (x1, y1), (x2, y2), color, 2)

            label = f"{name}  {sim:.0%}" if name != "unknown" else "Unknown"
            (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(disp, (x1, y1 - th - 8), (x1 + tw + 6, y1), color, -1)
            cv2.putText(
                disp, label, (x1 + 3, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1,
            )

        h, w = disp.shape[:2]
        rgb = cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)
        qi = QImage(rgb.data, w, h, w * 3, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qi).scaled(
            self.video_lbl.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_lbl.setPixmap(pix)

        # FPS
        self._fps_count += 1
        now = time.time()
        if now - self._fps_ts >= 1.0:
            self.fps_lbl.setText(f"FPS: {self._fps_count / (now - self._fps_ts):.1f}")
            self._fps_count = 0
            self._fps_ts = now

    # ------------------------------------------------------------------
    # Enroll
    # ------------------------------------------------------------------

    def _enroll_camera(self):
        if self._capture is None:
            return
        name, ok = QInputDialog.getText(self, "Enroll", "Enter person name:")
        if not ok or not name.strip():
            return
        cap = cv2.VideoCapture(0)
        ok2, frame = cap.read()
        cap.release()
        if not ok2:
            QMessageBox.warning(self, "Error", "Could not capture frame.")
            return
        self._do_enroll(name.strip(), frame)

    def _enroll_file(self):
        name, ok = QInputDialog.getText(self, "Enroll", "Enter person name:")
        if not ok or not name.strip():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Select face image", "", "Images (*.jpg *.jpeg *.png *.bmp)"
        )
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            QMessageBox.warning(self, "Error", "Cannot read image file.")
            return
        self._do_enroll(name.strip(), img)

    def _do_enroll(self, name: str, img: np.ndarray):
        _, buf = cv2.imencode(".jpg", img)
        try:
            resp = requests.post(
                f"{API_BASE}/enroll",
                files={"file": ("face.jpg", buf.tobytes(), "image/jpeg")},
                data={"name": name},
                timeout=15,
            )
            result = resp.json()
            if result["success"]:
                QMessageBox.information(self, "Enrolled", result["message"])
                self._set_status(f"Enrolled: {name}")
            else:
                QMessageBox.warning(self, "Failed", result["message"])
        except requests.RequestException as e:
            QMessageBox.critical(self, "Error", str(e))

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def _refresh_stats(self):
        try:
            s = requests.get(f"{API_BASE}/attendance/stats", timeout=2).json()
            ids = requests.get(f"{API_BASE}/identities", timeout=2).json()
            self.stats_lbl.setText(
                f"Today:     {s.get('today', 0)}\n"
                f"Unique:    {s.get('unique_today', 0)}\n"
                f"Unknowns:  {s.get('unknown_today', 0)}\n"
                f"Enrolled:  {len(ids)}"
            )
        except Exception:
            pass

    def _set_status(self, msg: str):
        self.status_lbl.setText(msg)

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def closeEvent(self, event):
        if self._capture:
            self._capture.stop()
            self._capture.wait()
        event.accept()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
