from src.state import InfraMinerState
from agents.project_intelligence import run_project_intelligence
from agents.source_logistics import run_source_logistics

state = InfraMinerState()

# =========================
# AGENT 1
# =========================
state = run_project_intelligence(state)

print("\n===== AGENT 1 OUTPUT =====")
print("Project:", state.get("project_name"))
print("Type:", state.get("project_type"))
print("Location:", state.get("project_location"))
print("Materials:", len(state.get("materials", [])))

for m in state.get("materials", []):
    print("  -", m)

print("\n===== AGENT 2 RUNNING =====")

# =========================
# AGENT 2
# =========================
state = run_source_logistics(state)

print("\n===== AGENT 2 OUTPUT =====")
print("Sources:", len(state.get("sources", [])))
print("Routes:", len(state.get("routes", [])))
print("Errors:", state.get("errors", []))

print("\n===== REAL SOURCES =====")
for s in state.get("sources", [])[:20]:
    print(
        "  -",
        s.get("source_id"),
        "|",
        s.get("source_name"),
        "|",
        s.get("material")
    )

print("\n===== SAMPLE ROUTES =====")
for r in state.get("routes", [])[:10]:
    print(
        "  -",
        r.get("source_id"),
        "|",
        r.get("origin"),
        "->",
        r.get("destination"),
        "|",
        r.get("distance_km"),
        "km",
        "|",
        r.get("transport_mode")
    )
