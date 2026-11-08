"""
InfraMiner AI - Agent 2 Demonstration Runner
Runs ONLY Agent 2: Source & Logistics using REAL verified Vadhavan source data.
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
from agents.source_logistics import run_source_logistics, VERIFIED_SOURCE_DATA_PATH


def main():
    # 1. Prepare required state from Agent 1 output without executing other agents
    agent1_file = Path("data/outputs/agent1_output.json")
    if not agent1_file.exists():
        print(f"Error: Required Agent 1 output file not found at {agent1_file}")
        print("Please run 'python run_agent1.py' first.")
        sys.exit(1)

    with open(agent1_file, "r", encoding="utf-8") as f:
        agent1_data = json.load(f)

    state: InfraMinerState = {
        "project_name": agent1_data.get("project_name", "Vadhavan Port"),
        "project_type": agent1_data.get("project_type", "Container Port"),
        "project_location": agent1_data.get("project_location"),
        "materials": agent1_data.get("materials", []),
        "source_dataset_path": str(VERIFIED_SOURCE_DATA_PATH),
    }

    # 2. Run Agent 2 (uses data/sources/verified_material_sources.csv)
    result = run_source_logistics(state)

    sources = result.get("sources", [])
    routes = result.get("routes", [])
    errors = result.get("errors", [])

    # Save output for downstream inspection
    out_dir = Path("data/outputs")
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "agent2_real_output.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    # 3. Print human-readable result
    print("===== AGENT 2: SOURCE & LOGISTICS =====\n")
    print(f"Sources: {len(sources)}")
    print(f"Routes: {len(routes)}")
    print(f"Errors: {errors if errors else 'None'}\n")

    print("===== REAL SOURCE CANDIDATES =====\n")
    for s in sources[:15]:
        print(f"- source_id: {s.get('source_id')}")
        print(f"  source_name: {s.get('source_name')}")
        print(f"  material_name: {s.get('material_name')}")
        print(f"  source_type: {s.get('source_type')}")
        print(f"  status: {s.get('status')}")
        print(f"  data_type: {s.get('data_type')}")
        print(f"  confidence: {s.get('confidence')}\n")

    print("===== SAMPLE ROUTES =====\n")
    for r in routes[:10]:
        print(f"- source_id: {r.get('source_id')}")
        print(f"  source_name: {r.get('source_name')}")
        print(f"  material_name: {r.get('material_name')}")
        print(f"  distance_km: {r.get('distance_km')}")
        print(f"  transport_mode: {r.get('transport_mode')}")
        print(f"  distance_source: {r.get('distance_source')}\n")

    print("===== AGENT 2 COMPLETE =====")


if __name__ == "__main__":
    main()

