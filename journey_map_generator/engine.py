"""
Rule-based journey map scaffolding engine.
Extracts phases, pain points, and emotions from coded research data.
No LLM required — works entirely on heuristics and pattern matching.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Optional

from .models import (
    Effort,
    Emotion,
    JourneyMap,
    JourneyPhase,
    JourneyStep,
    Opportunity,
    PainPoint,
    PainPointSeverity,
    PersonaContext,
)

# ---------------------------------------------------------------------------
# Emotion lexicons
# ---------------------------------------------------------------------------

EMOTION_KEYWORDS: dict[Emotion, list[str]] = {
    Emotion.FRUSTRATED: [
        "frustrat", "annoyed", "irritated", "stuck", "blocked", "can't", "cannot",
        "impossible", "terrible", "awful", "hate", "broken", "slow", "wrong",
        "painful", "wasted", "pointless", "useless", "confusing",
    ],
    Emotion.CONFUSED: [
        "confus", "unclear", "don't understand", "no idea", "lost", "where",
        "how do i", "which", "not sure", "uncertain", "bewildered", "baffled",
        "misleading", "complicated",
    ],
    Emotion.ANXIOUS: [
        "anxious", "worried", "nervous", "scared", "afraid", "risky", "risk",
        "concern", "hesitant", "doubt", "unsure", "fear", "panic",
    ],
    Emotion.OVERWHELMED: [
        "overwhelm", "too much", "too many", "flood", "inundated", "overload",
        "exhausted", "drowning", "complex", "complicated", "long",
    ],
    Emotion.NEUTRAL: [
        "okay", "fine", "alright", "average", "so-so", "acceptable", "adequate",
    ],
    Emotion.HOPEFUL: [
        "hope", "expect", "looking forward", "might", "could", "potential",
        "promising", "optimistic",
    ],
    Emotion.SATISFIED: [
        "satisfied", "good", "nice", "works", "helpful", "useful", "clear",
        "easy", "simple", "efficient", "quick", "smooth", "happy",
    ],
    Emotion.DELIGHTED: [
        "love", "amazing", "excellent", "fantastic", "perfect", "outstanding",
        "brilliant", "delight", "great", "wonderful", "best", "awesome",
    ],
}

EMOTION_SCORES: dict[Emotion, float] = {
    Emotion.FRUSTRATED: -0.8,
    Emotion.CONFUSED: -0.5,
    Emotion.ANXIOUS: -0.6,
    Emotion.OVERWHELMED: -0.7,
    Emotion.NEUTRAL: 0.0,
    Emotion.HOPEFUL: 0.3,
    Emotion.SATISFIED: 0.6,
    Emotion.DELIGHTED: 0.9,
}

PAIN_SEVERITY_SIGNALS: dict[PainPointSeverity, list[str]] = {
    PainPointSeverity.CRITICAL: [
        "can't", "cannot", "impossible", "broken", "doesn't work", "fails",
        "never", "always", "every time", "stopped", "crashed", "lost",
        "critical", "blocker", "urgent",
    ],
    PainPointSeverity.MODERATE: [
        "difficult", "hard", "slow", "confusing", "unclear", "annoying",
        "frustrating", "takes too long", "should be easier",
    ],
    PainPointSeverity.MINOR: [
        "minor", "small", "little", "slight", "occasionally", "sometimes",
        "could be better", "wish",
    ],
}

PHASE_SIGNAL_KEYWORDS: dict[str, list[str]] = {
    "Awareness": [
        "discover", "learn about", "first heard", "saw", "read", "noticed",
        "aware", "found out", "recommended", "ad", "search",
    ],
    "Consideration": [
        "consider", "compare", "research", "evaluate", "options", "alternative",
        "decided", "choosing", "looking at", "review", "feature",
    ],
    "Onboarding": [
        "sign up", "register", "create account", "first time", "setup",
        "install", "getting started", "welcome", "tutorial", "onboard",
    ],
    "Core Use": [
        "use", "using", "daily", "workflow", "task", "complete", "do",
        "work", "create", "build", "run",
    ],
    "Problem": [
        "issue", "error", "bug", "problem", "fail", "broke", "crash",
        "support", "help", "fix",
    ],
    "Resolution": [
        "resolved", "fixed", "solved", "worked out", "eventually", "finally",
        "figured out", "workaround",
    ],
}


# ---------------------------------------------------------------------------
# Text preprocessing
# ---------------------------------------------------------------------------

def _sentences(text: str) -> list[str]:
    """Split text into sentences."""
    text = re.sub(r"\n+", " ", text)
    return [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]


def _detect_emotion(text: str) -> tuple[Emotion, float]:
    """Detect dominant emotion and score from text."""
    text_lower = text.lower()
    scores: dict[Emotion, int] = Counter()
    for emotion, keywords in EMOTION_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[emotion] += 1

    if not scores:
        return Emotion.NEUTRAL, 0.0

    dominant = scores.most_common(1)[0][0]
    return dominant, EMOTION_SCORES[dominant]


def _detect_pain_severity(text: str) -> PainPointSeverity:
    """Detect pain point severity from text."""
    text_lower = text.lower()
    for severity in [
        PainPointSeverity.CRITICAL,
        PainPointSeverity.MODERATE,
        PainPointSeverity.MINOR,
    ]:
        for signal in PAIN_SEVERITY_SIGNALS[severity]:
            if signal in text_lower:
                return severity
    return PainPointSeverity.MODERATE


def _is_pain_point(sentence: str) -> bool:
    """Heuristic: does this sentence describe a pain point?"""
    s = sentence.lower()
    negative_signals = [
        "can't", "cannot", "doesn't", "don't", "never", "always broken",
        "hard to", "difficult", "confusing", "unclear", "slow", "annoying",
        "frustrat", "stuck", "issue", "problem", "error", "fail", "wish",
        "should", "why can't", "doesn't work",
    ]
    return any(sig in s for sig in negative_signals)


def _is_opportunity(sentence: str) -> bool:
    """Heuristic: does this sentence hint at an opportunity?"""
    s = sentence.lower()
    opportunity_signals = [
        "should", "could", "would be nice", "if only", "wish", "imagine if",
        "would help", "needs to", "want to be able", "improve", "better if",
    ]
    return any(sig in s for sig in opportunity_signals)


def _classify_phase(text: str) -> Optional[str]:
    """Attempt to classify text into a journey phase."""
    text_lower = text.lower()
    phase_scores: dict[str, int] = Counter()
    for phase, keywords in PHASE_SIGNAL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                phase_scores[phase] += 1
    if not phase_scores:
        return None
    return phase_scores.most_common(1)[0][0]


# ---------------------------------------------------------------------------
# Structured input parsing
# ---------------------------------------------------------------------------

def parse_coded_data(raw: str) -> dict[str, list[str]]:
    """
    Parse structured coded research data.
    Expects blocks like:
      ## Phase: Onboarding
      - User tried to sign up but couldn't find the button.
      - First time users were confused by the two-step process.

    Returns dict of phase_name -> list of observation strings.
    """
    result: dict[str, list[str]] = {}
    current_phase = "General"
    result[current_phase] = []

    phase_re = re.compile(
        r"^##\s*(?:Phase:?\s*)?(.+)$", re.IGNORECASE | re.MULTILINE
    )
    lines = raw.split("\n")
    for line in lines:
        line = line.strip()
        if not line:
            continue
        phase_match = phase_re.match(line)
        if phase_match:
            current_phase = phase_match.group(1).strip()
            if current_phase not in result:
                result[current_phase] = []
        elif line.startswith(("-", "*", "•", "–")):
            observation = line.lstrip("-*•– ").strip()
            if observation:
                result.setdefault(current_phase, []).append(observation)
        else:
            result.setdefault(current_phase, []).append(line)

    # Remove empty phases
    return {k: v for k, v in result.items() if v}


# ---------------------------------------------------------------------------
# Core scaffolding engine
# ---------------------------------------------------------------------------

def scaffold_journey_map(
    raw_data: str,
    persona_name: str = "Primary User",
    persona_role: Optional[str] = None,
    title: Optional[str] = None,
) -> JourneyMap:
    """
    Scaffold a journey map from raw coded research data.
    Entirely rule-based — no LLM required.

    Args:
        raw_data: Raw coded research notes (markdown-structured or plain text)
        persona_name: Name of the research persona
        persona_role: Optional role/description for the persona
        title: Optional journey map title

    Returns:
        JourneyMap dataclass populated from the data
    """
    coded = parse_coded_data(raw_data)
    phases: list[JourneyPhase] = []
    all_goals: list[str] = []
    all_frustrations: list[str] = []

    for phase_name, observations in coded.items():
        steps: list[JourneyStep] = []
        phase_emotions: list[float] = []

        for i, obs in enumerate(observations):
            sentences = _sentences(obs)
            if not sentences:
                continue

            emotion, score = _detect_emotion(obs)
            phase_emotions.append(score)

            pain_points: list[PainPoint] = []
            opportunities: list[Opportunity] = []
            actions: list[str] = []
            thoughts: list[str] = []

            for sentence in sentences:
                if _is_pain_point(sentence):
                    severity = _detect_pain_severity(sentence)
                    pain_points.append(
                        PainPoint(
                            description=sentence,
                            severity=severity,
                            source_quotes=[sentence],
                        )
                    )
                    if score < -0.3:
                        all_frustrations.append(sentence)
                elif _is_opportunity(sentence):
                    opportunities.append(
                        Opportunity(
                            description=sentence,
                            impact="medium",
                        )
                    )
                elif score > 0.3:
                    all_goals.append(sentence)

                # Heuristic: action vs thought
                if any(
                    v in sentence.lower()
                    for v in ["click", "open", "go to", "navigate", "select", "enter", "type", "scroll"]
                ):
                    actions.append(sentence)
                elif "?" in sentence or any(
                    t in sentence.lower()
                    for t in ["wonder", "think", "feel", "hope", "expect", "worry"]
                ):
                    thoughts.append(sentence)

            # Determine step effort from emotion score and pain density
            pain_count = len(pain_points)
            if pain_count >= 2 or score < -0.6:
                effort = Effort.HIGH
            elif pain_count == 1 or score < -0.2:
                effort = Effort.MEDIUM
            else:
                effort = Effort.LOW

            step_name = f"Step {i + 1}"
            # Try to extract a concise step name from first sentence
            first_sent = sentences[0] if sentences else obs
            if len(first_sent) <= 60:
                step_name = first_sent
            else:
                # Truncate to ~5 words
                words = first_sent.split()[:6]
                step_name = " ".join(words) + "…"

            steps.append(
                JourneyStep(
                    name=step_name,
                    description=obs,
                    emotion=emotion,
                    emotion_score=score,
                    effort=effort,
                    pain_points=pain_points,
                    opportunities=opportunities,
                    actions=actions,
                    thoughts=thoughts,
                    touchpoints=[],
                )
            )

        overall_sentiment = (
            sum(phase_emotions) / len(phase_emotions) if phase_emotions else 0.0
        )
        dominant_emotion, _ = _detect_emotion(
            " ".join(observations)
        )

        phases.append(
            JourneyPhase(
                name=phase_name,
                description=f"Observations from {len(observations)} coded data points.",
                steps=steps,
                overall_sentiment=overall_sentiment,
                dominant_emotion=dominant_emotion,
            )
        )

    persona = PersonaContext(
        name=persona_name,
        role=persona_role,
        goals=list(set(all_goals[:5])),
        frustrations=list(set(all_frustrations[:5])),
    )

    # Derive key insights
    all_pp = []
    for ph in phases:
        for st in ph.steps:
            for pp in st.pain_points:
                all_pp.append((ph.name, pp))

    critical = [
        f"{ctx}: {pp.description}"
        for ctx, pp in all_pp
        if pp.severity == PainPointSeverity.CRITICAL
    ]

    journey = JourneyMap(
        title=title or f"Journey Map — {persona_name}",
        persona=persona,
        phases=phases,
        key_insights=critical[:5],
        critical_moments=critical[:3],
        source_data_summary=f"Processed {sum(len(v) for v in coded.values())} observations across {len(coded)} phases.",
    )

    return journey
