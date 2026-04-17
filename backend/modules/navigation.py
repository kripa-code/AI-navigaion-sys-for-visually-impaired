"""
BlindBuddy — Navigation Module
Interfaces with Google Maps Directions API for route planning and step tracking.
"""
import math
import requests
from typing import Optional
from config import GOOGLE_MAPS_API_KEY

DIRECTIONS_BASE = "https://maps.googleapis.com/maps/api/directions/json"
GEOCODE_BASE = "https://maps.googleapis.com/maps/api/geocode/json"

# ─── Route Fetching ────────────────────────────────────────────────────────────

def get_route(origin_lat: float, origin_lng: float, destination: str) -> dict:
    """
    Fetch a walking route from origin coords to a destination string.
    Returns: { "steps": [...], "eta_minutes": int, "distance_km": float, "polyline": str }
    """
    params = {
        "origin": f"{origin_lat},{origin_lng}",
        "destination": destination,
        "mode": "walking",
        "key": GOOGLE_MAPS_API_KEY,
    }
    resp = requests.get(DIRECTIONS_BASE, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "OK":
        raise ValueError(f"Directions API error: {data.get('status')} — {data.get('error_message', '')}")

    leg = data["routes"][0]["legs"][0]
    steps = []
    for i, s in enumerate(leg["steps"]):
        steps.append({
            "index": i,
            "instruction": _strip_html(s.get("html_instructions", "")),
            "distance_m": s["distance"]["value"],
            "duration_s": s["duration"]["value"],
            "start_lat": s["start_location"]["lat"],
            "start_lng": s["start_location"]["lng"],
            "end_lat": s["end_location"]["lat"],
            "end_lng": s["end_location"]["lng"],
            "maneuver": s.get("maneuver", ""),
        })

    return {
        "steps": steps,
        "eta_minutes": leg["duration"]["value"] // 60,
        "distance_km": round(leg["distance"]["value"] / 1000, 2),
        "polyline": data["routes"][0]["overview_polyline"]["points"],
        "start_address": leg["start_address"],
        "end_address": leg["end_address"],
    }


def get_next_step(steps: list, current_lat: float, current_lng: float, step_index: int) -> dict:
    """
    Given current position and step index, return the current navigation instruction
    with remaining distance and whether we should advance to the next step.
    """
    if step_index >= len(steps):
        return {
            "instruction": "You have arrived at your destination.",
            "distance_remaining_m": 0,
            "advance": False,
            "arrived": True,
        }

    step = steps[step_index]
    dist_to_end = _haversine(
        current_lat, current_lng,
        step["end_lat"], step["end_lng"]
    )

    advance = dist_to_end < 10  # within 10m of step end → advance
    return {
        "instruction": step["instruction"],
        "distance_remaining_m": round(dist_to_end),
        "maneuver": step["maneuver"],
        "advance": advance,
        "arrived": False,
    }


def check_deviation(steps: list, current_lat: float, current_lng: float, step_index: int) -> bool:
    """
    Returns True if the user is more than 25m away from the nearest point on the route.
    """
    if step_index >= len(steps):
        return False
    step = steps[step_index]
    dist = _haversine(current_lat, current_lng, step["start_lat"], step["start_lng"])
    return dist > 25


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Returns distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _strip_html(text: str) -> str:
    """Remove HTML tags from Google Maps instruction strings."""
    import re
    clean = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", clean).strip()
