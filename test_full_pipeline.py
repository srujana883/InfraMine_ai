"""
InfraMiner AI - Full 4-Agent Pipeline Integration Test

Executes the complete multi-agent pipeline sequentially:
  DPR Retrieval
    -> Agent 1: Project & Material Intelligence (LLM)
    -> Agent 2: Source & Logistics (Deterministic)
    -> Agent 3: Cost, Environment & Resilience (Deterministic)
    -> Agent 4: Decision (AHP-TOPSIS, Deterministic)

Verifies:
  - Inter-agent state transition and field propagation
  - Shared state schema compliance (InfraMinerState)
  - Mathematical integrity of multi-criteria decision
  - Preservation of data provenance and assumption tags
  - Production of complete material sourcing and fallback plans
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

passed = 0
failed = 0


def report(name: str, ok: bool, detail: str = ""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} -- {detail}")


def merge_agent_output(state: dict, result: dict) -> None:
    """Merge an agent's partial output dict into the cumulative pipeline state."""
    # List fields that append in shared state
    for list_key in ["messages", "completed_agents", "errors"]:
        if list_key in result:
            state.setdefault(list_key, []).extend(result[list_key])

    # Scalar / object fields that overwrite or set
    for k, v in result.items():
        if k not in ["messages", "completed_agents", "errors"]:
            state[k] = v


print("=" * 70)
print("INFRAMINER AI - FULL 4-AGENT PIPELINE INTEGRATION TEST")
print("=" * 70)

# ===================================================================
# 1. IMPORT CHECK
# ===================================================================
print("\n[1] Importing All 4 Agents and Shared State")

try:
    from src.state import InfraMinerState
    from agents.project_intelligence import run_project_intelligence
    from agents.source_logistics import run_source_logistics
    from agents.cost_environment_resilience import run_cost_environment_resilience
    from agents.decision import run_decision
    report("Import all agent nodes and state schema", True)
except Exception as e:
    report("Import all agent nodes and state schema", False, str(e))
    sys.exit(1)


# Initialize shared pipeline state
pipeline_state: InfraMinerState = {}


# ===================================================================
# 2. STAGE 1: AGENT 1 - PROJECT & MATERIAL INTELLIGENCE
# ===================================================================
print("\n[2] Executing Agent 1: Project & Material Intelligence")

try:
    res1 = run_project_intelligence(pipeline_state)
    assert not res1.get("errors"), f"Agent 1 returned errors: {res1.get('errors')}"
    merge_agent_output(pipeline_state, res1)

    # Validate Project Information
    assert isinstance(pipeline_state.get("project_name"), str) and len(pipeline_state["project_name"]) > 0
    report(f"Agent 1: project_name = '{pipeline_state['project_name']}'", True)

    assert isinstance(pipeline_state.get("project_type"), str) and len(pipeline_state["project_type"]) > 0
    report(f"Agent 1: project_type = '{pipeline_state['project_type']}'", True)

    loc = pipeline_state.get("project_location")
    assert isinstance(loc, dict) and "lat" in loc and "lng" in loc
    report(f"Agent 1: project_location structure valid ({loc})", True)

    assert isinstance(pipeline_state.get("project_scope"), str) and len(pipeline_state["project_scope"]) > 20
    report("Agent 1: project_scope extracted successfully", True)

    constraints = pipeline_state.get("project_constraints")
    assert isinstance(constraints, list) and len(constraints) > 0
    report(f"Agent 1: project_constraints extracted ({len(constraints)} items)", True)

    timeline = pipeline_state.get("project_timeline")
    assert isinstance(timeline, str) and len(timeline) > 0
    report("Agent 1: project_timeline extracted successfully", True)

    # Validate Material Requirements
    materials = pipeline_state.get("materials")
    assert isinstance(materials, list) and len(materials) > 0
    report(f"Agent 1: materials extracted ({len(materials)} requirements)", True)

    # Check state tracking
    assert pipeline_state.get("current_agent") == "project_material_intelligence"
    assert "project_material_intelligence" in pipeline_state.get("completed_agents", [])
    report("Agent 1: State tracking and completed_agents verified", True)

except Exception as e:
    report("Agent 1 execution", False, str(e))


# ===================================================================
# 3. STAGE 2: AGENT 2 - SOURCE & LOGISTICS
# ===================================================================
print("\n[3] Executing Agent 2: Source & Logistics")

try:
    res2 = run_source_logistics(pipeline_state)
    assert not res2.get("errors"), f"Agent 2 returned errors: {res2.get('errors')}"
    merge_agent_output(pipeline_state, res2)

    sources = pipeline_state.get("sources")
    assert isinstance(sources, list) and len(sources) > 0
    report(f"Agent 2: Candidate sources discovered ({len(sources)} sources)", True)

    routes = pipeline_state.get("routes")
    assert isinstance(routes, list) and len(routes) > 0
    report(f"Agent 2: Logistics routes calculated ({len(routes)} routes)", True)

    # Verify route linkage
    source_ids = {s["source_id"] for s in sources}
    route_sids = {r["source_id"] for r in routes}
    assert source_ids == route_sids, "Mismatch between source IDs and route IDs"
    report("Agent 2: 1-to-1 linkage between sources and logistics routes", True)

    # Check state tracking
    assert pipeline_state.get("current_agent") == "source_logistics"
    assert "source_logistics" in pipeline_state.get("completed_agents", [])
    report("Agent 2: State tracking and completed_agents verified", True)

except Exception as e:
    report("Agent 2 execution", False, str(e))


# ===================================================================
# 4. STAGE 3: AGENT 3 - COST, ENVIRONMENT & RESILIENCE
# ===================================================================
print("\n[4] Executing Agent 3: Cost, Environment & Resilience")

try:
    res3 = run_cost_environment_resilience(pipeline_state)
    assert not res3.get("errors"), f"Agent 3 returned errors: {res3.get('errors')}"
    merge_agent_output(pipeline_state, res3)

    cost_ests = pipeline_state.get("cost_estimates")
    assert isinstance(cost_ests, list) and len(cost_ests) == len(sources)
    report(f"Agent 3: Cost estimates computed ({len(cost_ests)} estimates)", True)

    env_assess = pipeline_state.get("environmental_assessments")
    assert isinstance(env_assess, list) and len(env_assess) == len(sources)
    report(f"Agent 3: Environmental assessments computed ({len(env_assess)} assessments)", True)

    res_assess = pipeline_state.get("resilience_assessments")
    assert isinstance(res_assess, list) and len(res_assess) == len(sources)
    report(f"Agent 3: Resilience assessments computed ({len(res_assess)} assessments)", True)

    # Verify data provenance preservation
    has_demo_tags = all(
        c.get("cost_data_type") in (
            "assumption", "demonstration", "document_evidence",
            "unavailable", "calculated", "verified_document",
        )
        for c in cost_ests
    )
    assert has_demo_tags, "Missing provenance/assumption tag in cost estimates"
    report("Agent 3: Provenance/assumption data tags properly preserved", True)

    # Check state tracking
    assert pipeline_state.get("current_agent") == "cost_environment_resilience"
    assert "cost_environment_resilience" in pipeline_state.get("completed_agents", [])
    report("Agent 3: State tracking and completed_agents verified", True)

except Exception as e:
    report("Agent 3 execution", False, str(e))


# ===================================================================
# 5. STAGE 4: AGENT 4 - DECISION (AHP-TOPSIS)
# ===================================================================
print("\n[5] Executing Agent 4: Decision (AHP-TOPSIS)")

try:
    res4 = run_decision(pipeline_state)
    assert not res4.get("errors"), f"Agent 4 returned errors: {res4.get('errors')}"
    merge_agent_output(pipeline_state, res4)

    dec_res = pipeline_state.get("decision_results")
    assert isinstance(dec_res, dict), "decision_results missing or not a dict"
    report("Agent 4: decision_results produced in shared state", True)

    # Validate AHP
    ahp = dec_res.get("ahp", {})
    assert "weights" in ahp and len(ahp["weights"]) == 4
    assert ahp.get("is_consistent") is True
    assert ahp.get("consistency_ratio", 1.0) < 0.10
    report(f"Agent 4: AHP consistent (CR = {ahp['consistency_ratio']:.4f} < 0.10)", True)

    # Validate TOPSIS Ranking
    ranking = dec_res.get("ranking", [])
    assert isinstance(ranking, list) and len(ranking) > 0
    # Check ranking order
    for idx in range(len(ranking) - 1):
        assert ranking[idx]["closeness_coefficient"] >= ranking[idx + 1]["closeness_coefficient"]
    report(f"Agent 4: TOPSIS ranking verified ({len(ranking)} alternatives ranked)", True)

    # Validate Primary Recommendation
    primary = dec_res.get("primary_recommendation")
    assert primary is not None and "source_name" in primary
    report(f"Agent 4: Primary recommendation = '{primary['source_name']}' (Closeness: {primary['closeness_coefficient']:.4f})", True)

    # Validate Final Sourcing Plan by Material
    sourcing_plan = dec_res.get("final_sourcing_plan", [])
    assert isinstance(sourcing_plan, list) and len(sourcing_plan) > 0
    report(f"Agent 4: Final sourcing plan produced for {len(sourcing_plan)} material(s)", True)

    # Validate Fallback Alternatives
    fallbacks = dec_res.get("fallback_alternatives", [])
    assert isinstance(fallbacks, list)
    viable_fbs = [f for f in fallbacks if f.get("is_viable_fallback")]
    report(f"Agent 4: Fallback alternatives identified ({len(viable_fbs)} viable fallbacks)", True)

    # Validate Resilience Narrative
    res_expl = dec_res.get("resilience_explanation")
    assert isinstance(res_expl, str) and len(res_expl) > 50
    report("Agent 4: Resilience and fallback explanation narrative verified", True)

    # Check state tracking
    assert pipeline_state.get("current_agent") == "decision"
    assert "decision" in pipeline_state.get("completed_agents", [])
    report("Agent 4: State tracking and completed_agents verified", True)

except Exception as e:
    report("Agent 4 execution", False, str(e))


# ===================================================================
# 6. PIPELINE-WIDE INTEGRITY AND AUDIT CHECKS
# ===================================================================
print("\n[6] Pipeline-Wide Integrity Checks")

try:
    completed = pipeline_state.get("completed_agents", [])
    expected_agents = [
        "project_material_intelligence",
        "source_logistics",
        "cost_environment_resilience",
        "decision",
    ]
    assert completed == expected_agents, f"Expected {expected_agents}, got {completed}"
    report("All 4 agents completed in exact sequential order", True)

    messages = pipeline_state.get("messages", [])
    assert len(messages) >= 4, f"Expected at least 4 status messages, got {len(messages)}"
    report(f"Execution log complete ({len(messages)} pipeline messages recorded)", True)

    errors = pipeline_state.get("errors", [])
    assert len(errors) == 0, f"Unexpected pipeline errors recorded: {errors}"
    report("Zero errors encountered across entire pipeline", True)

    # Check that decision was computed dynamically, not hardcoded
    # Verify primary recommendation matches top of ranking
    assert primary["source_id"] == ranking[0]["source_id"]
    report("Dynamic consistency: Primary recommendation matches top TOPSIS alternative", True)

    # Save complete pipeline output artifact
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    full_output_file = out_dir / "full_pipeline_output.json"
    with full_output_file.open("w", encoding="utf-8") as f:
        json.dump(pipeline_state, f, indent=2, ensure_ascii=False, default=str)
    report(f"Complete pipeline state saved to {full_output_file}", True)

except Exception as e:
    report("Pipeline integrity checks", False, str(e))


# ===================================================================
# SUMMARY EXECUTION REPORT
# ===================================================================
print("\n" + "=" * 70)
print("FULL PIPELINE INTEGRATION EXECUTION SUMMARY")
print("=" * 70)
print(f"Project Name              : {pipeline_state.get('project_name')}")
print(f"Project Type              : {pipeline_state.get('project_type')}")
print(f"Materials Extracted       : {len(pipeline_state.get('materials', []))}")
print(f"Candidate Sources Matched : {len(pipeline_state.get('sources', []))}")
print(f"Logistics Routes Evaluated: {len(pipeline_state.get('routes', []))}")
print(f"Cost Estimates Computed   : {len(pipeline_state.get('cost_estimates', []))}")
print(f"Environmental Assessments : {len(pipeline_state.get('environmental_assessments', []))}")
print(f"Resilience Assessments    : {len(pipeline_state.get('resilience_assessments', []))}")
print(f"Decision Alternatives     : {len(pipeline_state.get('decision_results', {}).get('ranking', []))}")
print(f"AHP Consistency Ratio (CR): {pipeline_state.get('decision_results', {}).get('ahp', {}).get('consistency_ratio')}")
print(f"Primary Recommendation    : {pipeline_state.get('decision_results', {}).get('primary_recommendation', {}).get('source_name')}")
print(f"Completed Agents          : {' -> '.join(pipeline_state.get('completed_agents', []))}")

print("\nFinal Sourcing Plan by Material:")
for plan in pipeline_state.get('decision_results', {}).get('final_sourcing_plan', []):
    p = plan['primary_source']
    fbs = [fb['source_name'] for fb in plan.get('fallback_sources', [])]
    fb_str = ', '.join(fbs) if fbs else 'None'
    print(f"  * {plan['material_name']}: Primary={p['source_name']} (Closeness: {p['closeness_coefficient']:.4f}) | Fallback={fb_str}")

print("\n" + "=" * 70)
total = passed + failed
print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
if failed == 0:
    print("FULL PIPELINE INTEGRATION TEST PASSED SUCCESSFULLY")
else:
    print("FULL PIPELINE INTEGRATION TEST ENCOUNTERED FAILURES")
print("=" * 70)

