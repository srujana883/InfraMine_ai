"""
InfraMiner AI - Live Multi-Agent Pipeline Test

Verifies the true live end-to-end execution path:
  Document (PDF) -> Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 -> Final Decision

Executes all 4 agents live sequentially on shared in-memory state.
Intermediate saved JSON files are NOT loaded or used to advance the pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run_live_pipeline

passed = 0
failed = 0


def report(name: str, ok: bool, detail: str = "") -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} -- {detail}")


def main():
    print("=" * 70)
    print("INFRAMINER AI - LIVE MULTI-AGENT PIPELINE TEST")
    print("=" * 70)

    test_doc = "documents/raw/Vadhavan-DPR_May-2023.pdf"
    print(f"\n[1] Starting live pipeline execution with test document:")
    print(f"    {test_doc}")
    print("    Running Agent 1 -> Agent 2 -> Agent 3 -> Agent 4 live in memory...\n")

    try:
        final_state = run_live_pipeline(
            project_document_path=test_doc,
            save_output=True,
            output_path="data/outputs/live_pipeline_test_output.json",
        )
    except Exception as exc:
        print(f"\nFATAL: run_live_pipeline raised an unhandled exception: {exc}")
        sys.exit(1)

    print("\n" + "=" * 70)
    print("VERIFYING LIVE EXECUTION RESULTS")
    print("=" * 70)

    # 1. Pipeline Errors Check
    errors = final_state.get("errors", [])
    report("Zero errors encountered across entire live pipeline", len(errors) == 0, f"Errors: {errors}")

    # 2. Agent 1 Verification
    p_name = final_state.get("project_name")
    report("Agent 1: project_name populated", bool(p_name), f"got: {p_name}")

    p_type = final_state.get("project_type")
    report("Agent 1: project_type populated", bool(p_type), f"got: {p_type}")

    materials = final_state.get("materials", [])
    report("Agent 1: materials list populated", isinstance(materials, list) and len(materials) > 0, f"count: {len(materials)}")

    # 3. Agent 2 Verification
    sources = final_state.get("sources", [])
    report("Agent 2: candidate sources matched", isinstance(sources, list) and len(sources) > 0, f"count: {len(sources)}")

    routes = final_state.get("routes", [])
    report("Agent 2: logistics routes calculated", isinstance(routes, list) and len(routes) == len(sources), f"routes={len(routes)}, sources={len(sources)}")

    # 4. Agent 3 Verification
    cost_ests = final_state.get("cost_estimates", [])
    report("Agent 3: cost estimates computed", isinstance(cost_ests, list) and len(cost_ests) == len(sources), f"count: {len(cost_ests)}")

    env_assess = final_state.get("environmental_assessments", [])
    report("Agent 3: environmental assessments computed", isinstance(env_assess, list) and len(env_assess) == len(sources), f"count: {len(env_assess)}")

    res_assess = final_state.get("resilience_assessments", [])
    report("Agent 3: resilience assessments computed", isinstance(res_assess, list) and len(res_assess) == len(sources), f"count: {len(res_assess)}")

    # 5. Agent 4 Verification
    dec_res = final_state.get("decision_results", {})
    report("Agent 4: decision_results structure generated", isinstance(dec_res, dict) and bool(dec_res))

    ahp = dec_res.get("ahp", {})
    cr = ahp.get("consistency_ratio", 1.0)
    report("Agent 4: AHP consistency ratio verified (< 0.10)", cr < 0.10, f"CR = {cr}")

    ranking = dec_res.get("ranking", [])
    report("Agent 4: TOPSIS ranking populated", isinstance(ranking, list) and len(ranking) > 0, f"count: {len(ranking)}")

    primary = dec_res.get("primary_recommendation", {})
    report("Agent 4: Primary recommendation generated", bool(primary and primary.get("source_name")), f"primary: {primary.get('source_name')}")

    sourcing_plan = dec_res.get("final_sourcing_plan", [])
    report("Agent 4: Final sourcing plan produced", isinstance(sourcing_plan, list) and len(sourcing_plan) > 0, f"count: {len(sourcing_plan)}")

    # 6. Workflow Sequential Integrity
    completed = final_state.get("completed_agents", [])
    expected = [
        "project_material_intelligence",
        "source_logistics",
        "cost_environment_resilience",
        "decision",
    ]
    report("Sequential workflow: All 4 agents executed in exact order", completed == expected, f"completed: {completed}")

    # Summary
    print("\n" + "=" * 70)
    print("LIVE PIPELINE SUMMARY")
    print("=" * 70)
    print(f"Project Name              : {p_name}")
    print(f"Project Type              : {p_type}")
    print(f"Materials Extracted       : {len(materials)}")
    print(f"Candidate Sources Matched : {len(sources)}")
    print(f"Logistics Routes Evaluated: {len(routes)}")
    print(f"Cost Estimates Computed   : {len(cost_ests)}")
    print(f"Environmental Assessments : {len(env_assess)}")
    print(f"Resilience Assessments    : {len(res_assess)}")
    print(f"Decision Alternatives     : {len(ranking)}")
    print(f"AHP Consistency Ratio (CR): {cr:.4f}")
    print(f"Primary Recommendation    : {primary.get('source_name')} ({primary.get('source_id')})")
    print(f"Completed Agents          : {' -> '.join(completed)}")

    print("\n" + "=" * 70)
    total = passed + failed
    print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
    if failed == 0:
        print("LIVE MULTI-AGENT PIPELINE TEST PASSED SUCCESSFULLY")
    else:
        print("LIVE MULTI-AGENT PIPELINE TEST ENCOUNTERED FAILURES")
    print("=" * 70)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

