"""
InfraMiner AI - Agent 1: Project & Material Intelligence
Complete Validation Suite
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
print("AGENT 1 - PROJECT & MATERIAL INTELLIGENCE - VALIDATION")
print("=" * 70)


# ===================================================================
# 1. SYNTAX / IMPORT
# ===================================================================

print("\n[1] Syntax and Import")

try:
    from agents.project_intelligence import (
        ProjectInfoExtraction,
        ProjectLocation,
        MaterialRequirement,
        MaterialListExtraction,
        extract_project_info,
        extract_material_requirements,
        run_project_intelligence,
        _retrieve_project_context,
        _retrieve_material_context,
    )
    report("Import all symbols", True)
except Exception as e:
    report("Import all symbols", False, str(e))

try:
    from src.state import InfraMinerState
    report("Import InfraMinerState", True)
except Exception as e:
    report("Import InfraMinerState", False, str(e))

try:
    from src.llm.factory import get_llm
    report("Import get_llm", True)
except Exception as e:
    report("Import get_llm", False, str(e))


# ===================================================================
# 2. PYDANTIC MODEL VALIDATION
# ===================================================================

print("\n[2] Pydantic Model Validation")

# Project info - valid
try:
    pi = ProjectInfoExtraction(
        project_name="Test Port",
        project_type="port",
        project_location=ProjectLocation(lat=19.82, lng=72.71),
        project_scope="A test port project.",
        project_constraints=["Seismic Zone III", "CRZ-I"],
        project_timeline="Phase I: 2024-2029",
    )
    d = pi.model_dump()
    assert d["project_name"] == "Test Port"
    report("ProjectInfoExtraction valid", True)
except Exception as e:
    report("ProjectInfoExtraction valid", False, str(e))

# Null coordinates
try:
    pi2 = ProjectInfoExtraction(
        project_name="Test",
        project_type="dam",
        project_location=ProjectLocation(lat=None, lng=None),
        project_scope="A test project.",
        project_constraints=[],
        project_timeline="TBD",
    )
    assert pi2.project_location.lat is None
    assert pi2.project_location.lng is None
    report("Null coordinates accepted", True)
except Exception as e:
    report("Null coordinates accepted", False, str(e))

# Missing required field
try:
    ProjectInfoExtraction(project_name="Test")
    report("Rejects missing fields", False, "No ValidationError")
except Exception:
    report("Rejects missing fields", True)

# Material - valid with nulls
try:
    mat = MaterialRequirement(
        material_name="Rock Armour",
        quantity=None,
        unit=None,
        specification=None,
        purpose="Breakwater",
        alternatives=[],
    )
    d = mat.model_dump()
    assert d["quantity"] is None
    assert d["specification"] is None
    report("MaterialRequirement null handling", True)
except Exception as e:
    report("MaterialRequirement null handling", False, str(e))

# Material - with values
try:
    mat2 = MaterialRequirement(
        material_name="Concrete",
        quantity=32.1,
        unit="million tonnes",
        specification="M40",
        purpose="Berth construction",
        alternatives=["M25"],
    )
    d2 = mat2.model_dump()
    assert d2["quantity"] == 32.1
    assert d2["specification"] == "M40"
    assert d2["alternatives"] == ["M25"]
    report("MaterialRequirement with values", True)
except Exception as e:
    report("MaterialRequirement with values", False, str(e))

# MaterialListExtraction wrapper
try:
    mle = MaterialListExtraction(materials=[mat, mat2])
    assert len(mle.materials) == 2
    report("MaterialListExtraction wrapper", True)
except Exception as e:
    report("MaterialListExtraction wrapper", False, str(e))


# ===================================================================
# 3. DOCUMENT INDEX RETRIEVAL (no LLM)
# ===================================================================

print("\n[3] Document Index Retrieval")

try:
    ctx = _retrieve_project_context()
    assert ctx.strip(), "Empty context"
    report("Project context retrieval", True)
except Exception as e:
    report("Project context retrieval", False, str(e))

# Check category coverage (at least 3 of 5 within the char limit)
try:
    found_cats = sum(
        1 for cat in [
            "Project Identity", "Project Location", "Project Scope",
            "Project Timeline", "Project Constraints",
        ]
        if cat in ctx
    )
    assert found_cats >= 3, f"Only {found_cats}/5 categories found"
    report(f"Category coverage ({found_cats}/5 in context)", True)
except Exception as e:
    report("Category coverage", False, str(e))

try:
    mctx = _retrieve_material_context()
    assert mctx.strip(), "Empty material context"
    report("Material context retrieval", True)
except Exception as e:
    report("Material context retrieval", False, str(e))

# Check material keywords appear
try:
    mctx_lower = mctx.lower()
    found = sum(
        1 for kw in ["rock", "concrete", "sand", "material", "armour"]
        if kw in mctx_lower
    )
    assert found >= 3, f"Only {found}/5 material keywords found"
    report("Material context contains relevant terms", True)
except Exception as e:
    report("Material context contains relevant terms", False, str(e))


# ===================================================================
# 4. SHARED STATE COMPATIBILITY
# ===================================================================

print("\n[4] Shared State Compatibility")

try:
    state_fields = set(InfraMinerState.__annotations__.keys())
    agent1_fields = {
        "project_name", "project_type", "project_location",
        "project_scope", "project_constraints", "project_timeline",
        "materials", "messages", "current_agent", "completed_agents",
    }
    missing = agent1_fields - state_fields
    assert not missing, f"Fields not in state: {missing}"
    report("All output fields exist in InfraMinerState", True)
except Exception as e:
    report("All output fields exist in InfraMinerState", False, str(e))


# ===================================================================
# 5. ERROR HANDLING (without LLM)
# ===================================================================

print("\n[5] Error Handling")

try:
    extract_project_info("")
    report("Rejects empty project text", False, "No error raised")
except ValueError:
    report("Rejects empty project text", True)
except Exception as e:
    report("Rejects empty project text", False, str(e))

try:
    extract_material_requirements("")
    report("Rejects empty material text", False, "No error raised")
except ValueError:
    report("Rejects empty material text", True)
except Exception as e:
    report("Rejects empty material text", False, str(e))


# ===================================================================
# 6. END-TO-END AGENT 1 (with real LLM)
# ===================================================================

print("\n[6] End-to-End Agent 1 Execution (LLM)")

from src.config import settings

if not settings.is_llm_configured:
    print(f"  SKIP: {settings.llm_provider.upper()} API key not set")
else:
    print(f"  Using LLM provider: {settings.llm_provider}")

    state: InfraMinerState = {}
    result = run_project_intelligence(state)

    # Check for errors
    errors = result.get("errors", [])
    if errors:
        for err in errors:
            report("Agent 1 execution", False, err)
    else:
        report("Agent 1 no errors", True)

        # Project fields
        for field in [
            "project_name", "project_type", "project_location",
            "project_scope", "project_constraints", "project_timeline",
        ]:
            val = result.get(field)
            if field == "project_location":
                ok = isinstance(val, dict) and "lat" in val and "lng" in val
            elif field == "project_constraints":
                ok = isinstance(val, list)
            else:
                ok = isinstance(val, str) and bool(val.strip())
            report(f"Field: {field}", ok, f"got: {type(val).__name__}")

        # Coordinates must not be fabricated as 0.0
        loc = result.get("project_location", {})
        if loc.get("lat") == 0.0 or loc.get("lng") == 0.0:
            report("Coordinates not fabricated", False, "0.0 detected")
        else:
            report("Coordinates not fabricated", True)

        # Materials
        materials = result.get("materials", [])
        report(
            f"Materials extracted ({len(materials)} items)",
            len(materials) >= 1,
        )

        if materials:
            for m in materials:
                if m.get("quantity") is not None:
                    assert isinstance(m["quantity"], (int, float))
                if m.get("unit") is not None:
                    assert isinstance(m["unit"], str)
            report("Material null/type handling", True)

            print("\n  --- Sample Materials ---")
            for m in materials[:5]:
                qty = m.get("quantity")
                unit = m.get("unit", "")
                spec = m.get("specification", "")
                print(
                    f"    {m['material_name']}: "
                    f"qty={qty} {unit or ''} | "
                    f"spec={spec or 'N/A'} | "
                    f"purpose={m.get('purpose', 'N/A')}"
                )

        # State metadata
        report(
            "current_agent set",
            result.get("current_agent") == "project_material_intelligence",
        )
        report(
            "completed_agents set",
            "project_material_intelligence"
            in result.get("completed_agents", []),
        )
        report("messages present", bool(result.get("messages")))

        # Print project info summary
        print("\n  --- Project Info ---")
        print(f"    Name: {result.get('project_name')}")
        print(f"    Type: {result.get('project_type')}")
        print(f"    Location: {result.get('project_location')}")
        constraints = result.get("project_constraints", [])
        print(f"    Constraints: {len(constraints)}")
        print(f"    Materials: {len(materials)}")

    # Save output for downstream agents
    output_dir = Path("data/outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "agent1_output.json"
    with output_file.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Output saved: {output_file}")


# ===================================================================
# FINAL REPORT
# ===================================================================

print("\n" + "=" * 70)
total = passed + failed
print(f"RESULTS: {passed}/{total} passed, {failed}/{total} failed")

if failed == 0:
    print("AGENT 1 VALIDATION PASSED")
else:
    print("AGENT 1 VALIDATION HAS FAILURES")
print("=" * 70)