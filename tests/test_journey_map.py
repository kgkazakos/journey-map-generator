"""Tests for journey-map-generator."""
from __future__ import annotations

from pathlib import Path

import pytest

from journey_map_generator.engine import (
    _detect_emotion,
    _is_pain_point,
    _is_opportunity,
    _classify_phase,
    parse_coded_data,
    scaffold_journey_map,
)
from journey_map_generator.export import to_csv, to_json, to_markdown
from journey_map_generator.models import (
    Emotion,
    JourneyMap,
    PainPointSeverity,
)

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Unit tests — emotion detection
# ---------------------------------------------------------------------------


def test_detect_emotion_frustrated():
    emotion, score = _detect_emotion("I can't find the button and it's so frustrating.")
    assert emotion == Emotion.FRUSTRATED
    assert score < 0


def test_detect_emotion_delighted():
    emotion, score = _detect_emotion("This feature is amazing and I love it.")
    assert emotion == Emotion.DELIGHTED
    assert score > 0.5


def test_detect_emotion_neutral():
    emotion, score = _detect_emotion("The system is okay I suppose.")
    assert score >= -0.2


def test_detect_emotion_score_range():
    _, score = _detect_emotion("terrible broken impossible")
    assert -1.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Unit tests — pain point detection
# ---------------------------------------------------------------------------


def test_is_pain_point_true():
    assert _is_pain_point("I can't figure out how to export the data.") is True
    assert _is_pain_point("The feature doesn't work as expected.") is True
    assert _is_pain_point("It's hard to find the settings.") is True


def test_is_pain_point_false():
    assert _is_pain_point("The collaboration feature works really well.") is False
    assert _is_pain_point("Users enjoy the dashboard view.") is False


def test_is_opportunity():
    assert _is_opportunity("Users wish there was a faster way to create projects.") is True
    assert _is_opportunity("It would be nice if export worked automatically.") is True


# ---------------------------------------------------------------------------
# Unit tests — phase classification
# ---------------------------------------------------------------------------


def test_classify_phase_onboarding():
    result = _classify_phase("User signed up and saw the welcome tutorial.")
    assert result == "Onboarding"


def test_classify_phase_problem():
    result = _classify_phase("There was an error and the feature crashed.")
    assert result == "Problem"


# ---------------------------------------------------------------------------
# Integration tests — parse coded data
# ---------------------------------------------------------------------------


def test_parse_coded_data_phases():
    raw = """
## Phase: Awareness
- They searched online for alternatives.

## Phase: Onboarding
- Signing up was confusing.
- Email verification failed twice.
"""
    result = parse_coded_data(raw)
    assert "Awareness" in result
    assert "Onboarding" in result
    assert len(result["Onboarding"]) == 2


def test_parse_coded_data_unstructured():
    raw = "User was frustrated by slow search. They eventually found a workaround."
    result = parse_coded_data(raw)
    # Should fall into General
    assert len(result) >= 1


# ---------------------------------------------------------------------------
# Integration tests — scaffold_journey_map
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_data() -> str:
    return (FIXTURES / "sample_research.md").read_text()


def test_scaffold_returns_journey_map(sample_data):
    journey = scaffold_journey_map(sample_data, persona_name="Research Participant")
    assert isinstance(journey, JourneyMap)


def test_scaffold_has_phases(sample_data):
    journey = scaffold_journey_map(sample_data)
    assert len(journey.phases) >= 3


def test_scaffold_persona(sample_data):
    journey = scaffold_journey_map(sample_data, persona_name="Emma", persona_role="Product Manager")
    assert journey.persona.name == "Emma"
    assert journey.persona.role == "Product Manager"


def test_scaffold_has_steps(sample_data):
    journey = scaffold_journey_map(sample_data)
    total_steps = sum(len(ph.steps) for ph in journey.phases)
    assert total_steps >= 5


def test_scaffold_pain_points(sample_data):
    journey = scaffold_journey_map(sample_data)
    all_pp = journey.all_pain_points()
    assert len(all_pp) >= 1


def test_scaffold_emotion_arc(sample_data):
    journey = scaffold_journey_map(sample_data)
    arc = journey.emotion_arc()
    assert len(arc) >= 1
    for label, score in arc:
        assert -1.0 <= score <= 1.0


def test_scaffold_title(sample_data):
    journey = scaffold_journey_map(sample_data, title="My Custom Map")
    assert journey.title == "My Custom Map"


# ---------------------------------------------------------------------------
# Export tests
# ---------------------------------------------------------------------------


def test_to_json(sample_data):
    journey = scaffold_journey_map(sample_data)
    result = to_json(journey)
    import json
    parsed = json.loads(result)
    assert "title" in parsed
    assert "phases" in parsed


def test_to_markdown(sample_data):
    journey = scaffold_journey_map(sample_data)
    result = to_markdown(journey)
    assert "## Journey Phases" in result
    assert journey.title in result


def test_to_csv(sample_data):
    journey = scaffold_journey_map(sample_data)
    result = to_csv(journey)
    lines = result.strip().split("\n")
    assert len(lines) >= 2  # header + at least one data row
    assert "Phase" in lines[0]
    assert "Emotion" in lines[0]


def test_to_markdown_has_pain_points(sample_data):
    journey = scaffold_journey_map(sample_data)
    result = to_markdown(journey)
    assert "Pain points" in result or "CRITICAL" in result or "MODERATE" in result
