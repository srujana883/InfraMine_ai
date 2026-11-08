"""
InfraMiner AI — Agent 2: Source & Logistics — Validation Suite
"""
import sys, json
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
        print(f"  FAIL: {name} — {detail}")


print("=" * 70)
print("AGENT 2 — SOURCE & LOGISTICS — VALIDATION")
print("=" * 70)


# ===================================================================
# 1. SYNTAX / IMPORT
# ===================================================================
print("\n[1] Syntax and Import")

try:
    from agents.source_logistics import (
        MaterialSource, LogisticsRoute,
        haversine_distance, load_source_data,
        find_sources_for_material, calculate_logistics,
        discover_sources, run_source_logistics,
    )
    report("Import all symbols", True)
except Exception as e:
    report("Import all symbols", False, str(e))


# ===================================================================
# 2. PYDANTIC MODELS
# ===================================================================
print("\n[2] Pydantic Model Validation")

try:
    ms = MaterialSource(
        source_id="TEST-01", source_name="Test Quarry",
        source_type="quarry", material_name="Rock",
        latitude=19.5, longitude=73.5,
        available_quantity=1000000, quantity_unit="tonnes",
        data_type="demonstration",
    )
    d = ms.model_dump()
    assert d["source_id"] == "TEST-01"
    report("MaterialSource valid", True)
except Exception as e:
    report("MaterialSource valid", False, str(e))

try:
    ms2 = MaterialSource(
        source_id="TEST-02", source_name="Unknown",
        source_type="supplier", material_name="Steel",
        available_quantity=None, latitude=None, longitude=None,
    )
    assert ms2.available_quantity is None
    assert ms2.latitude is None
    report("MaterialSource null handling", True)
except Exception as e:
    report("MaterialSource null handling", False, str(e))

try:
    lr = LogisticsRoute(
        source_id="TEST-01", source_name="Test Quarry",
        material_name="Rock",
        origin_lat=19.5, origin_lng=73.5,
        destination_lat=19.82, destination_lng=72.71,
        distance_km=95.5, transport_mode="road",
    )
    d = lr.model_dump()
    assert d["distance_km"] == 95.5
    report("LogisticsRoute valid", True)
except Exception as e:
    report("LogisticsRoute valid", False, str(e))


# ===================================================================
# 3. HAVERSINE DISTANCE
# ===================================================================
print("\n[3] Haversine Distance Calculation")

try:
    # Mumbai to Pune straight-line distance for these coordinates
    d1 = haversine_distance(19.076, 72.877, 18.520, 73.856)
    assert 115 < d1 < 125, f"Got {d1}"
    report(f"Mumbai-Pune distance ({d1:.1f} km)", True)
except Exception as e:
    report("Mumbai-Pune distance", False, str(e))

try:
    # Same point = 0
    d0 = haversine_distance(19.82, 72.71, 19.82, 72.71)
    assert d0 == 0.0
    report("Zero distance for same point", True)
except Exception as e:
    report("Zero distance for same point", False, str(e))


# ===================================================================
# 4. SOURCE DATA LOADING
# ===================================================================
print("\n[4] Source Data Loading")

try:
    sources = load_source_data()
    assert len(sources) > 0, "No sources loaded"
    report(f"Loaded {len(sources)} source records", True)
except Exception as e:
    report("Load source data", False, str(e))

try:
    # Verify record structure
    src = sources[0]
    assert "source_id" in src
    assert "source_name" in src
    assert "material_name" in src
    assert "data_type" in src
    report("Source record structure valid", True)
except Exception as e:
    report("Source record structure valid", False, str(e))

try:
    # Missing file returns empty list
    empty = load_source_data("nonexistent.csv")
    assert empty == []
    report("Missing file returns empty list", True)
except Exception as e:
    report("Missing file returns empty list", False, str(e))


# ===================================================================
# 5. SOURCE MATCHING
# ===================================================================
print("\n[5] Material-Source Matching")

try:
    rock_matches = find_sources_for_material("Rock/Stone", None, sources)
    assert len(rock_matches) >= 1, f"Got {len(rock_matches)}"
    report(f"Rock/Stone matched {len(rock_matches)} source(s)", True)
except Exception as e:
    report("Rock/Stone matching", False, str(e))

try:
    steel_matches = find_sources_for_material("Steel Reinforcement", "Fe500D", sources)
    report(f"Steel matched {len(steel_matches)} source(s)", len(steel_matches) >= 1)
except Exception as e:
    report("Steel matching", False, str(e))

try:
    cement_matches = find_sources_for_material("Cement", None, sources)
    report(f"Cement matched {len(cement_matches)} source(s)", len(cement_matches) >= 1)
except Exception as e:
    report("Cement matching", False, str(e))

try:
    none_matches = find_sources_for_material("Unobtainium", None, sources)
    assert none_matches == []
    report("Non-existent material returns empty", True)
except Exception as e:
    report("Non-existent material returns empty", False, str(e))


# ===================================================================
# 6. LOGISTICS CALCULATION
# ===================================================================
print("\n[6] Logistics Calculation")

try:
    test_src = {
        "source_id": "T1", "source_name": "Test",
        "material_name": "Rock", "latitude": 19.45,
        "longitude": 73.52, "transport_mode": "road",
        "data_type": "demonstration",
    }
    loc = {"lat": 19.82, "lng": 72.71}
    route = calculate_logistics(test_src, loc)
    assert route["distance_km"] is not None
    assert route["distance_km"] > 0
    assert route["distance_source"] == "haversine_calculation"
    report(f"Haversine route ({route['distance_km']} km)", True)
except Exception as e:
    report("Haversine route calculation", False, str(e))

try:
    # Source with dataset distance
    test_src2 = {
        "source_id": "T2", "source_name": "Test2",
        "material_name": "Sand", "latitude": None,
        "longitude": None, "distance_km": 50.0,
        "transport_mode": "marine",
    }
    route2 = calculate_logistics(test_src2, loc)
    assert route2["distance_km"] == 50.0
    assert route2["distance_source"] == "dataset"
    report("Dataset distance used when coordinates missing", True)
except Exception as e:
    report("Dataset distance", False, str(e))


# ===================================================================
# 7. FULL DISCOVERY (using Agent 1 output)
# ===================================================================
print("\n[7] Full Source Discovery")

try:
    output_file = Path("data/outputs/agent1_output.json")
    if output_file.exists():
        with output_file.open("r", encoding="utf-8") as f:
            agent1_output = json.load(f)
        materials = agent1_output.get("materials", [])

        if materials:
            proj_loc = agent1_output.get("project_location")
            srcs, rts, msgs = discover_sources(materials, proj_loc)
            report(f"Discovered {len(srcs)} source(s) for {len(materials)} material(s)", len(srcs) >= 1)
            report(f"Calculated {len(rts)} route(s)", len(rts) >= 1)

            if srcs:
                print(f"\n  --- Sample Sources ---")
                for s in srcs[:5]:
                    print(f"    {s['source_name']}: {s['material_name']} "
                          f"({s['source_type']}, {s['data_type']})")

            if rts:
                print(f"\n  --- Sample Routes ---")
                for r in rts[:5]:
                    print(f"    {r['source_name']} -> project: "
                          f"{r['distance_km']} km via {r['transport_mode']}")
        else:
            report("Agent 1 output has materials", False, "Empty materials list")
    else:
        print("  SKIP: Agent 1 output not found")
except Exception as e:
    report("Full source discovery", False, str(e))


# ===================================================================
# 8. STATE INTEGRATION
# ===================================================================
print("\n[8] Shared State Integration")

try:
    from src.state import InfraMinerState
    state_fields = set(InfraMinerState.__annotations__.keys())
    for field in ["sources", "routes", "messages", "current_agent", "completed_agents"]:
        assert field in state_fields, f"Missing: {field}"
    report("Agent 2 output fields in InfraMinerState", True)
except Exception as e:
    report("Agent 2 output fields in InfraMinerState", False, str(e))


# ===================================================================
# 9. NODE FUNCTION TEST
# ===================================================================
print("\n[9] LangGraph Node Test")

try:
    # With materials in state
    test_state = {
        "materials": [
            {"material_name": "Rock/Stone", "quantity": 32100000, "unit": "tonnes", "specification": None},
            {"material_name": "Cement", "quantity": None, "unit": None, "specification": None},
        ],
        "project_location": {"lat": 19.82, "lng": 72.71},
    }
    result = run_source_logistics(test_state)
    assert not result.get("errors"), f"Errors: {result.get('errors')}"
    assert len(result.get("sources", [])) >= 1
    assert len(result.get("routes", [])) >= 1
    assert result.get("current_agent") == "source_logistics"
    assert "source_logistics" in result.get("completed_agents", [])
    report("Node function with materials", True)
except Exception as e:
    report("Node function with materials", False, str(e))

try:
    # Without materials — should return error
    empty_result = run_source_logistics({})
    assert empty_result.get("errors")
    report("Node function handles missing materials", True)
except Exception as e:
    report("Node function handles missing materials", False, str(e))


# ===================================================================
# SAVE AGENT 2 OUTPUT
# ===================================================================
if 'result' in dir() and result and not result.get("errors"):
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    out_file = output_dir / "agent2_output.json"
    if not out_file.exists():
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False, default=str)
        print(f"\n  Output saved: data/outputs/agent2_output.json")


# ===================================================================
# FINAL REPORT
# ===================================================================
print("\n" + "=" * 70)
total = passed + failed
print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")
if failed == 0:
    print("AGENT 2 COMPLETE")
else:
    print("AGENT 2 VALIDATION HAS FAILURES")
print("=" * 70)

