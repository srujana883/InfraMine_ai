"""
InfraMiner AI - Agent 3: Cost, Environment & Resilience
Complete Validation Suite (no LLM required)
"""

import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

passed = 0
failed = 0


def report(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} -- {detail}")


print("=" * 70)
print("AGENT 3 - COST, ENVIRONMENT & RESILIENCE - VALIDATION")
print("=" * 70)


# ===================================================================
# 1. SYNTAX / IMPORT
# ===================================================================
print("\n[1] Syntax and Import")

try:
    from agents.cost_environment_resilience import (
        load_cost_data,
        load_environmental_data,
        load_disruption_scenarios,
        calculate_cost_estimate,
        calculate_environmental_assessment,
        calculate_resilience_assessment,
        run_cost_environment_resilience,
        _match_cost_category,
        _get_transport_rate,
        _find_material_quantity,
        _count_alternatives,
        _find_applicable_scenarios,
    )
    report("Import all Agent 3 symbols", True)
except Exception as e:
    report("Import all Agent 3 symbols", False, str(e))

try:
    from src.state import InfraMinerState
    report("Import InfraMinerState", True)
except Exception as e:
    report("Import InfraMinerState", False, str(e))


# ===================================================================
# 2. COST DATASET LOADING
# ===================================================================
print("\n[2] Cost Dataset Loading")

try:
    cost_data = load_cost_data()
    assert len(cost_data) >= 5, f"Only {len(cost_data)} categories"
    report(f"Loaded {len(cost_data)} cost categories", True)
except Exception as e:
    report("Load cost data", False, str(e))

try:
    assert "rock/stone" in cost_data
    assert "cement" in cost_data
    assert "fill material" in cost_data
    report("Expected categories present", True)
except Exception as e:
    report("Expected categories present", False, str(e))

try:
    rock = cost_data["rock/stone"]
    assert rock["unit_cost"] is not None and rock["unit_cost"] > 0
    assert rock["transport_rate_road"] is not None and rock["transport_rate_road"] > 0
    assert rock["data_type"] == "assumption"
    report("Cost entry structure valid", True)
except Exception as e:
    report("Cost entry structure valid", False, str(e))


# ===================================================================
# 3. COST SCHEMA
# ===================================================================
print("\n[3] Cost Category Matching")

try:
    assert _match_cost_category("Rock/Stone for breakwater", cost_data) == "rock/stone"
    assert _match_cost_category("Fill material for reclamation", cost_data) == "fill material"
    assert _match_cost_category("Cement", cost_data) == "cement"
    assert _match_cost_category("Steel Reinforcement", cost_data) == "steel"
    report("Cost category matching", True)
except Exception as e:
    report("Cost category matching", False, str(e))

try:
    assert _match_cost_category("Nonexistent Material XYZ", cost_data) is None
    report("Unmatched material returns None", True)
except Exception as e:
    report("Unmatched material returns None", False, str(e))


# ===================================================================
# 4. MATERIAL COST CALCULATION
# ===================================================================
print("\n[4] Material Cost Calculation")

test_source = {
    "source_id": "T1", "source_name": "Test Quarry",
    "source_type": "quarry", "material_name": "Rock/Stone",
    "data_type": "demonstration",
}
test_route = {
    "source_id": "T1", "distance_km": 85.0, "transport_mode": "road",
}

try:
    # quantity=1000, rock unit_cost=450 => material_cost=450000
    est = calculate_cost_estimate(test_source, test_route, 1000.0, cost_data)
    assert est["material_cost"] == 1000.0 * cost_data["rock/stone"]["unit_cost"]
    report(f"Material cost = qty * unit_cost ({est['material_cost']})", True)
except Exception as e:
    report("Material cost calculation", False, str(e))


# ===================================================================
# 5. TRANSPORTATION COST CALCULATION
# ===================================================================
print("\n[5] Transportation Cost Calculation")

try:
    # qty=1000, dist=85, road_rate=4.5 => transport=1000*85*4.5=382500
    rate = cost_data["rock/stone"]["transport_rate_road"]
    expected_transport = 1000.0 * 85.0 * rate
    assert est["transportation_cost"] == expected_transport
    report(f"Transport cost = qty * dist * rate ({est['transportation_cost']})", True)
except Exception as e:
    report("Transportation cost calculation", False, str(e))


# ===================================================================
# 6. TOTAL COST CALCULATION
# ===================================================================
print("\n[6] Total Cost Calculation")

try:
    expected_total = est["material_cost"] + est["transportation_cost"]
    assert est["total_cost"] == expected_total
    report(f"Total cost = material + transport ({est['total_cost']})", True)
except Exception as e:
    report("Total cost calculation", False, str(e))

try:
    assert est["cost_data_type"] == "assumption"
    assert est["cost_currency"] == "INR"
    report("Cost provenance preserved", True)
except Exception as e:
    report("Cost provenance preserved", False, str(e))


# ===================================================================
# 7. MISSING COST DATA HANDLING
# ===================================================================
print("\n[7] Missing Cost Data Handling")

try:
    # Missing quantity
    est_noqty = calculate_cost_estimate(test_source, test_route, None, cost_data)
    assert est_noqty["material_cost"] is None
    assert est_noqty["transportation_cost"] is None
    assert est_noqty["calculation_notes"] is not None
    report("Missing quantity handled", True)
except Exception as e:
    report("Missing quantity handled", False, str(e))

try:
    # Missing distance
    route_nodist = {"source_id": "T1", "distance_km": None, "transport_mode": "road"}
    est_nodist = calculate_cost_estimate(test_source, route_nodist, 1000.0, cost_data)
    assert est_nodist["material_cost"] is not None  # material cost still works
    assert est_nodist["transportation_cost"] is None
    report("Missing distance handled", True)
except Exception as e:
    report("Missing distance handled", False, str(e))

try:
    # Unknown material
    unk_source = {**test_source, "material_name": "Unobtainium"}
    est_unk = calculate_cost_estimate(unk_source, test_route, 1000.0, cost_data)
    assert est_unk["material_cost"] is None
    assert est_unk["transportation_cost"] is None
    assert est_unk["cost_data_type"] == "unavailable"
    report("Unknown material handled", True)
except Exception as e:
    report("Unknown material handled", False, str(e))

try:
    # Empty cost data
    est_empty = calculate_cost_estimate(test_source, test_route, 1000.0, {})
    assert est_empty["material_cost"] is None
    report("Empty cost data handled", True)
except Exception as e:
    report("Empty cost data handled", False, str(e))


# ===================================================================
# 8. ENVIRONMENTAL DATASET LOADING
# ===================================================================
print("\n[8] Environmental Dataset Loading")

try:
    src_factors, trn_factors = load_environmental_data()
    assert len(src_factors) >= 2, f"Only {len(src_factors)} source types"
    assert len(trn_factors) >= 2, f"Only {len(trn_factors)} transport modes"
    report(f"Loaded {len(src_factors)} source types, {len(trn_factors)} transport modes", True)
except Exception as e:
    report("Load environmental data", False, str(e))

try:
    assert "quarry" in src_factors
    assert "road" in trn_factors
    report("Expected environmental categories present", True)
except Exception as e:
    report("Expected environmental categories present", False, str(e))


# ===================================================================
# 9. ENVIRONMENTAL ASSESSMENT
# ===================================================================
print("\n[9] Environmental Assessment")

try:
    env = calculate_environmental_assessment(
        test_source, test_route, src_factors, trn_factors
    )
    assert 0 <= env["source_impact_score"] <= 1
    assert 0 <= env["transport_impact_score"] <= 1
    assert 0 <= env["combined_impact_score"] <= 1
    assert env["impact_category"] in ("low", "medium", "high")
    assert env["regulatory_sensitivity"] in ("low", "medium", "high")
    report(f"Environmental score: {env['combined_impact_score']} ({env['impact_category']})", True)
except Exception as e:
    report("Environmental assessment", False, str(e))

try:
    # Marine source should have higher water impact
    marine_source = {**test_source, "source_type": "marine_borrow"}
    marine_route = {**test_route, "transport_mode": "marine"}
    env_marine = calculate_environmental_assessment(
        marine_source, marine_route, src_factors, trn_factors
    )
    assert env_marine["source_impact_score"] != env["source_impact_score"]
    report("Different source types produce different scores", True)
except Exception as e:
    report("Different source types produce different scores", False, str(e))


# ===================================================================
# 10. MISSING ENVIRONMENTAL DATA HANDLING
# ===================================================================
print("\n[10] Missing Environmental Data Handling")

try:
    env_empty = calculate_environmental_assessment(
        {**test_source, "source_type": "unknown_type"},
        test_route, src_factors, trn_factors,
    )
    assert env_empty["source_impact_score"] == 0.5  # default
    report("Unknown source type handled (default 0.5)", True)
except Exception as e:
    report("Unknown source type handled", False, str(e))

try:
    env_empty2 = calculate_environmental_assessment(
        test_source, test_route, {}, {},
    )
    assert env_empty2["combined_impact_score"] == 0.5  # both defaults
    report("Empty environmental data handled", True)
except Exception as e:
    report("Empty environmental data handled", False, str(e))


# ===================================================================
# 11. RESILIENCE DATASET LOADING
# ===================================================================
print("\n[11] Resilience Dataset Loading")

try:
    scenarios = load_disruption_scenarios()
    assert len(scenarios) >= 5, f"Only {len(scenarios)} scenarios"
    report(f"Loaded {len(scenarios)} disruption scenarios", True)
except Exception as e:
    report("Load disruption scenarios", False, str(e))

try:
    sc = scenarios[0]
    assert "scenario_id" in sc
    assert "probability" in sc
    assert "severity" in sc
    assert isinstance(sc["affected_source_types"], list)
    assert isinstance(sc["affected_transport_modes"], list)
    report("Scenario structure valid", True)
except Exception as e:
    report("Scenario structure valid", False, str(e))


# ===================================================================
# 12. DISRUPTION SCENARIO HANDLING
# ===================================================================
print("\n[12] Disruption Scenario Handling")

try:
    applicable = _find_applicable_scenarios("quarry", "road", scenarios)
    assert len(applicable) >= 2, f"Only {len(applicable)} applicable"
    report(f"Quarry+road: {len(applicable)} applicable scenarios", True)
except Exception as e:
    report("Disruption scenario matching", False, str(e))

try:
    applicable_marine = _find_applicable_scenarios("marine_borrow", "marine", scenarios)
    assert len(applicable_marine) >= 1
    report(f"Marine: {len(applicable_marine)} applicable scenarios", True)
except Exception as e:
    report("Marine scenario matching", False, str(e))


# ===================================================================
# 13. ALTERNATIVE SOURCE / FALLBACK LOGIC
# ===================================================================
print("\n[13] Alternative Source / Fallback Logic")

test_sources = [
    {"source_id": "A", "material_name": "Rock/Stone"},
    {"source_id": "B", "material_name": "Rock/Stone"},
    {"source_id": "C", "material_name": "Rock/Stone"},
    {"source_id": "D", "material_name": "Cement"},
]

try:
    alt_a = _count_alternatives("A", "Rock/Stone", test_sources)
    assert alt_a == 2, f"Expected 2 alternatives, got {alt_a}"
    report("Count alternatives (2 for Rock A)", True)
except Exception as e:
    report("Count alternatives", False, str(e))

try:
    alt_d = _count_alternatives("D", "Cement", test_sources)
    assert alt_d == 0, f"Expected 0 alternatives, got {alt_d}"
    report("Count alternatives (0 for Cement D)", True)
except Exception as e:
    report("Count alternatives (single source)", False, str(e))


# ===================================================================
# 14. RESILIENCE ASSESSMENT
# ===================================================================
print("\n[14] Resilience Assessment")

try:
    res = calculate_resilience_assessment(
        test_source, test_route, test_sources, scenarios
    )
    assert 0 <= res["resilience_score"] <= 1
    assert res["resilience_category"] in ("low", "medium", "high")
    assert res["alternative_count"] >= 0
    assert isinstance(res["fallback_feasible"], bool)
    assert isinstance(res["applicable_scenarios"], list)
    report(f"Resilience score: {res['resilience_score']} ({res['resilience_category']})", True)
except Exception as e:
    report("Resilience assessment", False, str(e))

try:
    # Single source = higher dependency risk
    single_sources = [{"source_id": "T1", "material_name": "Rock/Stone"}]
    res_single = calculate_resilience_assessment(
        test_source, test_route, single_sources, scenarios
    )
    assert res_single["dependency_risk"] == 1.0
    assert res_single["alternative_count"] == 0
    assert res_single["fallback_feasible"] is False
    report("Single-source dependency detected", True)
except Exception as e:
    report("Single-source dependency", False, str(e))

try:
    # Planned source = higher availability risk
    planned_source = {**test_source, "operational_status": "planned"}
    res_planned = calculate_resilience_assessment(
        planned_source, test_route, test_sources, scenarios
    )
    assert res_planned["availability_risk"] == 0.5
    report("Planned source availability risk = 0.5", True)
except Exception as e:
    report("Planned source availability risk", False, str(e))


# ===================================================================
# 15. SHARED STATE INTEGRATION
# ===================================================================
print("\n[15] Shared State Integration")

try:
    state_fields = set(InfraMinerState.__annotations__.keys())
    agent3_fields = {
        "cost_estimates", "environmental_assessments",
        "resilience_assessments", "messages",
        "current_agent", "completed_agents",
    }
    missing = agent3_fields - state_fields
    assert not missing, f"Fields not in state: {missing}"
    report("All Agent 3 output fields in InfraMinerState", True)
except Exception as e:
    report("All Agent 3 output fields in InfraMinerState", False, str(e))


# ===================================================================
# 16. LANGGRAPH NODE EXECUTION
# ===================================================================
print("\n[16] LangGraph Node Execution")

try:
    test_state = {
        "materials": [
            {"material_name": "Rock/Stone", "quantity": 32100000, "unit": "tonnes"},
            {"material_name": "Cement", "quantity": None, "unit": None},
        ],
        "sources": [
            {
                "source_id": "Q1", "source_name": "Test Quarry",
                "source_type": "quarry", "material_name": "Rock/Stone",
                "operational_status": "operational", "data_type": "demonstration",
            },
            {
                "source_id": "C1", "source_name": "Test Cement",
                "source_type": "supplier", "material_name": "Cement",
                "operational_status": "operational", "data_type": "demonstration",
            },
        ],
        "routes": [
            {"source_id": "Q1", "distance_km": 85, "transport_mode": "road"},
            {"source_id": "C1", "distance_km": 165, "transport_mode": "road"},
        ],
    }
    result = run_cost_environment_resilience(test_state)
    assert len(result.get("cost_estimates", [])) == 2
    assert len(result.get("environmental_assessments", [])) == 2
    assert len(result.get("resilience_assessments", [])) == 2
    assert result.get("current_agent") == "cost_environment_resilience"
    assert "cost_environment_resilience" in result.get("completed_agents", [])
    assert result.get("messages")
    report("Node execution with test data", True)
except Exception as e:
    report("Node execution with test data", False, str(e))


# ===================================================================
# 17. MISSING INPUT HANDLING
# ===================================================================
print("\n[17] Missing Input Handling")

try:
    result_nosrc = run_cost_environment_resilience({"sources": [], "routes": []})
    assert result_nosrc.get("errors")
    report("Missing sources returns error", True)
except Exception as e:
    report("Missing sources returns error", False, str(e))

try:
    result_noroute = run_cost_environment_resilience({
        "sources": [test_state["sources"][0]], "routes": [],
    })
    assert result_noroute.get("errors")
    report("Missing routes returns error", True)
except Exception as e:
    report("Missing routes returns error", False, str(e))

try:
    result_empty = run_cost_environment_resilience({})
    assert result_empty.get("errors")
    report("Empty state returns error", True)
except Exception as e:
    report("Empty state returns error", False, str(e))


# ===================================================================
# 18. END-TO-END AGENT 3 DETERMINISTIC EXECUTION
# ===================================================================
print("\n[18] End-to-End Agent 3 (using saved Agent 1+2 outputs)")

try:
    a1_path = Path("data/outputs/agent1_output.json")
    a2_path = Path("data/outputs/agent2_output.json")

    if a1_path.exists() and a2_path.exists():
        with a1_path.open("r", encoding="utf-8") as f:
            a1 = json.load(f)
        with a2_path.open("r", encoding="utf-8") as f:
            a2 = json.load(f)

        e2e_state = {
            "materials": a1.get("materials", []),
            "sources": a2.get("sources", []),
            "routes": a2.get("routes", []),
        }

        e2e_result = run_cost_environment_resilience(e2e_state)

        costs = e2e_result.get("cost_estimates", [])
        envs = e2e_result.get("environmental_assessments", [])
        ress = e2e_result.get("resilience_assessments", [])
        errors = e2e_result.get("errors", [])

        assert len(costs) >= 1, "No cost estimates"
        assert len(envs) >= 1, "No environmental assessments"
        assert len(ress) >= 1, "No resilience assessments"

        report(f"E2E: {len(costs)} costs, {len(envs)} envs, {len(ress)} resilience", True)

        # Check that at least one cost has a total
        has_total = any(c.get("total_cost") is not None for c in costs)
        report(f"At least one total cost computed: {has_total}", has_total)

        # Print sample
        print("\n  --- Sample Cost Estimate ---")
        for c in costs[:2]:
            print(f"    {c['source_name']}: material={c['material_cost']}, "
                  f"transport={c['transportation_cost']}, "
                  f"total={c['total_cost']} {c['cost_currency']}")

        print("\n  --- Sample Environmental ---")
        for e in envs[:2]:
            print(f"    {e['source_name']}: score={e['combined_impact_score']} "
                  f"({e['impact_category']}), reg={e['regulatory_sensitivity']}")

        print("\n  --- Sample Resilience ---")
        for r in ress[:2]:
            print(f"    {r['source_name']}: score={r['resilience_score']} "
                  f"({r['resilience_category']}), "
                  f"alts={r['alternative_count']}, "
                  f"scenarios={r['scenario_count']}")

        if errors:
            print(f"\n  Non-fatal errors: {len(errors)}")
            for err in errors[:3]:
                print(f"    {err}")

        # Save output
        output_dir = Path("data/outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        with (output_dir / "agent3_output.json").open("w", encoding="utf-8") as f:
            json.dump(e2e_result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  Output saved: data/outputs/agent3_output.json")
    else:
        print("  SKIP: Agent 1 or Agent 2 output files not found")
except Exception as e:
    report("End-to-end Agent 3", False, str(e))


# ===================================================================
# FINAL REPORT
# ===================================================================
print("\n" + "=" * 70)
total = passed + failed
print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
if failed == 0:
    print("AGENT 3 VALIDATION PASSED")
else:
    print("AGENT 3 VALIDATION HAS FAILURES")
print("=" * 70)

