"""
BlindBuddy — Vision Module (YOLOv8 Object Detection)
Processes camera frames and returns structured scene data.
"""
import io
import math
import base64
from typing import Optional
from PIL import Image
from config import YOLO_MODEL, YOLO_CONFIDENCE

# YOLOv8 model loaded globally once at startup
_model = None

# Mapping from YOLO COCO class names to friendlier names (and distance estimation hints)
HAZARD_CLASSES = {
    "person": "pedestrian",
    "bicycle": "bicycle",
    "car": "car",
    "motorcycle": "motorcycle",
    "bus": "bus",
    "truck": "truck",
    "traffic light": "traffic light",
    "stop sign": "stop sign",
    "bench": "bench obstacle",
    "dog": "dog",
    "cat": "cat",
    "chair": "chair obstacle",
    "dining table": "table obstacle",
    "potted plant": "plant obstacle",
    "fire hydrant": "fire hydrant",
    "parking meter": "pole obstacle",
    "umbrella": "umbrella",
    "backpack": "backpack on ground",
    "suitcase": "suitcase obstacle",
}


def load_model():
    """Load YOLOv8 model. Called once on server startup."""
    global _model
    try:
        from ultralytics import YOLO
        _model = YOLO(YOLO_MODEL)
        print(f"✅ Loaded YOLOv8 model: {YOLO_MODEL}")
    except Exception as e:
        print(f"⚠️  YOLOv8 load failed: {e}. Vision module will return empty results.")
        _model = None


def detect_objects(image_bytes: bytes) -> list[dict]:
    """
    Run YOLOv8 on the given image bytes.
    Returns a list of detected objects with direction and estimated distance.
    """
    if _model is None:
        return []

    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_width, img_height = img.size

        results = _model(img, conf=YOLO_CONFIDENCE, verbose=False)
        detections = []

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            cls_name = _model.names[cls_id].lower()
            conf = float(box.conf[0])

            # Bounding box (x1, y1, x2, y2) in pixels
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            box_width = x2 - x1
            box_height = y2 - y1
            cx = (x1 + x2) / 2

            # Direction: left / center / right based on center x relative to image width
            if cx < img_width * 0.35:
                direction = "left"
            elif cx > img_width * 0.65:
                direction = "right"
            else:
                direction = "ahead"

            # Rough distance estimate: larger boxes = closer objects
            # Assumes a 'person' filling ~50% of frame height ≈ 1.5m
            box_fraction = box_height / img_height
            est_distance_m = max(0.5, round(1.5 / max(box_fraction, 0.1), 1))

            friendly_name = HAZARD_CLASSES.get(cls_name, cls_name)

            detections.append({
                "object": friendly_name,
                "raw_class": cls_name,
                "direction": direction,
                "distance": f"{est_distance_m} meters",
                "distance_m": est_distance_m,
                "confidence": round(conf, 2),
                "bbox": {"x1": round(x1), "y1": round(y1), "x2": round(x2), "y2": round(y2)},
            })

        # Sort by distance ascending (closest first)
        detections.sort(key=lambda d: d["distance_m"])
        return detections

    except Exception as e:
        print(f"Vision detection error: {e}")
        return []


def detect_objects_from_base64(b64_image: str) -> list[dict]:
    """Convenience wrapper that accepts base64-encoded image strings."""
    image_bytes = base64.b64decode(b64_image)
    return detect_objects(image_bytes)
