"""Export journey maps to JSON, Markdown, and CSV."""
from __future__ import annotations

import csv
import io
import json

from .models import JourneyMap


def to_json(journey: JourneyMap, indent: int = 2) -> str:
    """Serialize journey map to JSON string."""
    def _serialise(obj):
        if hasattr(obj, "value"):
            return obj.value
        if hasattr(obj, "__dataclass_fields__"):
            return {k: _serialise(v) for k, v in vars(obj).items()}
        if isinstance(obj, list):
            return [_serialise(i) for i in obj]
        if isinstance(obj, dict):
            return {k: _serialise(v) for k, v in obj.items()}
        return obj

    return json.dumps(_serialise(journey), indent=indent)


def to_markdown(journey: JourneyMap) -> str:
    """Render journey map as structured Markdown."""
    lines = []
    lines.append(f"# {journey.title}")
    lines.append("")

    # Persona
    lines.append(f"**Persona:** {journey.persona.name}")
    if journey.persona.role:
        lines.append(f"**Role:** {journey.persona.role}")
    if journey.persona.goals:
        lines.append(f"**Goals:** {'; '.join(journey.persona.goals)}")
    if journey.persona.frustrations:
        lines.append(f"**Known frustrations:** {'; '.join(journey.persona.frustrations)}")
    lines.append("")

    # Summary
    if journey.summary:
        lines.append("## Summary")
        lines.append("")
        lines.append(journey.summary)
        lines.append("")

    # Key insights
    if journey.key_insights:
        lines.append("## Key Insights")
        lines.append("")
        for ins in journey.key_insights:
            lines.append(f"- {ins}")
        lines.append("")

    # Moments of truth
    if journey.critical_moments:
        lines.append("## Moments of Truth")
        lines.append("")
        for i, m in enumerate(journey.critical_moments, 1):
            lines.append(f"{i}. {m}")
        lines.append("")

    # Phases
    lines.append("## Journey Phases")
    lines.append("")

    for ph in journey.phases:
        sentiment_label = (
            "😊 Positive" if ph.overall_sentiment > 0.2
            else "😐 Neutral" if ph.overall_sentiment > -0.2
            else "😞 Negative"
        )
        lines.append(f"### {ph.name} — {sentiment_label}")
        lines.append("")
        lines.append(ph.description)
        lines.append("")

        for st in ph.steps:
            lines.append(f"**Step:** {st.name}")
            lines.append(f"- Emotion: {st.emotion.value} (score: {st.emotion_score:+.1f})")
            lines.append(f"- Effort: {st.effort.value}")

            if st.pain_points:
                lines.append(f"- **Pain points ({len(st.pain_points)}):**")
                for pp in st.pain_points:
                    lines.append(f"  - [{pp.severity.value.upper()}] {pp.description}")

            if st.opportunities:
                lines.append("- **Opportunities:**")
                for opp in st.opportunities:
                    lines.append(f"  - {opp.description}")

            if st.thoughts:
                lines.append(f"- Thoughts: {'; '.join(st.thoughts[:2])}")
            if st.actions:
                lines.append(f"- Actions: {'; '.join(st.actions[:2])}")
            lines.append("")

    # Source
    if journey.source_data_summary:
        lines.append("---")
        lines.append(f"*{journey.source_data_summary}*")
        if journey.llm_backend:
            lines.append(f"*LLM enrichment: {journey.llm_backend}*")

    return "\n".join(lines)


def to_csv(journey: JourneyMap) -> str:
    """Export journey map steps to CSV for spreadsheet use."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Phase", "Step", "Emotion", "Emotion Score", "Effort",
        "Pain Points", "Pain Severity", "Opportunities", "Thoughts", "Actions"
    ])

    for ph in journey.phases:
        for st in ph.steps:
            pain_descs = "; ".join(pp.description for pp in st.pain_points)
            pain_sevs = "; ".join(pp.severity.value for pp in st.pain_points)
            opp_descs = "; ".join(opp.description for opp in st.opportunities)
            writer.writerow([
                ph.name,
                st.name,
                st.emotion.value,
                f"{st.emotion_score:+.2f}",
                st.effort.value,
                pain_descs,
                pain_sevs,
                opp_descs,
                "; ".join(st.thoughts[:3]),
                "; ".join(st.actions[:3]),
            ])

    return output.getvalue()


def emotion_arc_text(journey: JourneyMap) -> str:
    """Render the emotion arc as a simple ASCII chart."""
    arc = journey.emotion_arc()
    if not arc:
        return "No emotion arc data."

    lines = []
    for label, score in arc:
        bar_pos = int((score + 1.0) * 20)  # map -1..1 to 0..40
        bar = " " * bar_pos + "●"
        lines.append(f"  {label[:40]:<40} {bar}  ({score:+.2f})")

    header = "  " + " " * 40 + "|" + " " * 19 + "|"
    ruler = "  " + " " * 40 + "← negative  positive →"
    return "\n".join([ruler, header] + lines)
