"""
InfraMiner AI — Shared Graph State

This module defines the central state schema (InfraMinerState) that flows
through all 8 agents in the LangGraph pipeline.  Every agent reads the
fields it needs and writes its output fields back into this state.

Design decisions
----------------
* Top-level state uses TypedDict (required by LangGraph's StateGraph).
* List fields that agents *append* to use Annotated[list, operator.add]
  so that each node's return value is merged (appended) rather than
  overwriting the previous contents.
* Scalar / optional fields use plain annotations (last-write-wins).
* Domain data models (MaterialRequirement, CandidateSource, etc.) will
  be defined as Pydantic BaseModel classes in src/models/ in a later
  phase.  Until then the list fields are typed as list[dict] so the
  file is importable and usable immediately.
"""

from __future__ import annotations

import operator
from typing import Annotated, Optional, TypedDict


# ---------------------------------------------------------------------------
# InfraMinerState — the single object that travels through the graph
# ---------------------------------------------------------------------------

class InfraMinerState(TypedDict, total=False):
    """Shared state for the InfraMiner AI multi-agent pipeline.

    Field groups
    ------------
    1. Project information        — written by Agent 1 (Project Intelligence)
    2. Material requirements      — written by Agent 2 (Material Requirement)
    3. Candidate sources          — written by Agent 3 (Source Discovery)
    4. Logistics routes           — written by Agent 4 (Geospatial & Logistics)
    5. Cost estimates             — written by Agent 5 (Cost)
    6. Environmental assessments  — written by Agent 6 (Environmental)
    7. Resilience assessments     — written by Agent 7 (Resilience)
    8. Decision results           — written by Agent 8 (Decision)
    9. Workflow metadata          — written by all agents
    """

    # ------------------------------------------------------------------
    # 1. Project information  (Agent 1: Project Intelligence)
    # ------------------------------------------------------------------
    project_name: str
    project_type: str                          # port, highway, dam, rail, …
    project_location: Optional[dict]           # {"lat": float, "lng": float}
    project_scope: str                         # extracted scope description
    project_constraints: list[str]             # CRZ, seismic zone, etc.
    project_timeline: Optional[str]

    # ------------------------------------------------------------------
    # 2. Material requirements  (Agent 2: Material Requirement)
    #    Each dict represents a MaterialRequirement (Pydantic model later).
    # ------------------------------------------------------------------
    materials: Annotated[list[dict], operator.add]

    # ------------------------------------------------------------------
    # 3. Candidate sources  (Agent 3: Source Discovery)
    #    Each dict represents a CandidateSource (Pydantic model later).
    # ------------------------------------------------------------------
    sources: Annotated[list[dict], operator.add]

    # ------------------------------------------------------------------
    # 4. Logistics routes  (Agent 4: Geospatial & Logistics)
    #    Each dict represents a LogisticsRoute (Pydantic model later).
    # ------------------------------------------------------------------
    routes: Annotated[list[dict], operator.add]

    # ------------------------------------------------------------------
    # 5. Cost estimates  (Agent 5: Cost)
    #    Each dict represents a CostEstimate (Pydantic model later).
    # ------------------------------------------------------------------
    cost_estimates: Annotated[list[dict], operator.add]

    # ------------------------------------------------------------------
    # 6. Environmental assessments  (Agent 6: Environmental)
    #    Each dict represents an EnvironmentalAssessment (Pydantic later).
    # ------------------------------------------------------------------
    environmental_assessments: Annotated[list[dict], operator.add]

    # ------------------------------------------------------------------
    # 7. Resilience assessments  (Agent 7: Resilience)
    #    Each dict represents a ResilienceAssessment (Pydantic later).
    # ------------------------------------------------------------------
    resilience_assessments: Annotated[list[dict], operator.add]

    # ------------------------------------------------------------------
    # 8. Decision results  (Agent 8: Decision)
    #    A single dict representing the DecisionResult (Pydantic later).
    # ------------------------------------------------------------------
    decision_results: Optional[dict]

    # ------------------------------------------------------------------
    # 9. Workflow metadata  (written by all agents)
    # ------------------------------------------------------------------
    messages: Annotated[list[str], operator.add]          # status log
    errors: Annotated[list[str], operator.add]            # non-fatal errors
    current_agent: Optional[str]                          # currently executing
    completed_agents: Annotated[list[str], operator.add]  # finished agents

