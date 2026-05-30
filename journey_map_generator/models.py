"""Core data models for journey-map-generator."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Emotion(str, Enum):
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    NEUTRAL = "neutral"
    SATISFIED = "satisfied"
    DELIGHTED = "delighted"
    ANXIOUS = "anxious"
    OVERWHELMED = "overwhelmed"
    HOPEFUL = "hopeful"


class Effort(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class PainPointSeverity(str, Enum):
    MINOR = "minor"
    MODERATE = "moderate"
    CRITICAL = "critical"


@dataclass
class PainPoint:
    description: str
    severity: PainPointSeverity = PainPointSeverity.MODERATE
    frequency: Optional[str] = None
    source_quotes: list[str] = field(default_factory=list)


@dataclass
class Opportunity:
    description: str
    impact: str = "medium"
    effort_to_fix: Effort = Effort.MEDIUM


@dataclass
class JourneyStep:
    name: str
    description: str
    emotion: Emotion = Emotion.NEUTRAL
    emotion_score: float = 0.0  # -1.0 (negative) to 1.0 (positive)
    effort: Effort = Effort.MEDIUM
    pain_points: list[PainPoint] = field(default_factory=list)
    opportunities: list[Opportunity] = field(default_factory=list)
    thoughts: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    touchpoints: list[str] = field(default_factory=list)


@dataclass
class JourneyPhase:
    name: str
    description: str
    steps: list[JourneyStep] = field(default_factory=list)
    overall_sentiment: float = 0.0  # aggregate of step scores
    dominant_emotion: Emotion = Emotion.NEUTRAL
    phase_goal: Optional[str] = None


@dataclass
class PersonaContext:
    name: str
    role: Optional[str] = None
    goals: list[str] = field(default_factory=list)
    frustrations: list[str] = field(default_factory=list)
    context: Optional[str] = None


@dataclass
class JourneyMap:
    title: str
    persona: PersonaContext
    phases: list[JourneyPhase] = field(default_factory=list)
    summary: Optional[str] = None
    key_insights: list[str] = field(default_factory=list)
    critical_moments: list[str] = field(default_factory=list)  # moments of truth
    llm_backend: Optional[str] = None
    source_data_summary: Optional[str] = None

    def emotion_arc(self) -> list[tuple[str, float]]:
        """Return the emotional arc across all steps."""
        arc = []
        for phase in self.phases:
            for step in phase.steps:
                arc.append((f"{phase.name} → {step.name}", step.emotion_score))
        return arc

    def all_pain_points(self) -> list[tuple[str, PainPoint]]:
        """Return all pain points with phase context."""
        points = []
        for phase in self.phases:
            for step in phase.steps:
                for pp in step.pain_points:
                    points.append((f"{phase.name} / {step.name}", pp))
        return points

    def critical_pain_points(self) -> list[tuple[str, PainPoint]]:
        return [
            (ctx, pp)
            for ctx, pp in self.all_pain_points()
            if pp.severity == PainPointSeverity.CRITICAL
        ]
