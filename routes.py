from flask import Blueprint, render_template, request, jsonify
import cv2
import numpy as np
import tempfile
import os

from extensions import limiter
from inference import get_model, encode_image_to_base64
from validators import (
    has_valid_extension, has_valid_magic_bytes,
    ALLOWED_IMAGE_EXTENSIONS, ALLOWED_VIDEO_EXTENSIONS,
    IMAGE_SIGNATURES, VIDEO_SIGNATURES,
)

bp = Blueprint("main", __name__)


def parse_common_params() -> dict:
    # Shared params used by both routes — change defaults here only
    return {
        "conf":  float(request.form.get("conf", 0.55)),
        "iou":   float(request.form.get("iou", 0.45)),
        "model": get_model(request.form.get("model", "yolov8n.pt")),
    }


@bp.route("/")
def index():
    return render_template("index.html")


@bp.route("/detect/image", methods=["POST"])
@limiter.limit("5 per minute")
def detect_image():
    try:
        file       = request.files.get("image")
        params = parse_common_params()
        conf   = params["conf"]
        iou    = params["iou"]
        model  = params["model"]

        if not file:
            return jsonify({"error": "No image uploaded"}), 400

        if not has_valid_extension(file.filename, ALLOWED_IMAGE_EXTENSIONS):
            return jsonify({"error": "Invalid file extension. Allowed: jpg, jpeg, png, bmp, webp"}), 400

        raw_bytes = file.read()
        if not has_valid_magic_bytes(raw_bytes, IMAGE_SIGNATURES):
            return jsonify({"error": "File content does not match a valid image format."}), 400

        file_bytes = np.frombuffer(raw_bytes, np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img is None:
            return jsonify({"error": "Could not decode image."}), 400

        print(f"Image detection: shape={img.shape}, conf={conf}, iou={iou}")

        results   = model.predict(img, conf=conf, iou=iou, verbose=False)
        result    = results[0]
        annotated = result.plot()

        detections = [
            {"class": model.names[int(b.cls[0])], "confidence": round(float(b.conf[0]), 2)}
            for b in result.boxes
        ]
        detections.sort(key=lambda x: x["confidence"], reverse=True)
        print(f"Done — {len(detections)} objects found.")

        return jsonify({
            "annotated_image": encode_image_to_base64(annotated),
            "detections": detections,
        })

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@bp.route("/detect/video", methods=["POST"])
@limiter.limit("2 per minute")
def detect_video():
    try:
        file       = request.files.get("video")
        params = parse_common_params()
        conf   = params["conf"]
        iou    = params["iou"]
        model  = params["model"]
        frame_skip = int(request.form.get("frame_skip", 5))

        if not file:
            return jsonify({"error": "No video uploaded"}), 400

        if not has_valid_extension(file.filename, ALLOWED_VIDEO_EXTENSIONS):
            return jsonify({"error": "Invalid file extension. Allowed: mp4, avi, mov, mkv"}), 400

        # Read only first 16 bytes for magic byte check — avoids loading full video into RAM
        header = file.read(16)
        if not has_valid_magic_bytes(header, VIDEO_SIGNATURES):
            return jsonify({"error": "File content does not match a valid video format."}), 400

        # Stream video to disk 1MB at a time instead of buffering whole file in memory
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        try:
            tfile.write(header)
            file.seek(16)
            while chunk := file.read(1024 * 1024):
                tfile.write(chunk)
        finally:
            tfile.close() 

        cap         = cv2.VideoCapture(tfile.name)
        class_stats = {}
        frame_idx   = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            frame_idx += 1
            if frame_idx % frame_skip != 0:
                continue   

            results = model.predict(frame, conf=conf, iou=iou, verbose=False)
            result  = results[0]

            per_frame = {}
            for box in result.boxes:
                cls_name = model.names[int(box.cls[0])]
                box_conf = float(box.conf[0])
                per_frame[cls_name] = per_frame.get(cls_name, 0) + 1
                if cls_name not in class_stats:
                    class_stats[cls_name] = {"max_in_frame": 0, "max_conf": 0.0, "frames": 0}
                class_stats[cls_name]["max_conf"] = max(class_stats[cls_name]["max_conf"], box_conf)

            for cls_name, count in per_frame.items():
                class_stats[cls_name]["frames"]      += 1
                class_stats[cls_name]["max_in_frame"] = max(class_stats[cls_name]["max_in_frame"], count)

        cap.release()
        try:
            os.unlink(tfile.name)
        except PermissionError:
            pass    # Windows may briefly hold the file lock — safe to skip cleanup

        summary = [
            {"class": k, "max_in_frame": v["max_in_frame"], "max_conf": round(v["max_conf"], 2)}
            for k, v in sorted(class_stats.items(), key=lambda x: x[1]["frames"], reverse=True)
        ]

        print(f"Video done — {len(summary)} classes.")
        return jsonify({"summary": summary})

    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500