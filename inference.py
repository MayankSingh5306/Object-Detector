import cv2
import numpy as np
import base64
from ultralytics import YOLO

model_cache = {}


def get_model(model_name: str) -> YOLO:
    """Load and cache models so each is only downloaded/loaded once.
    Subsequent calls with the same model name return the cached instance instantly.
    """
    allowed = {"yolov8n.pt", "yolov8s.pt", "yolov8m.pt", "yolov8l.pt", "yolov8x.pt"}
    if model_name not in allowed:
        model_name = "yolov8n.pt"   # fallback to safe default
    if model_name not in model_cache:
        print(f"Loading model: {model_name}")
        model_cache[model_name] = YOLO(model_name)
    return model_cache[model_name]


def encode_image_to_base64(img_bgr: np.ndarray) -> str:
    """Convert a BGR numpy image to a base64 PNG string for JSON transfer."""
    _, buffer = cv2.imencode(".png", img_bgr)
    return base64.b64encode(buffer).decode("utf-8")