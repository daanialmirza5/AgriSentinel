"""Live webcam capture via OpenCV, running in a background thread.

If no camera is available on this machine (headless server, permissions
denied, no webcam hardware), start() reports a clear error and the rest of
the application (image/video upload workflows) remains fully usable.
"""
from __future__ import annotations

import threading
import time
from typing import Optional

import cv2
import numpy as np

from app.services.inference import inference_service

INFERENCE_INTERVAL_S = 0.5


class CameraManager:
    def __init__(self) -> None:
        self._cap: Optional[cv2.VideoCapture] = None
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._lock = threading.Lock()
        self.device_index: Optional[int] = None
        self.field_id: Optional[str] = None
        self.latest_jpeg: Optional[bytes] = None
        self.latest_raw_frame: Optional[np.ndarray] = None
        self.frames_processed = 0
        self.last_detection_count = 0
        self.error: Optional[str] = None

    def list_devices(self, max_probe: int = 4) -> list[int]:
        found = []
        for i in range(max_probe):
            cap = cv2.VideoCapture(i, cv2.CAP_DSHOW if hasattr(cv2, "CAP_DSHOW") else 0)
            if cap is not None and cap.isOpened():
                found.append(i)
            if cap is not None:
                cap.release()
        return found

    @property
    def active(self) -> bool:
        return self._running

    def start(self, device_index: int, field_id: Optional[str] = None) -> dict:
        if self._running:
            return self.status()
        cap = cv2.VideoCapture(device_index)
        if not cap.isOpened():
            self.error = f"Could not open camera device index {device_index}."
            return self.status()
        self._cap = cap
        self.device_index = device_index
        self.field_id = field_id
        self.error = None
        self.frames_processed = 0
        self.last_detection_count = 0
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self.status()

    def stop(self) -> dict:
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2)
        if self._cap is not None:
            self._cap.release()
        self._cap = None
        self.device_index = None
        return self.status()

    def status(self) -> dict:
        return {
            "active": self._running,
            "device_index": self.device_index,
            "available": self.error is None,
            "frames_processed": self.frames_processed,
            "last_detection_count": self.last_detection_count,
            "error": self.error,
        }

    def _loop(self) -> None:
        last_infer = 0.0
        while self._running and self._cap is not None:
            ok, frame = self._cap.read()
            if not ok:
                self.error = "Camera read failed; stopping stream."
                self._running = False
                break
            now = time.time()
            if now - last_infer >= INFERENCE_INTERVAL_S:
                last_infer = now
                try:
                    detections, annotated, _meta = inference_service.infer(frame)
                    self.last_detection_count = len(detections)
                    self.frames_processed += 1
                except Exception as exc:  # keep stream alive even if inference hiccups
                    annotated = frame
                    self.error = f"inference error: {exc}"
            else:
                annotated = frame
            ok2, buf = cv2.imencode(".jpg", annotated, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if ok2:
                with self._lock:
                    self.latest_jpeg = buf.tobytes()
                    self.latest_raw_frame = frame
            time.sleep(0.03)

    def mjpeg_generator(self):
        boundary = b"--frame"
        while self._running:
            with self._lock:
                jpeg = self.latest_jpeg
            if jpeg is not None:
                yield boundary + b"\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            time.sleep(0.05)

    def capture_raw_frame(self) -> Optional[np.ndarray]:
        with self._lock:
            return None if self.latest_raw_frame is None else self.latest_raw_frame.copy()


camera_manager = CameraManager()
