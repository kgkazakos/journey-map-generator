"""
LLM enrichment for journey-map-generator.
Supports Claude Opus 4, Gemini 4 Argon, GPT-5.5.
LLM is ON by default; pass backend=None to run rule-based only.
"""
from __future__ import annotations

import json

from .models import (
    JourneyMap,
    Opportunity,
)

SUPPORTED_BACKENDS = {
    "claude": "anthropic/claude-opus-4-5",
    "gemini": "gemini/gemini-4-argon",
    "openai": "openai/gpt-5.5",
}

DEFAULT_BACKEND = "claude"


def _call_litellm(prompt: str, backend: str, max_tokens: int = 2000) -> str:
    """Call LLM via LiteLLM."""
    try:
        from litellm import completion  # type: ignore
    except ImportError as e:
        raise ImportError(
            "LLM enrichment requires litellm. Install with: pip install 'journey-map-generator[llm]'"
        ) from e

    model = SUPPORTED_BACKENDS.get(backend, backend)
    response = completion(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def enrich_journey_map(
    journey: JourneyMap,
    raw_data: str,
    backend: str = DEFAULT_BACKEND,
) -> JourneyMap:
    """
    Enrich a rule-based journey map with LLM-generated insights.

    Adds:
    - Richer step descriptions and emotional nuance
    - Synthesised key insights
    - Narrative summary
    - Identified moments of truth
    - Opportunities with prioritised recommendations

    Args:
        journey: Base journey map from rule-based engine
        raw_data: Original raw research data
        backend: One of 'claude', 'gemini', 'openai' (or LiteLLM model string)

    Returns:
        Enriched JourneyMap
    """
    # Build a compact representation for the LLM
    phase_summary = []
    for ph in journey.phases:
        steps_text = []
        for st in ph.steps:
            steps_text.append(
                f"  Step: {st.name}\n"
                f"  Emotion: {st.emotion.value} (score: {st.emotion_score:.1f})\n"
                f"  Pain points: {[pp.description for pp in st.pain_points]}\n"
            )
        phase_summary.append(
            f"Phase: {ph.name}\n"
            f"Overall sentiment: {ph.overall_sentiment:.2f}\n"
            + "\n".join(steps_text)
        )

    map_text = "\n\n".join(phase_summary)

    # ---- 1. Generate narrative summary ----
    summary_prompt = f"""You are a senior UX researcher synthesising a user journey map.

PERSONA: {journey.persona.name} ({journey.persona.role or 'User'})
JOURNEY TITLE: {journey.title}

PHASE & STEP DATA:
{map_text}

RAW RESEARCH DATA (excerpt):
{raw_data[:2000]}

Write a 2-3 paragraph narrative summary of this user's journey. Focus on:
- The emotional arc (where do they start, where does it peak negatively, where does it resolve?)
- The most critical friction points
- The moments where they feel success or delight
- What this tells us about the core product/service gap

Be specific, practitioner-facing, and avoid generic statements. Do not use bullet points."""

    try:
        journey.summary = _call_litellm(summary_prompt, backend, max_tokens=600)
    except Exception as e:
        journey.summary = f"[LLM enrichment failed: {e}]"

    # ---- 2. Generate key insights ----
    insights_prompt = f"""You are a UX researcher extracting actionable insights from a journey map.

JOURNEY: {journey.title}
PERSONA: {journey.persona.name}

PHASE DATA:
{map_text}

Return EXACTLY 5 key insights as a JSON array of strings. Each insight should:
- Be a complete, actionable statement
- Reference a specific phase or moment in the journey
- Be written for a product team audience (PM, designer, engineer)
- Avoid vague generalities

Return only valid JSON, no markdown:
["insight 1", "insight 2", "insight 3", "insight 4", "insight 5"]"""

    try:
        insights_raw = _call_litellm(insights_prompt, backend, max_tokens=500)
        # Strip potential markdown fences
        clean = insights_raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        journey.key_insights = json.loads(clean)
    except Exception:
        # Keep rule-based insights
        pass

    # ---- 3. Identify moments of truth ----
    moments_prompt = f"""You are a CX strategist. Given this journey map data, identify the 3 most critical "moments of truth" — the make-or-break interactions that disproportionately affect perception of the product or service.

JOURNEY: {journey.title}
{map_text}

Return EXACTLY 3 moments of truth as a JSON array of strings. Be specific.
Return only valid JSON, no markdown:
["moment 1", "moment 2", "moment 3"]"""

    try:
        moments_raw = _call_litellm(moments_prompt, backend, max_tokens=400)
        clean = moments_raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        journey.critical_moments = json.loads(clean)
    except Exception:
        pass

    # ---- 4. Enrich opportunities per phase ----
    opps_prompt = f"""You are a product designer generating opportunity statements from a journey map.

JOURNEY: {journey.title}
PERSONA: {journey.persona.name}

{map_text}

For each phase, generate 1-2 concrete, specific opportunities using the format:
"How might we [action] so that [persona] can [outcome]?"

Return as JSON with phase names as keys:
{{"Phase Name": ["HMW 1", "HMW 2"]}}

Return only valid JSON, no markdown."""

    try:
        opps_raw = _call_litellm(opps_prompt, backend, max_tokens=800)
        clean = opps_raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        phase_opps: dict[str, list[str]] = json.loads(clean)

        for ph in journey.phases:
            if ph.name in phase_opps:
                hmws = phase_opps[ph.name]
                for hmw in hmws:
                    # Add to last step of phase (representative)
                    if ph.steps:
                        ph.steps[-1].opportunities.append(
                            Opportunity(description=hmw, impact="high")
                        )
    except Exception:
        pass

    journey.llm_backend = SUPPORTED_BACKENDS.get(backend, backend)
    return journey


def get_available_backends() -> dict[str, str]:
    """Return dict of available backends and their model strings."""
    return SUPPORTED_BACKENDS.copy()
