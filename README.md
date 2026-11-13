# journey-map-generator

**CPR Orbital Tool #38 — S6: Pre-study & impact**

Scaffold user journey maps with phases, pain points, and emotional arcs from coded qualitative research data. Rule-based core, LLM enrichment via Claude Opus 4, Gemini 4 Argon, or GPT-5.5.

---

## What this solves

After user research, you have notes, transcripts, and affinity maps — but turning that into a structured journey map is slow, inconsistent, and usually done in a slide deck that doesn't connect to the underlying data.

`journey-map-generator` takes your coded research data and scaffolds a structured journey map in seconds: phases, steps, pain points ranked by severity, emotional arc, moments of truth, and HMW opportunities. LLM enrichment adds narrative synthesis and cross-phase insight extraction.

## What this is — and what it is not

**This is:** a tool that scaffolds a journey map from your coded research observations, with rule-based heuristics for emotion and pain detection and optional LLM synthesis for narrative layers.

**This is not:** a substitute for proper user research or a way to generate a journey map without research data. The quality of output depends entirely on the quality and depth of your coded observations. The emotional arc and pain severity ratings are heuristic — treat them as starting points for researcher interpretation, not ground truth.

---

## Features

- **Phase-aware scaffolding** — parse `## Phase: Name` structured research notes into journey phases
- **Emotion detection** — keyword-based sentiment scoring with emotional arc visualisation
- **Pain point extraction** — automatic severity classification (critical / moderate / minor)
- **Opportunity generation** — surfaces HMW statements per phase via LLM
- **Moments of truth** — LLM-identified make-or-break interactions
- **Multi-backend LLM** — Claude Opus 4, Gemini 4 Argon, GPT-5.5 (via LiteLLM)
- **Export** — JSON (CI-friendly), Markdown, CSV for downstream use
- **Streamlit UI** — interactive map with emotion arc charts and per-phase drill-down
- **Batch mode** — generate maps for multiple personas from one dataset

---

## Installation

```bash
pip install journey-map-generator
```

With LLM enrichment:

```bash
pip install 'journey-map-generator[llm]'
```

---

## Quick start

### CLI

```bash
# Rule-based only
journey-map-generator generate --input research.md --persona "Emma" --llm-backend none

# With Claude Opus (default)
export ANTHROPIC_API_KEY=sk-ant-...
journey-map-generator generate --input research.md --persona "Emma"

# With Gemini
export GEMINI_API_KEY=...
journey-map-generator generate --input research.md --persona "Emma" --llm-backend gemini

# With GPT-5.5
export OPENAI_API_KEY=sk-...
journey-map-generator generate --input research.md --persona "Emma" --llm-backend openai

# Export to Markdown
journey-map-generator generate --input research.md --format markdown --output map.md

# Export to JSON (CI pipelines)
journey-map-generator generate --input research.md --format json --output map.json
```

### Batch mode (multiple personas)

```bash
journey-map-generator batch \
  --input research.md \
  --personas "Power User,New User,Admin" \
  --output-dir ./maps/
```

### Python API

```python
from journey_map_generator import scaffold_journey_map
from journey_map_generator.llm import enrich_journey_map
from journey_map_generator.export import to_markdown

# Step 1: rule-based scaffold
journey = scaffold_journey_map(
    raw_data=open("research.md").read(),
    persona_name="Emma",
    persona_role="Senior Product Manager",
)

# Step 2: LLM enrichment (optional)
journey = enrich_journey_map(journey, raw_data, backend="claude")

# Step 3: export
print(to_markdown(journey))
```

### Streamlit UI

```bash
streamlit run app.py
```

---

## Input format

Structure your coded research data with phase headings and observation bullets:

```markdown
## Phase: Awareness
- User discovered the product via a colleague recommendation.
- The landing page was confusing — couldn't identify the core value prop.

## Phase: Onboarding
- Sign-up flow was quick but email verification failed twice.
- Couldn't find how to import existing data — spent 20 minutes searching.

## Phase: Core Use
- Search is frustratingly slow with large datasets.
- Collaborative features are consistently the highest-rated by users.
- CSV export doesn't support their company's file format — critical blocker.

## Phase: Problem
- Error messages show only codes, not explanations.
- Support response time averages 4 hours — unacceptable for production.
```

Unstructured text is also supported — the engine will attempt phase classification via keyword matching.

---

## LLM backends

| Backend | Model | Environment variable |
|---------|-------|---------------------|
| `claude` (default) | `anthropic/claude-opus-4-5` | `ANTHROPIC_API_KEY` |
| `gemini` | `gemini/gemini-4-argon` | `GEMINI_API_KEY` |
| `openai` | `openai/gpt-5.5` | `OPENAI_API_KEY` |
| `none` | Rule-based only | — |

---

## CI / JSON output

LLM enrichment never runs in CI if API keys are absent — the tool degrades gracefully to rule-based output. Use `--format json` and `--llm-backend none` for reproducible pipeline runs:

```bash
journey-map-generator generate --input research.md --format json --llm-backend none > map.json
```

---

## Part of the CPR Ecosystem

`journey-map-generator` is **Tool #38** in the [CPR Orbital Series](https://github.com/kgkazakos) — 40 open-source Python tools for AI-native product research infrastructure, shipping almost daily.

**Related tools in this series:**

| Tool | What it does |
|------|-------------|
| [`affinity-bot`](https://github.com/kgkazakos/affinity-bot) | LLM-powered affinity diagramming from raw research notes |
| [`jtbd-extractor`](https://github.com/kgkazakos/jtbd-extractor) | Pulls Jobs-to-Be-Done statements from interview transcripts |
| [`insight-differ`](https://github.com/kgkazakos/insight-differ) | Surfaces contradictions and gaps between research reports |
| [`qual-sniffer`](https://github.com/kgkazakos/qual-sniffer) | Detects methodological weaknesses in discussion guides |
| [`say-do-lite`](https://github.com/kgkazakos/say-do-lite) | Lightweight Say-Do Gap detection from transcripts |

---

## Development

```bash
git clone https://github.com/kgkazakos/journey-map-generator
cd journey-map-generator
pip install -e ".[dev]"
pytest tests/ -v
ruff check journey_map_generator/
```

---

## License

MIT © Kostas Kazakos

---

*Part of the Computational Product Research (CPR) discipline — building AI-native infrastructure for product research.*
