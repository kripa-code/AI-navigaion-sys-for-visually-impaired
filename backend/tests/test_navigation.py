"""
BlindBuddy — Navigation Module Tests
"""
import pytest
from modules.navigation import _haversine, _strip_html, get_next_step, check_deviation


def test_haversine_same_point():
    """Distance between the same point should be 0."""
    assert _haversine(0, 0, 0, 0) == pytest.approx(0.0, abs=0.1)


def test_haversine_known_distance():
    """New York to LA ≈ 3940 km."""
    dist = _haversine(40.7128, -74.0060, 34.0522, -118.2437)
    assert 3_900_000 < dist < 4_000_000  # meters


def test_strip_html():
    assert _strip_html("<b>Turn left</b> onto <div>Main St</div>") == "Turn left onto Main St"
    assert _strip_html("No HTML here") == "No HTML here"


MOCK_STEPS = [
    {
        "index": 0,
        "instruction": "Head north on Main St",
        "distance_m": 200,
        "duration_s": 160,
        "start_lat": 37.7749, "start_lng": -122.4194,
        "end_lat": 37.7760, "end_lng": -122.4194,
        "maneuver": "",
    },
    {
        "index": 1,
        "instruction": "Turn right onto Oak Ave",
        "distance_m": 150,
        "duration_s": 120,
        "start_lat": 37.7760, "start_lng": -122.4194,
        "end_lat": 37.7760, "end_lng": -122.4180,
        "maneuver": "turn-right",
    },
]


def test_get_next_step_returns_instruction():
    step_info = get_next_step(MOCK_STEPS, 37.7749, -122.4194, 0)
    assert "instruction" in step_info
    assert step_info["instruction"] == "Head north on Main St"
    assert "distance_remaining_m" in step_info


def test_get_next_step_arrived():
    step_info = get_next_step(MOCK_STEPS, 0, 0, 99)  # beyond last step
    assert step_info["arrived"] is True


def test_check_deviation_on_route():
    # User is at the start of step 0 — should NOT be deviated
    deviated = check_deviation(MOCK_STEPS, 37.7750, -122.4194, 0)
    assert deviated is False


def test_check_deviation_off_route():
    # User is 1 degree off lat (~111 km) — should be deviated
    deviated = check_deviation(MOCK_STEPS, 38.7749, -122.4194, 0)
    assert deviated is True
