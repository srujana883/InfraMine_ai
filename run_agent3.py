"""
InfraMiner AI - Agent 3 Demonstration Runner
Runs ONLY Agent 3: Cost, Environment & Resilience using REAL verified Vadhavan datasets.
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
from agents.cost_environment_resilience import (
    run_cost_environment_resilience,
    VERIFIED_COST_DATA_PATH,
    VERIFIED_ENVIRONMENTAL_DATA_PATH,
    VERIFIED_DISRUPTION_DATA_PATH,
)


def main():
    # 1. Prepare required state from Agent 1 and Agent 2 outputs without executing Agent 4
    agent1_file = Path("data/outputs/agent1_output.json")
    agent2_file = Path("data/outputs/agent2_real_output.json")

    # Fallback to demo agent2 output if real output doesn't exist yet
    if not agent2_file.exists():
        agent2_file = Path("data/outputs/agent2_output.json")

    if not agent1_file.exists() or not agent2_file.exists():
        print("Error: Required input files from Agent 1 and/or Agent 2 not found.")
        print("Please run 'python run_agent1.py' and 'python run_agent2.py' first.")
        sys.exit(1)

    with open(agent1_file, "r", encoding="utf-8") as f:
        agent1_data = json.load(f)

    with open(agent2_file, "r", encoding="utf-8") as f:
        agent2_data = json.load(f)

    state: InfraMinerState = {
        "project_name": agent1_data.get("project_name", "Vadhavan Port"),
        "materials": agent1_data.get("materials", []),
        "sources": agent2_data.get("sources", []),
        "routes": agent2_data.get("routes", []),
        "cost_dataset_path": str(VERIFIED_COST_DATA_PATH),
        "environmental_dataset_path": str(VERIFIED_ENVIRONMENTAL_DATA_PATH),
        "disruption_dataset_path": str(VERIFIED_DISRUPTION_DATA_PATH),
    }

    # 2. Run Agent 3
    result = run_cost_environment_resilience(state)

    costs = result.get("cost_estimates", [])
    envs = result.get("environmental_assessments", [])
    ress = result.get("resilience_assessments", [])
    errors = result.get("errors", [])

    # Save output for inspection
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "agent3_real_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    # 3. Print human-readable result
    print("===== AGENT 3: COST, ENVIRONMENT & RESILIENCE =====\n")
    print(f"Cost assessments: {len(costs)}")
    print(f"Environmental assessments: {len(envs)}")
    print(f"Resilience assessments: {len(ress)}")
    print(f"Errors: {errors if errors else 'None'}\n")

    print("===== SAMPLE COST ASSESSMENTS =====\n")
    for i, c in enumerate(costs[:3], 1):
        print(f"[{i}] Source: {c.get('source_name')} ({c.get('source_id')})")
        print(f"    Material: {c.get('material_name')}")
        qty_str = f"{c.get('quantity'):,.1f}" if c.get("quantity") is not None else "NULL"
        print(f"    Quantity: {qty_str}")
        uc_str = f"Rs. {c.get('unit_cost'):,.2f}" if c.get("unit_cost") is not None else "NULL (unspecified in DPR)"
        print(f"    Unit Cost: {uc_str}")
        mc_str = f"Rs. {c.get('material_cost'):,.2f} INR" if c.get("material_cost") is not None else "NULL"
        print(f"    Material Cost: {mc_str}")
        print(f"    Distance: {c.get('distance_km')} km via {c.get('transport_mode')}")
        tr_str = f"Rs. {c.get('transport_rate')}" if c.get("transport_rate") is not None else "NULL (per-unit-km rate not stated in DPR)"
        print(f"    Transport Rate: {tr_str}")
        tc_str = f"Rs. {c.get('total_cost'):,.2f} INR" if c.get("total_cost") is not None else "NULL"
        print(f"    Total Cost: {tc_str}")
        print(f"    Cost Data Type: {c.get('cost_data_type')}")
        if c.get("source_document"):
            print(f"    Citation: {c.get('source_document')}, {c.get('document_page')}")
        if c.get("calculation_notes"):
            print(f"    Notes: {c.get('calculation_notes')}")
        print()

    print("===== SAMPLE ENVIRONMENTAL ASSESSMENTS =====\n")
    for i, e in enumerate(envs[:3], 1):
        print(f"[{i}] Source: {e.get('source_name')} ({e.get('source_id')})")
        print(f"    Primary Factor: {e.get('primary_environmental_factor')}")
        print(f"    Impact Value: {e.get('primary_impact_value')} {e.get('primary_impact_unit') or ''}")
        print(f"    Regulatory Status: {e.get('status')} (Sensitivity: {e.get('regulatory_sensitivity')})")
        print(f"    Synthetic 0-1 Score: {e.get('combined_impact_score')} (PRESERVED AS NULL TO PREVENT FABRICATION)")
        print(f"    Data Type: {e.get('data_type')}")
        if e.get("source_document"):
            print(f"    Citation: {e.get('source_document')}, {e.get('document_page')}")
        if e.get("evidence_text"):
            print(f"    Evidence: \"{e.get('evidence_text')}\"")
        print()

    print("===== SAMPLE RESILIENCE ASSESSMENTS =====\n")
    for i, r in enumerate(ress[:3], 1):
        print(f"[{i}] Source: {r.get('source_name')} ({r.get('source_id')})")
        print(f"    Resilience Category: {str(r.get('resilience_category')).upper()} (Score: {r.get('resilience_score')})")
        print(f"    Alternative Count: {r.get('alternative_count')} alternatives")
        print(f"    Fallback Note: {r.get('fallback_note')}")
        print(f"    Numerical Disruption: {r.get('disruption_risk')} (PRESERVED AS NULL TO PREVENT FABRICATION)")
        print(f"    Data Type: {r.get('data_type')}")
        print(f"    Applicable Scenarios: {r.get('applicable_scenarios')}")
        if r.get("primary_scenario_id"):
            print(f"    Primary Scenario: {r.get('primary_scenario_id')} ({r.get('primary_risk_type')})")
        print()

    print("===== AGENT 3 COMPLETE =====")


if __name__ == "__main__":
    main()

