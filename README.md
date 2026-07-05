# YOLOv8 Object Detection — Video Analyser

A full-stack object detection web app built with Flask and vanilla HTML/CSS/JS, powered by Ultralytics YOLOv8.

## Features

- **Image detection** — upload an image, get annotated result with bounding boxes and confidence scores
- **Video detection** — upload a video, get per-class detection summary across sampled frames
- **Model selection** — switch between YOLOv8n / s / m / l / x live from the UI
- **Configurable thresholds** — confidence, IoU, and frame skip sliders
- **File validation** — checks both file extension and magic bytes before processing
- **Memory efficient** — video streamed to disk in 1MB chunks, never fully loaded into RAM

## Architecture

```
Video Analyser/
├── app.py              # Flask entry point — creates app, registers blueprint
├── routes.py           # HTTP route handlers for /detect/image and /detect/video
├── inference.py        # YOLO model loading, caching, and image encoding
├── validators.py       # File extension and magic byte validation
├── test_validators.py  # pytest unit tests for validation functions
├── requirements.txt    # Python dependencies
├── README.md           # This file
├── .gitignore          # Excludes .pt weights, __pycache__, .pytest_cache from git
├── templates/
│   └── index.html      # Single-page UI structure
└── static/
    ├── style.css        # All styling — no framework, plain CSS
    └── script.js        # All interactivity — vanilla JS, no framework
```

**Why split into multiple files?**
`app.py` is kept as a thin entry point — it only creates the Flask app and registers routes. `routes.py` owns the API layer, `inference.py` owns the ML layer, and `validators.py` owns the security layer. Each can be changed independently — swapping YOLOv8 for a different model only touches `inference.py`, adding a new file type only touches `validators.py`.

**Why Flask + vanilla JS over Streamlit?**
Streamlit abstracts away HTTP, API design, and frontend fundamentals. Flask with vanilla JS demonstrates full-stack understanding — the browser talks to the backend via explicit `fetch()` calls, the backend returns structured JSON, and the frontend renders it. Every layer is visible and intentional.

**Why base64 JSON for image transfer?**
Keeps the API to a single endpoint returning one JSON object — no separate file-serving routes needed for the annotated image. Acceptable for images; for production, signed URLs to object storage would be better.

## Setup

**Requirements:** Python 3.10+

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
py app.py
```

Open `http://127.0.0.1:5000` in your browser.

On first use, YOLOv8 will automatically download the selected model weights (~6MB for n, ~130MB for x). This is a one-time download per model.

## Usage

### Image Mode
1. Select model and thresholds in the sidebar
2. Upload an image (JPG, PNG, BMP, WEBP) via browse or drag-and-drop
3. Click **Run Detection**
4. View annotated result and detected objects table

### Video Mode
1. Select model, thresholds, and frame skip in the sidebar
2. Upload a video (MP4, AVI, MOV, MKV)
3. Click **Run Detection**
4. View per-class detection summary table

**Frame skip:** processes every Nth frame. At 30fps, skip=5 means one sample per 0.17 seconds — sufficient for static/slow-moving scenes. Higher skip = faster processing, lower accuracy.

## Model Comparison

| Model | Parameters | mAP | Speed (CPU) |
|-------|-----------|-----|-------------|
| YOLOv8n | 3.2M | 37.3% | ~45ms/frame |
| YOLOv8s | 11.2M | 44.9% | ~90ms/frame |
| YOLOv8m | 25.9M | 50.2% | ~230ms/frame |
| YOLOv8l | 43.7M | 52.9% | ~430ms/frame |
| YOLOv8x | 68.2M | 53.9% | ~640ms/frame |

## Known Limitations

- Video processing is synchronous — long videos will block the request thread. The correct fix is a background job queue (Celery or RQ) that processes the video asynchronously and polls for results, or SSE streaming to keep the connection alive with progress updates.
- Only COCO 80-class objects are detectable (no mirrors, cabinets, etc.)
- No GPU acceleration by default — requires CUDA setup for significant speedup
- No annotated video output — video mode returns a stats table only, not a downloadable processed video. Adding this would require `cv2.VideoWriter` to write annotated frames and a separate download endpoint.
- `model_cache` is a module-level dict — safe under Flask's single-process dev server. Under a multi-worker production server (Gunicorn with multiple processes), each worker gets its own separate cache, so the same model may be loaded multiple times across workers. A shared cache (Redis) would fix this in production.

## Dependencies

- `flask` — web framework and HTTP server
- `ultralytics` — YOLOv8 model loading and inference
- `opencv-python` — image/video decoding and annotation
- `numpy` — array operations for image data

## Future Work
- Rate limiting via Flask-Limiter once deployed to a public server
- Background job queue (Celery/RQ) for long video processing
- Dockerize for one-command deployment