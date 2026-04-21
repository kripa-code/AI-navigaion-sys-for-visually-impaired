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


import cv2
import numpy as np

def detect_objects(image_bytes: bytes) -> list[dict]:
    """
    Run YOLOv8 + OpenCV Door Detection on the given image bytes.
    Returns a list of detected objects.
    """
    if _model is None:
        return []

    try:
        # 1. Decode image for both libraries
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_cv2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_cv2 is None:
            return []
            
        img_height, img_width = img_cv2.shape[:2]

        # 2. YOLOv8 Detection
        # Convert to RGB for PIL/YOLO if needed, but YOLO can take numpy
        results = _model(img_cv2, conf=YOLO_CONFIDENCE, verbose=False)
        detections = []

        for box in results[0].boxes:
            cls_id = int(box.cls[0])
            cls_name = _model.names[cls_id].lower()
            conf = float(box.conf[0])

            x1, y1, x2, y2 = box.xyxy[0].tolist()
            box_height = y2 - y1
            cx = (x1 + x2) / 2

            if cx < img_width * 0.35:
                direction = "left"
            elif cx > img_width * 0.65:
                direction = "right"
            else:
                direction = "ahead"

            box_fraction = box_height / img_height
            est_distance_m = max(0.5, round(1.5 / max(box_fraction, 0.1), 1))

            detections.append({
                "object": HAZARD_CLASSES.get(cls_name, cls_name),
                "raw_class": cls_name,
                "direction": direction,
                "distance": f"{est_distance_m} meters",
                "distance_m": est_distance_m,
                "confidence": round(conf, 2),
                "bbox": {"x": round(x1), "y": round(y1), "w": round(x2 - x1), "h": round(y2 - y1)},
            })

        # 3. Friend's Door Detection Logic
        door_boxes = _detect_doors_logic(img_cv2)
        for (dx, dy, dw, dh) in door_boxes:
            # Simple heuristic for door distance: usually ~2m if it occupies a fair chunk of height
            door_fraction = dh / img_height
            dist_m = max(1.0, round(2.0 / max(door_fraction, 0.2), 1))
            
            dcx = dx + (dw / 2)
            if dcx < img_width * 0.35:
                ddir = "left"
            elif dcx > img_width * 0.65:
                ddir = "right"
            else:
                ddir = "ahead"

            detections.append({
                "object": "door",
                "raw_class": "door",
                "direction": ddir,
                "distance": f"{dist_m} meters",
                "distance_m": dist_m,
                "confidence": 0.8, # Estimated confidence for contour detection
                "bbox": {"x": dx, "y": dy, "w": dw, "h": dh},
            })

        detections.sort(key=lambda d: d["distance_m"])
        return detections

    except Exception as e:
        print(f"Vision detection error: {e}")
        return []

def _detect_doors_logic(image):
    """Friend's logic for detecting doors using OpenCV contours."""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(edges, kernel, iterations=2)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        door_boxes = []
        img_h, img_w = image.shape[:2]

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h
            aspect = h / float(w) if w != 0 else 0
            rel_area = area / float(img_h * img_w)
            if 1.5 < aspect < 4.5 and 0.02 < rel_area < 0.40 and w > 40 and h > 80:
                door_boxes.append((x, y, w, h))
        return door_boxes
    except:
        return []

def detect_objects_from_base64(b64_image: str) -> list[dict]:
    """Convenience wrapper that accepts base64-encoded image strings."""
    image_bytes = base64.b64decode(b64_image)
    return detect_objects(image_bytes)
