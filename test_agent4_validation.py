"""
InfraMiner AI - Agent 4: Decision (AHP-TOPSIS)
Comprehensive Validation Suite (Deterministic, no LLM required)
"""

import sys
import json
import math
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


print("=" * 70)
print("AGENT 4 - DECISION (AHP-TOPSIS) - VALIDATION")
print("=" * 70)


# ===================================================================
# 1. SYNTAX / IMPORT
# ===================================================================
print("\n[1] Syntax and Import")

try:
    from agents.decision import (
        CRITERIA,
        CRITERION_TYPE,
        DEFAULT_PAIRWISE_MATRIX,
        _RI_TABLE,
        compute_ahp_weights,
        build_decision_matrix,
        normalize_matrix,
        apply_weights,
        find_ideal_solutions,
        calculate_distances,
        calculate_closeness,
        rank_alternatives,
        identify_fallbacks,
        build_final_sourcing_plan,
        generate_resilience_explanation,
        run_topsis,
        run_decision,
    )
    report("Import all Agent 4 symbols", True)
except Exception as e:
    report("Import all Agent 4 symbols", False, str(e))

try:
    from src.state import InfraMinerState
    report("Import InfraMinerState", True)
except Exception as e:
    report("Import InfraMinerState", False, str(e))


# ===================================================================
# 2. DECISION MATRIX CREATION
# ===================================================================
print("\n[2] Decision Matrix Creation")

sample_sources = [
    {
        "source_id": "S1",
        "source_name": "Quarry Alpha",
        "source_type": "quarry",
        "material_name": "Rock",
        "data_type": "demonstration",
    },
    {
        "source_id": "S2",
        "source_name": "Quarry Beta",
        "source_type": "quarry",
        "material_name": "Rock",
        "data_type": "demonstration",
    },
]
sample_routes = [
    {"source_id": "S1", "distance_km": 50.0, "transport_mode": "road"},
    {"source_id": "S2", "distance_km": 100.0, "transport_mode": "road"},
]
sample_costs = [
    {"source_id": "S1", "total_cost": 500000.0},
    {"source_id": "S2", "total_cost": 800000.0},
]
sample_envs = [
    {"source_id": "S1", "combined_impact_score": 0.35},
    {"source_id": "S2", "combined_impact_score": 0.55},
]
sample_res = [
    {"source_id": "S1", "resilience_score": 0.85},
    {"source_id": "S2", "resilience_score": 0.70},
]

try:
    alts, mat = build_decision_matrix(
        sample_sources, sample_routes, sample_costs, sample_envs, sample_res
    )
    assert len(alts) == 2, f"Expected 2 alternatives, got {len(alts)}"
    assert len(mat) == 2, f"Expected 2 rows in matrix, got {len(mat)}"
    assert len(mat[0]) == 4, f"Expected 4 criteria columns, got {len(mat[0])}"
    assert mat[0] == [500000.0, 50.0, 0.35, 0.85]
    assert mat[1] == [800000.0, 100.0, 0.55, 0.70]
    report("Decision matrix built correctly with 2 alternatives x 4 criteria", True)
except Exception as e:
    report("Decision matrix creation", False, str(e))


# ===================================================================
# 3. CORRECT CRITERIA
# ===================================================================
print("\n[3] Correct Criteria")

try:
    expected_criteria = ["cost", "logistics", "environmental", "resilience"]
    assert CRITERIA == expected_criteria, f"Expected {expected_criteria}, got {CRITERIA}"
    assert len(CRITERIA) == 4, f"Expected 4 criteria, got {len(CRITERIA)}"
    report("All 4 standard criteria present (cost, logistics, environmental, resilience)", True)
except Exception as e:
    report("Correct criteria", False, str(e))


# ===================================================================
# 4. COST DIRECTION (Lower is better)
# ===================================================================
print("\n[4] Cost Direction")

try:
    assert CRITERION_TYPE["cost"] == "cost", f"Expected cost direction 'cost', got {CRITERION_TYPE['cost']}"
    report("Cost criterion direction is 'cost' (lower is better)", True)
except Exception as e:
    report("Cost direction", False, str(e))


# ===================================================================
# 5. LOGISTICS DIRECTION (Lower is better)
# ===================================================================
print("\n[5] Logistics Direction")

try:
    assert CRITERION_TYPE["logistics"] == "cost", f"Expected logistics direction 'cost', got {CRITERION_TYPE['logistics']}"
    report("Logistics distance direction is 'cost' (lower distance is better)", True)
except Exception as e:
    report("Logistics direction", False, str(e))


# ===================================================================
# 6. ENVIRONMENTAL DIRECTION (Lower is better)
# ===================================================================
print("\n[6] Environmental Direction")

try:
    assert CRITERION_TYPE["environmental"] == "cost", f"Expected env direction 'cost', got {CRITERION_TYPE['environmental']}"
    report("Environmental impact direction is 'cost' (lower impact is better)", True)
except Exception as e:
    report("Environmental direction", False, str(e))


# ===================================================================
# 7. RESILIENCE DIRECTION (Higher is better)
# ===================================================================
print("\n[7] Resilience Direction")

try:
    assert CRITERION_TYPE["resilience"] == "benefit", f"Expected resilience direction 'benefit', got {CRITERION_TYPE['resilience']}"
    report("Resilience direction is 'benefit' (higher resilience is better)", True)
except Exception as e:
    report("Resilience direction", False, str(e))


# ===================================================================
# 8. AHP PAIRWISE MATRIX
# ===================================================================
print("\n[8] AHP Pairwise Matrix")

try:
    M = DEFAULT_PAIRWISE_MATRIX
    n = len(M)
    assert n == 4, f"Expected 4x4 matrix, got {n} rows"
    for i in range(n):
        assert len(M[i]) == 4, f"Row {i} has length {len(M[i])}"
        assert M[i][i] == 1.0, f"Diagonal element M[{i}][{i}] != 1.0"
        for j in range(n):
            prod = M[i][j] * M[j][i]
            assert abs(prod - 1.0) < 1e-4, f"Reciprocal failed at ({i},{j}): {M[i][j]} * {M[j][i]} = {prod}"
    report("AHP pairwise matrix is 4x4, diagonal 1.0, and reciprocally symmetric", True)
except Exception as e:
    report("AHP pairwise matrix", False, str(e))


# ===================================================================
# 9. AHP WEIGHT CALCULATION
# ===================================================================
print("\n[9] AHP Weight Calculation")

try:
    ahp_out = compute_ahp_weights()
    w = ahp_out["weights"]
    for c in CRITERIA:
        assert c in w, f"Missing weight for {c}"
        assert 0.0 < w[c] < 1.0, f"Weight for {c} out of bounds: {w[c]}"
    assert w["resilience"] > w["cost"], "Resilience weight should exceed cost weight"
    assert w["resilience"] > w["logistics"], "Resilience weight should exceed logistics weight"
    report(f"AHP weights calculated: Cost={w['cost']}, Log={w['logistics']}, Env={w['environmental']}, Res={w['resilience']}", True)
except Exception as e:
    report("AHP weight calculation", False, str(e))


# ===================================================================
# 10. AHP WEIGHTS SUM TO 1
# ===================================================================
print("\n[10] Weights Sum to 1")

try:
    w_sum = sum(ahp_out["weights"].values())
    assert abs(w_sum - 1.0) < 1e-3, f"Weights sum to {w_sum}, expected 1.0"
    report(f"Criterion weights sum to {w_sum:.4f} (approx 1.0)", True)
except Exception as e:
    report("Weights sum to 1", False, str(e))


# ===================================================================
# 11. LAMBDA MAX
# ===================================================================
print("\n[11] Lambda Max")

try:
    lam_max = ahp_out["lambda_max"]
    assert lam_max >= 4.0, f"lambda_max ({lam_max}) should be >= n (4.0)"
    assert lam_max < 4.5, f"lambda_max ({lam_max}) abnormally high for a consistent matrix"
    report(f"Lambda max calculated: {lam_max:.4f} (>= 4.0)", True)
except Exception as e:
    report("Lambda max", False, str(e))


# ===================================================================
# 12. CONSISTENCY INDEX (CI)
# ===================================================================
print("\n[12] Consistency Index (CI)")

try:
    ci = ahp_out["consistency_index"]
    expected_ci = (ahp_out["lambda_max"] - 4.0) / 3.0
    assert abs(ci - expected_ci) < 1e-3, f"CI mismatch: got {ci}, expected {expected_ci}"
    assert ci >= 0.0, f"CI cannot be negative: {ci}"
    report(f"Consistency Index (CI) = {ci:.4f}", True)
except Exception as e:
    report("Consistency Index", False, str(e))


# ===================================================================
# 13. CONSISTENCY RATIO (CR)
# ===================================================================
print("\n[13] Consistency Ratio (CR)")

try:
    cr = ahp_out["consistency_ratio"]
    ri_4 = _RI_TABLE[4]
    expected_cr = ci / ri_4
    assert abs(cr - expected_cr) < 1e-3, f"CR mismatch: got {cr}, expected {expected_cr}"
    assert cr < 0.10, f"CR = {cr:.4f} >= 0.10 (Matrix not consistent according to Saaty)"
    assert ahp_out["is_consistent"] is True
    report(f"Consistency Ratio (CR) = {cr:.4f} < 0.10 (Consistent: {ahp_out['is_consistent']})", True)
except Exception as e:
    report("Consistency Ratio", False, str(e))


# ===================================================================
# 14. TOPSIS NORMALIZATION
# ===================================================================
print("\n[14] TOPSIS Normalization")

try:
    norm_mat = normalize_matrix(mat)
    assert len(norm_mat) == 2
    assert len(norm_mat[0]) == 4
    for j in range(4):
        col_sq_sum = sum(norm_mat[i][j] ** 2 for i in range(2))
        assert abs(col_sq_sum - 1.0) < 1e-4, f"Column {j} Euclidean norm squared is {col_sq_sum}, expected 1.0"
    report("Vector normalization verified (columns sum to unit length)", True)
except Exception as e:
    report("TOPSIS normalization", False, str(e))


# ===================================================================
# 15. WEIGHTED NORMALIZED MATRIX
# ===================================================================
print("\n[15] Weighted Normalized Matrix")

try:
    weighted_mat = apply_weights(norm_mat, ahp_out["weights"])
    assert len(weighted_mat) == 2
    assert len(weighted_mat[0]) == 4
    w_vec = [ahp_out["weights"][c] for c in CRITERIA]
    for i in range(2):
        for j in range(4):
            expected_val = norm_mat[i][j] * w_vec[j]
            assert abs(weighted_mat[i][j] - expected_val) < 1e-4
    report("Weighted normalized matrix verified (v_ij = r_ij * w_j)", True)
except Exception as e:
    report("Weighted normalized matrix", False, str(e))


# ===================================================================
# 16. IDEAL SOLUTION (A+)
# ===================================================================
print("\n[16] Ideal Solution (A+)")

try:
    ideal, neg_ideal = find_ideal_solutions(weighted_mat)
    assert len(ideal) == 4
    for j, c in enumerate(CRITERIA):
        col_vals = [weighted_mat[i][j] for i in range(len(weighted_mat))]
        if CRITERION_TYPE[c] == "cost":
            assert ideal[j] == min(col_vals), f"For cost criterion {c}, ideal should be min"
        else:
            assert ideal[j] == max(col_vals), f"For benefit criterion {c}, ideal should be max"
    report("Ideal solution A+ correctly determined for cost/benefit criteria", True)
except Exception as e:
    report("Ideal solution", False, str(e))


# ===================================================================
# 17. NEGATIVE IDEAL SOLUTION (A-)
# ===================================================================
print("\n[17] Negative Ideal Solution (A-)")

try:
    assert len(neg_ideal) == 4
    for j, c in enumerate(CRITERIA):
        col_vals = [weighted_mat[i][j] for i in range(len(weighted_mat))]
        if CRITERION_TYPE[c] == "cost":
            assert neg_ideal[j] == max(col_vals), f"For cost criterion {c}, negative-ideal should be max"
        else:
            assert neg_ideal[j] == min(col_vals), f"For benefit criterion {c}, negative-ideal should be min"
    report("Negative ideal solution A- correctly determined for cost/benefit criteria", True)
except Exception as e:
    report("Negative ideal solution", False, str(e))


# ===================================================================
# 18. DISTANCE CALCULATIONS
# ===================================================================
print("\n[18] Distance Calculations")

try:
    d_plus, d_minus = calculate_distances(weighted_mat, ideal, neg_ideal)
    assert len(d_plus) == 2
    assert len(d_minus) == 2
    for dp in d_plus:
        assert dp >= 0.0, f"Distance d+ cannot be negative: {dp}"
    for dm in d_minus:
        assert dm >= 0.0, f"Distance d- cannot be negative: {dm}"
    report(f"Euclidean distances computed: d+={d_plus}, d-={d_minus}", True)
except Exception as e:
    report("Distance calculations", False, str(e))


# ===================================================================
# 19. CLOSENESS COEFFICIENT
# ===================================================================
print("\n[19] Closeness Coefficient")

try:
    closeness = calculate_closeness(d_plus, d_minus)
    assert len(closeness) == 2
    for c_val in closeness:
        assert 0.0 <= c_val <= 1.0, f"Closeness coefficient {c_val} out of bounds [0, 1]"
    # S1 is better than S2 in all 4 criteria, so S1 must have higher closeness
    assert closeness[0] > closeness[1], f"Expected S1 closeness ({closeness[0]}) > S2 ({closeness[1]})"
    report(f"Closeness coefficients: S1={closeness[0]:.4f}, S2={closeness[1]:.4f} (S1 > S2)", True)
except Exception as e:
    report("Closeness coefficient", False, str(e))


# ===================================================================
# 20. ALTERNATIVE RANKING
# ===================================================================
print("\n[20] Alternative Ranking")

try:
    ranked = rank_alternatives(alts, closeness)
    assert len(ranked) == 2
    assert ranked[0]["source_id"] == "S1"
    assert ranked[0]["rank"] == 1
    assert ranked[1]["source_id"] == "S2"
    assert ranked[1]["rank"] == 2
    report(f"Alternatives ranked: #1={ranked[0]['source_name']} (C={ranked[0]['closeness_coefficient']}), #2={ranked[1]['source_name']}", True)
except Exception as e:
    report("Alternative ranking", False, str(e))


# ===================================================================
# 21. FALLBACK IDENTIFICATION
# ===================================================================
print("\n[21] Fallback Identification")

try:
    fallbacks = identify_fallbacks(ranked, sample_res)
    assert len(fallbacks) == 1, f"Expected 1 fallback alternative, got {len(fallbacks)}"
    fb = fallbacks[0]
    assert fb["source_id"] == "S2"
    assert "is_viable_fallback" in fb
    assert isinstance(fb["feasibility_reasons"], list)
    assert len(fb["feasibility_reasons"]) > 0
    report(f"Fallback identified: {fb['source_name']} (viable: {fb['is_viable_fallback']}, reasons: {fb['feasibility_reasons']})", True)
except Exception as e:
    report("Fallback identification", False, str(e))


# ===================================================================
# 22. SHARED STATE INTEGRATION
# ===================================================================
print("\n[22] Shared State Integration")

try:
    state_annotations = InfraMinerState.__annotations__
    assert "decision_results" in state_annotations
    assert "current_agent" in state_annotations
    assert "completed_agents" in state_annotations
    assert "messages" in state_annotations
    report("All Agent 4 output keys exist in InfraMinerState schema", True)
except Exception as e:
    report("Shared state integration", False, str(e))


# ===================================================================
# 23. LANGGRAPH NODE EXECUTION
# ===================================================================
print("\n[23] LangGraph Node Execution")

try:
    mock_state: InfraMinerState = {
        "sources": sample_sources,
        "routes": sample_routes,
        "cost_estimates": sample_costs,
        "environmental_assessments": sample_envs,
        "resilience_assessments": sample_res,
    }
    node_out = run_decision(mock_state)
    assert "decision_results" in node_out
    assert node_out["current_agent"] == "decision"
    assert "decision" in node_out["completed_agents"]
    assert len(node_out["messages"]) >= 1

    dec_res = node_out["decision_results"]
    assert dec_res["methodology"] == "AHP-TOPSIS"
    assert "ahp" in dec_res
    assert "topsis" in dec_res
    assert "ranking" in dec_res
    assert "primary_recommendation" in dec_res
    assert "fallback_alternatives" in dec_res
    assert "final_sourcing_plan" in dec_res
    assert "resilience_explanation" in dec_res
    assert dec_res["primary_recommendation"]["source_id"] == "S1"
    report("run_decision successfully produced complete structured output", True)
except Exception as e:
    report("LangGraph node execution", False, str(e))


# ===================================================================
# 24. MISSING-INPUT HANDLING
# ===================================================================
print("\n[24] Missing-Input Handling")

try:
    # Empty state
    out_empty = run_decision({})
    assert out_empty.get("errors") is not None
    assert "decision" == out_empty["current_agent"]

    # Sources but no assessments
    out_no_assess = run_decision({"sources": sample_sources, "routes": sample_routes})
    assert out_no_assess.get("errors") is not None

    # Empty sources
    out_no_src = run_decision({"sources": [], "routes": sample_routes})
    assert out_no_src.get("errors") is not None

    report("Graceful error handling for empty states, missing sources, and missing assessments", True)
except Exception as e:
    report("Missing-input handling", False, str(e))


# ===================================================================
# 25. END-TO-END AGENT 4 EXECUTION USING AGENT 1-3 OUTPUTS
# ===================================================================
print("\n[25] End-to-End Agent 4 Execution (Real Outputs from Agents 1-3)")

try:
    a2_path = Path("data/outputs/agent2_output.json")
    a3_path = Path("data/outputs/agent3_output.json")

    assert a2_path.exists(), "data/outputs/agent2_output.json missing"
    assert a3_path.exists(), "data/outputs/agent3_output.json missing"

    with a2_path.open("r", encoding="utf-8") as f:
        a2_data = json.load(f)
    with a3_path.open("r", encoding="utf-8") as f:
        a3_data = json.load(f)

    pipeline_state: InfraMinerState = {
        "sources": a2_data["sources"],
        "routes": a2_data["routes"],
        "cost_estimates": a3_data["cost_estimates"],
        "environmental_assessments": a3_data["environmental_assessments"],
        "resilience_assessments": a3_data["resilience_assessments"],
    }

    final_result = run_decision(pipeline_state)
    assert "errors" not in final_result, f"Errors in execution: {final_result.get('errors')}"
    assert "decision_results" in final_result

    dr = final_result["decision_results"]
    assert dr["methodology"] == "AHP-TOPSIS"
    assert dr["ahp"]["is_consistent"] is True
    assert dr["ahp"]["consistency_ratio"] < 0.10
    assert len(dr["ranking"]) >= 3, f"Expected at least 3 ranked sources, got {len(dr['ranking'])}"
    assert dr["primary_recommendation"] is not None
    assert len(dr["final_sourcing_plan"]) >= 1
    assert len(dr["resilience_explanation"]) > 50

    print(f"\n  --- End-to-End Decision Summary ---")
    print(f"  Criteria Evaluated: {', '.join(dr['ahp']['criteria'])}")
    print(f"  AHP Consistency Ratio: {dr['ahp']['consistency_ratio']} (< 0.10: {dr['ahp']['is_consistent']})")
    print(f"  Primary Recommendation: {dr['primary_recommendation']['source_name']} (Closeness: {dr['primary_recommendation']['closeness_coefficient']})")
    print(f"  Ranked Alternatives Count: {len(dr['ranking'])}")
    for alt in dr["ranking"]:
        print(f"    Rank {alt['rank']}: {alt['source_name']} ({alt['material_name']}) - TOPSIS Score: {alt['closeness_coefficient']:.4f}")

    print(f"\n  --- Final Sourcing Plan by Material ---")
    for sp in dr["final_sourcing_plan"]:
        p_src = sp["primary_source"]
        fb_names = [f["source_name"] for f in sp["fallback_sources"]]
        print(f"    Material: {sp['material_name']}")
        print(f"      Primary Source: {p_src['source_name']} (Score: {p_src['closeness_coefficient']:.4f})")
        print(f"      Fallback Sources: {', '.join(fb_names) if fb_names else 'None'}")
        print(f"      Strategy: {sp['sourcing_strategy']}")

    # Save output for pipeline documentation and downstream inspection
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "agent4_output.json"
    with out_file.open("w", encoding="utf-8") as f:
        json.dump(final_result, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Output saved to: {out_file}")

    report("End-to-end Agent 4 execution with Agent 1-3 pipeline data passed perfectly", True)
except Exception as e:
    report("End-to-end Agent 4 execution", False, str(e))


# ===================================================================
# ADDITIONAL TESTS: SPECIALIZED METHODS
# ===================================================================
print("\n[Additional Tests] Specialized Decision Methods")

try:
    # Test custom pairwise matrix calculation
    custom_matrix = [
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
        [1.0, 1.0, 1.0, 1.0],
    ]
    custom_ahp = compute_ahp_weights(custom_matrix)
    for c in CRITERIA:
        assert abs(custom_ahp["weights"][c] - 0.25) < 1e-4
    assert custom_ahp["consistency_ratio"] == 0.0
    assert custom_ahp["is_consistent"] is True
    report("Custom equal-weights AHP matrix calculates exactly 0.25 each and CR=0", True)
except Exception as e:
    report("Custom AHP matrix", False, str(e))

try:
    # Test single alternative TOPSIS edge case
    single_res = run_topsis([sample_sources[0]], [[100.0, 10.0, 0.2, 0.9]], ahp_out["weights"])
    assert len(single_res["ranked_alternatives"]) == 1
    assert single_res["ranked_alternatives"][0]["closeness_coefficient"] == 1.0
    report("Single-alternative TOPSIS handled gracefully (closeness = 1.0)", True)
except Exception as e:
    report("Single alternative TOPSIS", False, str(e))


# ===================================================================
# FINAL REPORT
# ===================================================================
print("\n" + "=" * 70)
total = passed + failed
print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
if failed == 0:
    print("AGENT 4 VALIDATION PASSED")
else:
    print("AGENT 4 VALIDATION HAS FAILURES")
print("=" * 70)

