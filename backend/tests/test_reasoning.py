"""
BlindBuddy — Reasoning Module Tests (mocked LLM)
"""
import pytest
from unittest.mock import patch, MagicMock
from modules.reasoning import classify_urgency, build_prompt, get_guidance


CLOSE_CAR = [{"object": "car", "raw_class": "car", "direction": "right", "distance": "1 meters", "distance_m": 1.0, "confidence": 0.9}]
MEDIUM_PEDESTRIAN = [{"object": "pedestrian", "raw_class": "person", "direction": "ahead", "distance": "2.5 meters", "distance_m": 2.5, "confidence": 0.8}]
DISTANT_BENCH = [{"object": "bench obstacle", "raw_class": "bench", "direction": "left", "distance": "8 meters", "distance_m": 8.0, "confidence": 0.7}]
STAIRS = [{"object": "stairs", "raw_class": "stairs", "direction": "ahead", "distance": "2 meters", "distance_m": 2.0, "confidence": 0.85}]


def test_urgency_high_close_car():
    assert classify_urgency(CLOSE_CAR) == "HIGH"


def test_urgency_high_stairs():
    assert classify_urgency(STAIRS) == "HIGH"


def test_urgency_medium_pedestrian():
    assert classify_urgency(MEDIUM_PEDESTRIAN) == "MEDIUM"


def test_urgency_low_distant():
    assert classify_urgency(DISTANT_BENCH) == "LOW"


def test_urgency_empty_scene():
    assert classify_urgency([]) == "LOW"


def test_build_prompt_contains_instruction():
    prompt = build_prompt("Turn left in 10 meters", CLOSE_CAR, "HIGH")
    assert "Turn left in 10 meters" in prompt
    assert "car" in prompt
    assert "HIGH" in prompt


@patch("modules.reasoning.client")
def test_get_guidance_mocked_llm(mock_client):
    """Test that get_guidance returns guidance text without hitting real API."""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Stop. A car is very close on your right."
    mock_client.chat.completions.create.return_value = mock_response

    result = get_guidance("Turn right in 10 meters", CLOSE_CAR)
    assert "guidance" in result
    assert "urgency" in result
    assert result["urgency"] == "HIGH"
    assert len(result["guidance"]) > 5


@patch("modules.reasoning.client")
def test_get_guidance_fallback_on_llm_error(mock_client):
    """Test that fallback is used when LLM throws an exception."""
    mock_client.chat.completions.create.side_effect = Exception("API down")
    result = get_guidance("Turn left in 5 meters", [])
    assert result["guidance"] == "Turn left in 5 meters"
    assert result["urgency"] == "LOW"
