"""Basic usage example for journey-map-generator."""
from journey_map_generator import scaffold_journey_map
from journey_map_generator.export import to_markdown, to_json

# Sample coded research data
RESEARCH_DATA = """
## Phase: Awareness
- User discovered the tool through a LinkedIn post by a colleague.
- They searched for alternatives and compared pricing before deciding.

## Phase: Onboarding
- First login was smooth but the dashboard was overwhelming — too many panels.
- User couldn't figure out how to import existing data. This took 30 minutes.
- The quick-start guide was helpful once they found it (hidden in the footer).

## Phase: Core Use
- Daily use is mostly seamless, but search is slow when dealing with large datasets.
- Users love the collaboration features — consistently rated highest in interviews.
- Exporting to CSV doesn't work with their company's template format — a critical blocker.

## Phase: Problem
- Error messages show only codes, not explanations. Users feel completely lost.
- Support response time averages 4 hours. Unacceptable for production issues.

## Phase: Resolution
- Most users find workarounds eventually, but feel the product should handle this natively.
- Long-term users are satisfied but consistently describe onboarding as "a nightmare."
"""

# --- Rule-based only (no API key needed) ---
journey = scaffold_journey_map(
    raw_data=RESEARCH_DATA,
    persona_name="Emma",
    persona_role="Senior Product Manager",
    title="Emma's Journey — Project Management Tool",
)

print("=== Journey Map (Rule-based) ===")
print(f"Title: {journey.title}")
print(f"Phases: {[ph.name for ph in journey.phases]}")
print(f"Total steps: {sum(len(ph.steps) for ph in journey.phases)}")
print()

# Emotion arc
print("=== Emotion Arc ===")
for label, score in journey.emotion_arc():
    bar = "█" * int(abs(score) * 10)
    direction = "+" if score >= 0 else "-"
    print(f"  {label[:50]:<50} {direction}{bar} ({score:+.2f})")
print()

# Critical pain points
critical = journey.critical_pain_points()
if critical:
    print("=== Critical Pain Points ===")
    for ctx, pp in critical:
        print(f"  [{ctx}] {pp.description}")
    print()

# Export to markdown
md = to_markdown(journey)
print("=== Markdown Export (first 20 lines) ===")
for line in md.split("\n")[:20]:
    print(line)
print("...")
print()

# Export to JSON
jdata = to_json(journey)
import json
parsed = json.loads(jdata)
print(f"=== JSON Export ===")
print(f"Keys: {list(parsed.keys())}")
print(f"Phase count: {len(parsed['phases'])}")
print()

# --- LLM enrichment (requires API keys) ---
print("=== LLM Enrichment ===")
print("To enrich with Claude Opus:")
print("  from journey_map_generator.llm import enrich_journey_map")
print("  journey = enrich_journey_map(journey, raw_data=RESEARCH_DATA, backend='claude')")
print()
print("Supported backends:")
from journey_map_generator.llm import get_available_backends
for name, model in get_available_backends().items():
    print(f"  {name}: {model}")
