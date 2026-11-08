"""
InfraMiner AI - Production Live Multi-Agent Execution CLI

Executes the complete 4-agent pipeline sequentially in memory:
  Agent 1 (Project & Material Intelligence)
    -> Agent 2 (Source & Logistics)
    -> Agent 3 (Cost, Environment & Resilience)
    -> Agent 4 (Decision AHP-TOPSIS)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_live_pipeline


def print_pipeline_summary(state: dict) -> None:
    """Print structured summary of live pipeline execution."""
    print("\n" + "=" * 70)
    print("           INFRAMINER AI — LIVE PIPELINE EXECUTION SUMMARY")
    print("=" * 70)

    print(f"\nProject Name              : {state.get('project_name')}")
    print(f"Project Type              : {state.get('project_type')}")
    print(f"Materials Extracted       : {len(state.get('materials', []))}")
    print(f"Candidate Sources Matched : {len(state.get('sources', []))}")
    print(f"Logistics Routes Evaluated: {len(state.get('routes', []))}")
    print(f"Cost Estimates Computed   : {len(state.get('cost_estimates', []))}")
    print(f"Environmental Assessments : {len(state.get('environmental_assessments', []))}")
    print(f"Resilience Assessments    : {len(state.get('resilience_assessments', []))}")

    dec_res = state.get("decision_results", {})
    ranking = dec_res.get("ranking", [])
    ahp = dec_res.get("ahp", {})
    primary = dec_res.get("primary_recommendation", {})

    print(f"Decision Alternatives     : {len(ranking)}")
    print(f"AHP Consistency Ratio (CR): {ahp.get('consistency_ratio', 'N/A')}")
    print(f"Primary Recommendation    : {primary.get('source_name', 'N/A')} ({primary.get('source_id', 'N/A')})")
    print(f"Completed Agents          : {' -> '.join(state.get('completed_agents', []))}")

    sourcing_plan = dec_res.get("final_sourcing_plan", [])
    if sourcing_plan:
        print("\nFinal Sourcing Plan by Material:")
        for plan in sourcing_plan:
            p = plan.get("primary_source", {})
            fbs = [fb.get("source_name") for fb in plan.get("fallback_sources", [])]
            fb_str = ", ".join(fbs) if fbs else "None"
            score = p.get("closeness_coefficient", 0.0)
            print(f"  * {plan.get('material_name')}: Primary={p.get('source_name')} (Score: {score:.4f}) | Fallbacks={fb_str}")

    errors = state.get("errors", [])
    if errors:
        print("\nPipeline Errors:")
        for err in errors:
            print(f"  ! {err}")
    else:
        print("\nPipeline Status: COMPLETED SUCCESSFULLY (0 errors)")
    print("=" * 70 + "\n")


def main():
    doc_path = sys.argv[1] if len(sys.argv) > 1 else "documents/raw/Vadhavan-DPR_May-2023.pdf"
    print(f"Starting InfraMiner AI live pipeline with document: {doc_path}")
    final_state = run_live_pipeline(project_document_path=doc_path)
    print_pipeline_summary(final_state)


if __name__ == "__main__":
    main()