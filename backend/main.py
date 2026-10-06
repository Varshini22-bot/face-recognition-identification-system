"""
Face Recognition API — FastAPI backend
Endpoints:
  REST  : /health, /identities, /enroll, /attendance, /inference/*
  WS    : /ws/video  (real-time face recognition)
"""
import asyncio
import base64
import json
import logging
import os
from datetime import datetime
from typing import List, Optional

import cv2
import numpy as np
from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
from pathlib import Path

# Ensure backend directory is in sys.path regardless of execution directory
_backend_dir = str(Path(__file__).resolve().parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from database import Database
from face_detector import FaceDetector
from face_recognizer import FaceRecognizer
from feature_matcher import FeatureMatcher

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Face Recognition API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------

DB_DIR = os.environ.get("FACE_DB_DIR", "data/face_db")
SQL_PATH = os.environ.get("SQL_DB", "data/attendance.db")
MODEL_PACK = os.environ.get("MODEL_PACK", "buffalo_sc")

os.makedirs("data", exist_ok=True)

logger.info("Loading models (model_pack=%s) ...", MODEL_PACK)
detector = FaceDetector(model_pack=MODEL_PACK)
recognizer = FaceRecognizer(model_pack=MODEL_PACK)
matcher = FeatureMatcher(threshold=float(os.environ.get("SIM_THRESHOLD", "0.4")))
db = Database(SQL_PATH)

matcher.load(DB_DIR)
logger.info("Models ready. DB vectors: %d", matcher.index.ntotal)


class _State:
    inference_active: bool = False


state = _State()

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class IdentityInfo(BaseModel):
    name: str
    sample_count: int


class AttendanceRecord(BaseModel):
    id: int
    name: str
    similarity: float
    timestamp: str
    photo: Optional[str] = None


class EnrollResponse(BaseModel):
    success: bool
    message: str
    name: str


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/health")
def health():
    return {
        "status": "ok",
        "inference": state.inference_active,
        "vectors_in_db": matcher.index.ntotal,
    }


@app.get("/identities", response_model=List[IdentityInfo])
def list_identities():
    return [
        IdentityInfo(name=n, sample_count=len(matcher.metadata.get(n, [])))
        for n in matcher.list_identities()
    ]


@app.post("/enroll", response_model=EnrollResponse)
async def enroll(name: str = Form(...), file: UploadFile = File(...)):
    raw = await file.read()
    arr = np.frombuffer(raw, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Cannot decode image.")

    faces = detector.detect(img)
    if not faces:
        return EnrollResponse(success=False, message="No face detected in image.", name=name)

    face = faces[0]  # use highest-confidence face
    if face["kps"] is None:
        return EnrollResponse(success=False, message="No landmarks detected.", name=name)

    emb = recognizer.get_embedding(img, face["kps"])
    matcher.add(name, emb)
    matcher.save(DB_DIR)
    logger.info("Enrolled '%s' (total vectors: %d)", name, matcher.index.ntotal)
    return EnrollResponse(success=True, message=f"Enrolled '{name}' successfully.", name=name)


@app.delete("/identities/{name}")
def delete_identity(name: str):
    if not matcher.remove(name):
        raise HTTPException(status_code=404, detail=f"Identity '{name}' not found.")
    matcher.save(DB_DIR)
    return {"success": True, "deleted": name}


@app.get("/attendance", response_model=List[AttendanceRecord])
def get_attendance(limit: int = 100, date: Optional[str] = None, name: Optional[str] = None):
    return db.get_attendance(limit=limit, date_filter=date, name_filter=name)


@app.get("/attendance/stats")
def attendance_stats():
    return db.get_stats()


@app.post("/inference/start")
def inference_start():
    state.inference_active = True
    return {"status": "started"}


@app.post("/inference/stop")
def inference_stop():
    state.inference_active = False
    return {"status": "stopped"}


# ---------------------------------------------------------------------------
# WebSocket — real-time video stream
# ---------------------------------------------------------------------------

# Throttle: save to DB at most once per person per N seconds
_last_saved: dict = {}
_SAVE_COOLDOWN = 5  # seconds


@app.websocket("/ws/video")
async def video_ws(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if msg.get("type") != "frame":
                continue

            # Decode JPEG frame
            img_bytes = base64.b64decode(msg["data"])
            arr = np.frombuffer(img_bytes, np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            face_results = []

            if state.inference_active:
                try:
                    faces = detector.detect(frame)
                    now = datetime.now().timestamp()

                    for face in faces:
                        name = "unknown"
                        similarity = 0.0
                        bbox = face["bbox"]
                        kps = face["kps"]

                        if kps is not None and matcher.index.ntotal > 0:
                            emb = recognizer.get_embedding(frame, kps)
                            name, similarity = matcher.search(emb)
                            name = name or "unknown"

                            # Throttled attendance logging
                            if name != "unknown":
                                last = _last_saved.get(name, 0)
                                if now - last >= _SAVE_COOLDOWN:
                                    x1, y1, x2, y2 = bbox
                                    crop = frame[max(0, y1):y2, max(0, x1):x2]
                                    photo_b64 = None
                                    if crop.size > 0:
                                        _, buf = cv2.imencode(".jpg", crop)
                                        photo_b64 = base64.b64encode(buf).decode()
                                    db.add_attendance(name, similarity, photo_b64)
                                    _last_saved[name] = now

                        face_results.append(
                            {
                                "bbox": bbox,
                                "name": name,
                                "similarity": round(similarity, 3),
                                "det_score": round(face["score"], 3),
                            }
                        )
                except Exception as exc:
                    logger.error("Inference error: %s", exc, exc_info=True)

            await websocket.send_json(
                {
                    "type": "result",
                    "faces": face_results,
                    "inference_active": state.inference_active,
                }
            )

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.error("WebSocket error: %s", exc, exc_info=True)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
