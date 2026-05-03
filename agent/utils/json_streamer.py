import sys
import json


def send(msg: dict):
    """Send a JSON message to Electron via stdout."""
    print(json.dumps(msg, ensure_ascii=False), flush=True)


def log(message: str, level: str = "info", scene: int = None):
    payload = {"type": "log", "level": level, "message": message}
    if scene is not None:
        payload["scene"] = scene
    send(payload)


def progress(scene: int, total: int, status: str, percent: int = None):
    payload = {"type": "progress", "scene": scene, "total": total, "status": status}
    if percent is not None:
        payload["percent"] = percent
    send(payload)


def scene_done(scene: int, code: str):
    send({"type": "scene_done", "scene": scene, "code": code})


def awaiting_approval(scene: int, preview_url: str = "http://localhost:3000"):
    send({"type": "awaiting_approval", "scene": scene, "preview_url": preview_url})


def done(output_path: str, duration_ms: int = 0):
    send({"type": "done", "output_path": output_path, "duration_ms": duration_ms})


def error(message: str, scene: int = None, retryable: bool = True):
    payload = {"type": "error", "message": message, "retryable": retryable}
    if scene is not None:
        payload["scene"] = scene
    send(payload)
