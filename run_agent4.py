"""
InfraMiner AI - Agent 4 Demonstration Runner
Runs ONLY Agent 4: Decision using AHP-TOPSIS on outputs from Agents 1–3.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.state import InfraMinerState
from agents.decision import run_decision


def main():
    # 1. Load required state from Agents 1, 2, and 3 without executing them
    a1_file = Path("data/outputs/agent1_output.json")
    a2_file = Path("data/outputs/agent2_real_output.json")
    if not a2_file.exists():
        a2_file = Path("data/outputs/agent2_output.json")

    a3_file = Path("data/outputs/agent3_real_output.json")
    if not a3_file.exists():
        a3_file = Path("data/outputs/agent3_output.json")

    if not a1_file.exists() or not a2_file.exists() or not a3_file.exists():
        print("Error: Missing prerequisite output files from Agents 1, 2, or 3.")
        print("Please run 'python run_agent1.py', 'python run_agent2.py', and 'python run_agent3.py' first.")
        sys.exit(1)

    with open(a1_file, "r", encoding="utf-8") as f:
        a1_data = json.load(f)
    with open(a2_file, "r", encoding="utf-8") as f:
        a2_data = json.load(f)
    with open(a3_file, "r", encoding="utf-8") as f:
        a3_data = json.load(f)

    state: InfraMinerState = {
        "project_name": a1_data.get("project_name", "Vadhavan Port"),
        "materials": a1_data.get("materials", []),
        "sources": a2_data.get("sources", []),
        "routes": a2_data.get("routes", []),
        "cost_estimates": a3_data.get("cost_estimates", []),
        "environmental_assessments": a3_data.get("environmental_assessments", []),
        "resilience_assessments": a3_data.get("resilience_assessments", []),
    }

    # 2. Run ONLY Agent 4
    result = run_decision(state)

    decision_results = result.get("decision_results", {})
    ahp = decision_results.get("ahp", {})
    weights = ahp.get("weights", {})
    cr = ahp.get("consistency_ratio", 0.0)
    ranking = decision_results.get("ranking", [])
    sourcing_plan = decision_results.get("final_sourcing_plan", [])
    fallbacks = decision_results.get("fallback_alternatives", [])
    primary = decision_results.get("primary_recommendation", {})
    total_evaluated = decision_results.get("total_alternatives_evaluated", len(ranking))

    # Save real output
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "agent4_real_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    # 3. Print human-readable output
    print("===== AGENT 4: DECISION & AHP-TOPSIS =====\n")
    print(f"Alternatives evaluated: {total_evaluated}\n")

    print("===== AHP CRITERIA WEIGHTS =====\n")
    print(f"Cost: {weights.get('cost', 0.0):.4f}")
    print(f"Logistics: {weights.get('logistics', 0.0):.4f}")
    print(f"Environmental Impact: {weights.get('environmental', 0.0):.4f}")
    print(f"Resilience: {weights.get('resilience', 0.0):.4f}\n")
    print(f"AHP Consistency Ratio: {cr:.4f} ({'Consistent < 0.10' if cr < 0.10 else 'Inconsistent'})\n")

    print("===== TOPSIS RESULTS =====\n")
    print(f"Ranked Alternatives ({len(ranking)} unique alternatives):")
    for alt in ranking:
        sid = alt.get("source_id")
        sname = alt.get("source_name")
        mat = alt.get("material_name")
        c_score = alt.get("closeness_coefficient", 0.0)
        rank_num = alt.get("rank")
        dist = alt.get("actual_distance_km")
        status_info = alt.get("recommendation_status", "provisional_indicative")

        print(f"Rank {rank_num}: [{sid}] {sname}")
        print(f"  Material               : {mat}")
        print(f"  TOPSIS Closeness Score : {c_score:.4f}")
        print(f"  Lead Distance          : {dist} km" if dist is not None else "  Lead Distance          : NULL")
        print(f"  Cost Status            : {alt.get('cost_status')}")
        print(f"  Environmental Status   : {alt.get('environmental_status')}")
        print(f"  Resilience Status      : {alt.get('resilience_status')}")
        print(f"  Evaluation Status      : {status_info.upper()}\n")

    print("===== FINAL DECISION OUTPUT =====\n")
    print(f"Primary Overall Recommendation: {primary.get('source_name')} ({primary.get('source_id')})")
    print(f"Material: {primary.get('material_name')}")
    print(f"TOPSIS Closeness Score: {primary.get('closeness_coefficient'):.4f}\n")

    print("--- Final Sourcing Plans by Material ---")
    for plan in sourcing_plan:
        mat_name = plan.get("material_name")
        p_src = plan.get("primary_source", {})
        fb_sources = plan.get("fallback_sources", [])
        status = plan.get("recommendation_status", "provisional_indicative")

        print(f"\nMaterial: {mat_name}")
        print(f"  Evaluation Status : {status.upper()}")
        if p_src.get('source_name') == "No viable source identified":
            print("  Primary Source    : No viable source identified")
            print(f"  Candidate Source  : {p_src.get('source_id')} (Failed viability threshold: TOPSIS {p_src.get('closeness_coefficient', 0.0):.4f} < 0.30)")
        else:
            print(f"  Primary Source    : {p_src.get('source_name')} ({p_src.get('source_id')})")
            print(f"  TOPSIS Score      : {p_src.get('closeness_coefficient'):.4f}")
            if p_src.get("resilience_score") is not None:
                print(f"  Resilience Score  : {p_src.get('resilience_score')}")

        if fb_sources:
            print(f"  Fallback Sources  : ({len(fb_sources)} distinct sources)")
            for fb in fb_sources:
                print(f"    - {fb.get('source_name')} ({fb.get('source_id')}) | TOPSIS: {fb.get('closeness_coefficient'):.4f} | Viable: {fb.get('is_viable')}")
        else:
            print("  Fallback Sources  : None (Single-source dependency / No alternative)")

        print(f"  Strategy & Notes  : {plan.get('sourcing_strategy')}")

    print("\n--- Fallback / Resilience Information ---")
    viable_fallbacks = [f for f in fallbacks if f.get("is_viable_fallback")]
    print(f"Total viable fallback alternatives identified: {len(viable_fallbacks)}")
    for fb in viable_fallbacks[:5]:
        print(f"- {fb.get('source_name')} ({fb.get('material_name')}): Rank {fb.get('rank')}, Closeness {fb.get('closeness_coefficient'):.4f}, Alts {fb.get('alternative_count')}")

    print(f"\nResilience Narrative:\n{decision_results.get('resilience_explanation')}\n")

    errors = result.get("errors", [])
    print(f"Errors: {errors if errors else 'None'}\n")
    print("===== AGENT 4 COMPLETE =====")


if __name__ == "__main__":
    main()

