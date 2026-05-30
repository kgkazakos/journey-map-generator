"""
journey-map-generator — CPR Orbital Tool #38
Scaffolds journey maps with phases, pain points, and emotions from coded research data.
"""
__version__ = "0.1.0"

from .engine import scaffold_journey_map
from .export import to_csv, to_json, to_markdown
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

__all__ = [
    "scaffold_journey_map",
    "to_json",
    "to_markdown",
    "to_csv",
    "JourneyMap",
    "JourneyPhase",
    "JourneyStep",
    "PersonaContext",
    "PainPoint",
    "Opportunity",
    "Emotion",
    "Effort",
    "PainPointSeverity",
]
