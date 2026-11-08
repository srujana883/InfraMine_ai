"""
InfraMiner AI - Production Live Multi-Agent Pipeline Runner

Executes the frozen 4-agent sequential workflow on live in-memory state:
  Agent 1 (Project & Material Intelligence)
    -> Agent 2 (Source & Logistics)
    -> Agent 3 (Cost, Environment & Resilience)
    -> Agent 4 (Decision AHP-TOPSIS)

No intermediate saved JSON files are required or read to run downstream agents.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Optional

from src.state import InfraMinerState
from agents.project_intelligence import run_project_intelligence
from agents.source_logistics import run_source_logistics
from agents.cost_environment_resilience import run_cost_environment_resilience
from agents.decision import run_decision


def merge_agent_output(state: dict, result: dict) -> None:
    """Merge an agent's partial output dict into the cumulative pipeline state.

    Appends to list fields (messages, completed_agents, errors) and updates
    scalar / object fields directly in the shared live state.
    """
    for list_key in ["messages", "completed_agents", "errors"]:
        if list_key in result and result[list_key]:
            state.setdefault(list_key, []).extend(result[list_key])

    for k, v in result.items():
        if k not in ["messages", "completed_agents", "errors"]:
            state[k] = v


def run_live_pipeline(
    project_document_path: str | Path | None = None,
    save_output: bool = True,
    output_path: str | Path | None = None,
    progress_callback: Optional[Callable[[str, str, dict], None]] = None,
) -> InfraMinerState:
    """Execute the complete 4-agent multi-agent pipeline live in-memory.

    Parameters
    ----------
    project_document_path : str | Path | None
        Path to the project DPR document (PDF). Defaults to Vadhavan DPR if None.
    save_output : bool
        Whether to save the final state to disk for debugging/audit purposes.
        Intermediate saved JSON files are NEVER required for execution.
    output_path : str | Path | None
        Path to save final execution state if save_output is True.
    progress_callback : Optional[Callable[[str, str, dict], None]]
        Optional callback called before and after each agent step with:
        (agent_key: str, status: str, details: dict).
        Statuses: 'running', 'completed', 'failed'.

    Returns
    -------
    InfraMinerState
        The final comprehensive state containing project intelligence,
        material requirements, source logistics, cost/env/resilience assessments,
        and multi-criteria decision results.
    """
    # 1. Document validation & indexing check
    if project_document_path is not None:
        doc_file = Path(project_document_path).resolve()
        if not doc_file.exists():
            raise FileNotFoundError(f"Project document not found: {doc_file}")
    else:
        doc_file = Path("documents/raw/Vadhavan-DPR_May-2023.pdf").resolve()

    index_file = Path("data/document_index/pdf_pages.json").resolve()
    if not index_file.exists():
        from src.utils.document_index import build_document_index
        build_document_index(raw_documents_dir=doc_file.parent, index_file=index_file)

    # 2. Fresh initial state (no saved JSON loaded)
    state: InfraMinerState = {
        "messages": [],
        "completed_agents": [],
        "errors": [],
    }

    # 3. Stage 1: Agent 1 - Project & Material Intelligence
    if progress_callback:
        progress_callback("agent1", "running", {"message": "Extracting project intelligence and material requirements from DPR..."})
    res1 = run_project_intelligence(state)
    merge_agent_output(state, res1)

    if res1.get("errors") or "project_material_intelligence" not in state.get("completed_agents", []):
        if progress_callback:
            progress_callback("agent1", "failed", {"errors": res1.get("errors", ["Agent 1 failed"])})
        if save_output:
            _save_state(state, output_path)
        return state

    if progress_callback:
        progress_callback(
            "agent1",
            "completed",
            {
                "message": f"Identified {len(state.get('materials', []))} material requirement(s)",
                "materials_count": len(state.get("materials", [])),
                "project_name": state.get("project_name"),
            },
        )

    # 4. Stage 2: Agent 2 - Source & Logistics
    if progress_callback:
        progress_callback("agent2", "running", {"message": "Discovering candidate sources and evaluating logistics routes..."})
    res2 = run_source_logistics(state)
    merge_agent_output(state, res2)

    if res2.get("errors") or "source_logistics" not in state.get("completed_agents", []):
        if progress_callback:
            progress_callback("agent2", "failed", {"errors": res2.get("errors", ["Agent 2 failed"])})
        if save_output:
            _save_state(state, output_path)
        return state

    if progress_callback:
        progress_callback(
            "agent2",
            "completed",
            {
                "message": f"Matched {len(state.get('sources', []))} sources and {len(state.get('routes', []))} routes",
                "sources_count": len(state.get("sources", [])),
                "routes_count": len(state.get("routes", [])),
            },
        )

    # 5. Stage 3: Agent 3 - Cost, Environment & Resilience
    if progress_callback:
        progress_callback("agent3", "running", {"message": "Computing costs, environmental impacts, and resilience risks..."})
    res3 = run_cost_environment_resilience(state)
    merge_agent_output(state, res3)

    if res3.get("errors") or "cost_environment_resilience" not in state.get("completed_agents", []):
        if progress_callback:
            progress_callback("agent3", "failed", {"errors": res3.get("errors", ["Agent 3 failed"])})
        if save_output:
            _save_state(state, output_path)
        return state

    if progress_callback:
        progress_callback(
            "agent3",
            "completed",
            {
                "message": f"Computed {len(state.get('cost_estimates', []))} cost, environmental, and resilience assessments",
                "cost_count": len(state.get("cost_estimates", [])),
                "env_count": len(state.get("environmental_assessments", [])),
                "res_count": len(state.get("resilience_assessments", [])),
            },
        )

    # 6. Stage 4: Agent 4 - Decision (AHP-TOPSIS)
    if progress_callback:
        progress_callback("agent4", "running", {"message": "Executing AHP criteria weighting and TOPSIS multi-criteria ranking..."})
    res4 = run_decision(state)
    merge_agent_output(state, res4)

    if res4.get("errors") or "decision" not in state.get("completed_agents", []):
        if progress_callback:
            progress_callback("agent4", "failed", {"errors": res4.get("errors", ["Agent 4 failed"])})
        if save_output:
            _save_state(state, output_path)
        return state

    dec_res = state.get("decision_results", {})
    if progress_callback:
        progress_callback(
            "agent4",
            "completed",
            {
                "message": f"Ranked {len(dec_res.get('ranking', []))} unique alternatives (CR={dec_res.get('ahp', {}).get('consistency_ratio', 0.0):.4f})",
                "ranking_count": len(dec_res.get("ranking", [])),
                "cr": dec_res.get("ahp", {}).get("consistency_ratio", 0.0),
            },
        )

    # 7. Audit log save (optional, never read by pipeline)
    if save_output:
        _save_state(state, output_path)

    return state


def _save_state(state: InfraMinerState, output_path: str | Path | None = None) -> Path:
    """Save execution output for audit/debugging purposes only."""
    out_file = Path(output_path) if output_path else Path("data/outputs/live_pipeline_output.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)
    return out_file

