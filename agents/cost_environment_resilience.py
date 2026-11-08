"""
InfraMiner AI - Agent 3: Cost, Environment & Resilience

Deterministic analysis agent. No LLM calls.

Consumes Agent 1 (materials) and Agent 2 (sources, routes) outputs
and produces cost estimates, environmental assessments, and
resilience assessments using datasets and Python calculations.

Supports both:
- Real documented Vadhavan datasets with document citations and NULL handling
  (verified_cost_data.csv, verified_environmental_factors.csv, verified_disruption_scenarios.csv)
- Demonstration datasets for baseline validation testing
  (cost_data.csv, environmental_factors.csv, disruption_scenarios.csv)

Cost formula:
    material_cost       = quantity * unit_cost (if both available)
    transportation_cost = quantity * distance_km * transport_rate (if all available)
    total_cost          = material_cost + transportation_cost

Environmental assessment:
    - Demo mode: weighted average of 5 impact dimension scores
    - Verified mode: document-cited environmental impact factors (e.g. forest land diversion,
      benthic disruption, channel deepening) with zero fabrication of synthetic scores.

Resilience assessment:
    - Demo mode: composite of scenario disruption, availability, and dependency
    - Verified mode: scenario linkage to documented risks (monsoon shutdown, forest clearance,
      single concession dependency) with documented availability and alternative dependency risk.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from src.state import InfraMinerState


# ===================================================================
# Data paths
# ===================================================================

_DATA_DIR = Path(__file__).resolve().parents[1] / "data"

DEMO_COST_DATA_PATH = _DATA_DIR / "costs" / "cost_data.csv"
VERIFIED_COST_DATA_PATH = _DATA_DIR / "costs" / "verified_cost_data.csv"
COST_DATA_PATH = DEMO_COST_DATA_PATH

DEMO_ENVIRONMENTAL_DATA_PATH = _DATA_DIR / "environmental" / "environmental_factors.csv"
VERIFIED_ENVIRONMENTAL_DATA_PATH = _DATA_DIR / "environmental" / "verified_environmental_factors.csv"
ENVIRONMENTAL_DATA_PATH = DEMO_ENVIRONMENTAL_DATA_PATH

DEMO_DISRUPTION_DATA_PATH = _DATA_DIR / "resilience" / "disruption_scenarios.csv"
VERIFIED_DISRUPTION_DATA_PATH = _DATA_DIR / "resilience" / "verified_disruption_scenarios.csv"
DISRUPTION_DATA_PATH = DEMO_DISRUPTION_DATA_PATH

AGENT3_PROVENANCE_PATH = _DATA_DIR / "agent3_provenance.csv"


def get_default_agent3_datasets(state: dict | None = None) -> tuple[Path, Path, Path]:
    """Determine datasets for Agent 3 based on state and project context."""
    cost_p = Path(state["cost_dataset_path"]) if state and state.get("cost_dataset_path") else None
    env_p = Path(state["environmental_dataset_path"]) if state and state.get("environmental_dataset_path") else None
    dis_p = Path(state["disruption_dataset_path"]) if state and state.get("disruption_dataset_path") else None

    is_vadhavan = False
    if state:
        pname = str(state.get("project_name", "")).lower()
        if "vadhavan" in pname:
            is_vadhavan = True
        sources = state.get("sources", [])
        if any(
            isinstance(s, dict) and (s.get("source_id", "").startswith("VAD-") or s.get("data_type") == "verified_document")
            for s in sources
        ):
            is_vadhavan = True

    if not cost_p:
        cost_p = VERIFIED_COST_DATA_PATH if (is_vadhavan and VERIFIED_COST_DATA_PATH.exists()) else DEMO_COST_DATA_PATH
    if not env_p:
        env_p = VERIFIED_ENVIRONMENTAL_DATA_PATH if (is_vadhavan and VERIFIED_ENVIRONMENTAL_DATA_PATH.exists()) else DEMO_ENVIRONMENTAL_DATA_PATH
    if not dis_p:
        dis_p = VERIFIED_DISRUPTION_DATA_PATH if (is_vadhavan and VERIFIED_DISRUPTION_DATA_PATH.exists()) else DEMO_DISRUPTION_DATA_PATH

    return cost_p, env_p, dis_p


# ===================================================================
# CSV loading utilities
# ===================================================================

def _load_csv(path: Path) -> list[dict[str, Any]]:
    """Load a CSV file into a list of dicts. Returns [] if missing."""
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cleaned: dict[str, Any] = {}
            for k, v in row.items():
                if k is None:
                    continue
                k = k.strip()
                v = v.strip() if v else ""
                cleaned[k] = v if v else None
            rows.append(cleaned)
    return rows


def _safe_float(val: Any) -> float | None:
    """Convert to float, returning None on failure."""
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


# ===================================================================
# PHASE 1: Cost Analysis
# ===================================================================

def load_cost_data(
    path: str | Path = COST_DATA_PATH,
) -> dict[str, dict[str, Any]]:
    """Load cost data keyed by material_category or material name (lowercase)."""
    rows = _load_csv(Path(path))
    costs: dict[str, dict[str, Any]] = {}

    # Check if this is the verified schema (has 'material' column)
    is_verified = bool(rows and "material" in rows[0])

    if not is_verified:
        for row in rows:
            cat = (row.get("material_category") or "").lower().strip()
            if not cat:
                continue
            costs[cat] = {
                "material_unit": row.get("material_unit"),
                "unit_cost": _safe_float(row.get("unit_cost")),
                "cost_currency": row.get("cost_currency", "INR"),
                "transport_rate_road": _safe_float(row.get("transport_rate_road")),
                "transport_rate_rail": _safe_float(row.get("transport_rate_rail")),
                "transport_rate_marine": _safe_float(row.get("transport_rate_marine")),
                "data_type": row.get("data_type", "assumption"),
                "notes": row.get("notes"),
            }
        return costs

    # Verified dataset parsing
    for row in rows:
        mat_raw = row.get("material") or ""
        mat = mat_raw.lower().strip()
        if not mat:
            continue

        cost_cat = (row.get("cost_category") or "").lower().strip()
        unit_cost = _safe_float(row.get("unit_cost"))
        currency = row.get("currency", "INR")
        unit = row.get("unit")
        data_type = row.get("data_type", "verified_document")
        confidence = row.get("confidence", "high")
        source_doc = row.get("source_document")
        doc_page = row.get("document_page")
        evidence = row.get("evidence_text")
        notes = row.get("notes")
        status = row.get("status") or ("verified" if data_type == "verified_document" else "unavailable")

        entry = {
            "material_name": mat_raw,
            "material_unit": unit,
            "cost_category": cost_cat,
            "unit_cost": unit_cost,
            "cost_currency": currency,
            "data_type": data_type,
            "confidence": confidence,
            "source_document": source_doc,
            "document_page": doc_page,
            "evidence_text": evidence,
            "status": status,
            "notes": notes,
            "transport_rate_road": None,
            "transport_rate_rail": None,
            "transport_rate_marine": None,
        }

        # Check for transport rates
        if cost_cat == "transport_rate" and unit_cost is not None:
            if "per_tonne_km" in str(unit):
                entry["transport_rate_road"] = unit_cost
            elif "per_m3_at_20km" in str(unit):
                entry["transport_rate_road_20km"] = unit_cost

        # Material deduplication: prioritize unit rates over capital block costs
        if mat in costs:
            existing = costs[mat]
            if cost_cat in ("derived_unit_cost", "schedule_of_rates_reference", "supplier_market_purchase_price"):
                costs[mat] = entry
            elif existing.get("unit_cost") is None and unit_cost is not None:
                costs[mat] = entry
        else:
            costs[mat] = entry

    return costs


def _match_cost_category(material_name: str, cost_data: dict) -> str | None:
    """Find the best matching cost category for a material name."""
    name_lower = material_name.lower().strip()
    name_words = set(
        name_lower.replace("/", " ").replace("-", " ").replace("(", " ").replace(")", " ").split()
    )

    # 1. Exact match
    if name_lower in cost_data:
        return name_lower

    # 2. Match whole category words within material name
    for cat in sorted(cost_data, key=len, reverse=True):
        cat_words = set(cat.replace("/", " ").replace("-", " ").replace("(", " ").replace(")", " ").split())
        if cat_words and cat_words <= name_words:
            return cat

    # 3. Substring containment
    for cat in sorted(cost_data, key=len, reverse=True):
        if cat in name_lower or name_lower in cat:
            return cat

    # 4. Domain keyword fallback
    # Rock / Stone / Basalt / Aggregate / Murrum / Armour
    if any(k in name_words for k in ["rock", "stone", "basalt", "armour", "armor", "murrum", "aggregate"]):
        for target in [
            "rock / breakwater material",
            "rock/stone",
            "aggregate",
            "armour",
            "murrum",
            "core rock / filter rock (<=20 kg)",
            "excavated rock / soling stone",
            "murrum / building rubbish / earth",
        ]:
            if target in cost_data:
                return target

    # Sand / Reclamation / Fill
    if any(k in name_words for k in ["sand", "reclamation", "fill"]):
        for target in [
            "marine sand / reclamation fill",
            "fill material",
            "sand",
            "fill material / earth / sand",
        ]:
            if target in cost_data:
                return target

    # Dredged material
    if any(k in name_words for k in ["dredged", "dredge"]):
        for target in ["dredged material / channel dredging", "dredged material"]:
            if target in cost_data:
                return target

    # Concrete armour unit / Accropode / Tetrapod
    if any(k in name_words for k in ["accropode", "tetrapod"]):
        for target in [
            "concrete armour unit (tetrapod m-30)",
            "rock / concrete armour units",
            "accropode",
            "concrete",
        ]:
            if target in cost_data:
                return target

    # Cement
    if "cement" in name_words:
        for target in ["cement (opc 43/53, ppc)", "cement"]:
            if target in cost_data:
                return target

    # Steel / TMT / Reinforcement
    if any(k in name_words for k in ["steel", "tmt", "reinforcement"]):
        for target in ["deformed steel bars (tmt fe500d)", "steel"]:
            if target in cost_data:
                return target

    # Geotextile
    if "geotextile" in name_words:
        for target in ["geotextile / filter fabric", "geotextile"]:
            if target in cost_data:
                return target

    # Concrete
    if "concrete" in name_words:
        for target in ["structural concrete (m-20)", "structural concrete (m-25)", "concrete"]:
            if target in cost_data:
                return target

    return None


def _get_transport_rate(
    cost_entry: dict, transport_mode: str | None
) -> float | None:
    """Get the transport rate for a given mode."""
    if not transport_mode:
        return cost_entry.get("transport_rate_road")
    mode = transport_mode.lower().strip()
    if mode == "road":
        return cost_entry.get("transport_rate_road")
    if mode == "rail":
        return cost_entry.get("transport_rate_rail")
    if mode in ("marine", "sea", "water"):
        return cost_entry.get("transport_rate_marine")
    return cost_entry.get("transport_rate_road")


def calculate_cost_estimate(
    source: dict,
    route: dict,
    material_quantity: float | None,
    cost_data: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Calculate cost estimate for a single source-route pair.

    Formulas:
        material_cost       = quantity * unit_cost
        transportation_cost = quantity * distance_km * transport_rate
        total_cost          = material_cost + transportation_cost
    """
    source_id = source.get("source_id", "unknown")
    source_name = source.get("source_name", "unknown")
    material_name = source.get("material_name", "unknown")
    distance_km = _safe_float(route.get("distance_km"))
    transport_mode = route.get("transport_mode")
    source_data_type = source.get("data_type", "demonstration")

    # Find cost category
    cost_cat = _match_cost_category(material_name, cost_data)
    cost_entry = cost_data.get(cost_cat) if cost_cat else None

    material_cost: float | None = None
    transportation_cost: float | None = None
    total_cost: float | None = None
    unit_cost: float | None = None
    transport_rate: float | None = None
    cost_data_type = "unavailable"
    calculation_notes: list[str] = []

    # Provenance fields
    source_document = None
    document_page = None
    evidence_text = None
    confidence = None
    cost_category = None
    cost_status = "unavailable"

    if cost_entry is None:
        calculation_notes.append(
            f"No cost data found for material: {material_name}"
        )
    else:
        unit_cost = cost_entry.get("unit_cost")
        transport_rate = _get_transport_rate(cost_entry, transport_mode)
        cost_data_type = cost_entry.get("data_type", "assumption")
        source_document = cost_entry.get("source_document")
        document_page = cost_entry.get("document_page")
        evidence_text = cost_entry.get("evidence_text")
        confidence = cost_entry.get("confidence")
        cost_category = cost_entry.get("cost_category")
        cost_status = cost_entry.get("status") or ("verified" if cost_data_type == "verified_document" else cost_data_type)

        # Material cost
        if material_quantity is not None and unit_cost is not None:
            material_cost = material_quantity * unit_cost
        else:
            if material_quantity is None:
                calculation_notes.append("Quantity unavailable")
            if unit_cost is None:
                calculation_notes.append("Unit cost unavailable in project document / left NULL to prevent fabrication")

        # Transportation cost
        if (
            material_quantity is not None
            and distance_km is not None
            and transport_rate is not None
            and transport_rate > 0
        ):
            transportation_cost = material_quantity * distance_km * transport_rate
        else:
            if distance_km is None:
                calculation_notes.append("Distance unavailable")
            if transport_rate is None or transport_rate == 0:
                calculation_notes.append("Transport rate per unit-km unavailable in project document")

        # Total cost
        if material_cost is not None and transportation_cost is not None:
            total_cost = material_cost + transportation_cost
        elif material_cost is not None:
            total_cost = material_cost
            calculation_notes.append(
                "Total is material cost only (transport unavailable)"
            )
        elif transportation_cost is not None:
            total_cost = transportation_cost
            calculation_notes.append(
                "Total is transport cost only (material cost unavailable)"
            )

    result = {
        "source_id": source_id,
        "source_name": source_name,
        "material_name": material_name,
        "quantity": material_quantity,
        "unit_cost": unit_cost,
        "material_cost": material_cost,
        "distance_km": distance_km,
        "transport_mode": transport_mode,
        "transport_rate": transport_rate,
        "transportation_cost": transportation_cost,
        "total_cost": total_cost,
        "cost_currency": "INR",
        "cost_data_type": cost_data_type,
        "source_data_type": source_data_type,
        "calculation_notes": "; ".join(calculation_notes) if calculation_notes else None,
    }

    # Add provenance fields if available
    if source_document:
        result["source_document"] = source_document
    if document_page:
        result["document_page"] = document_page
    if evidence_text:
        result["evidence_text"] = evidence_text
    if confidence:
        result["confidence"] = confidence
    if cost_category:
        result["cost_category"] = cost_category
    if cost_status:
        result["cost_status"] = cost_status

    return result


# ===================================================================
# PHASE 2: Environmental Assessment
# ===================================================================

def load_environmental_data(
    path: str | Path = ENVIRONMENTAL_DATA_PATH,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load environmental factors. Returns (source_factors, transport_factors)."""
    rows = _load_csv(Path(path))
    source_factors: dict[str, Any] = {}
    transport_factors: dict[str, Any] = {}

    is_verified = bool(rows and "environmental_factor" in rows[0])

    if not is_verified:
        for row in rows:
            category = (row.get("category") or "").lower().strip()
            cat_type = (row.get("category_type") or "").lower().strip()
            if not category:
                continue

            entry = {
                "dust_emission": _safe_float(row.get("dust_emission_score")) or 0.0,
                "noise": _safe_float(row.get("noise_score")) or 0.0,
                "water_impact": _safe_float(row.get("water_impact_score")) or 0.0,
                "habitat_disruption": _safe_float(row.get("habitat_disruption_score")) or 0.0,
                "carbon_intensity": _safe_float(row.get("carbon_intensity_score")) or 0.0,
                "regulatory_sensitivity": row.get("regulatory_sensitivity", "medium"),
                "data_type": row.get("data_type", "assumption"),
            }

            if cat_type == "source_type":
                source_factors[category] = entry
            elif cat_type == "transport_mode":
                transport_factors[category] = entry

        return source_factors, transport_factors

    # Verified environmental dataset
    for row in rows:
        stype = (row.get("source_type") or "").lower().strip()
        mat_src = (row.get("material_or_source") or "").strip()
        factor = (row.get("environmental_factor") or "").strip()
        val = _safe_float(row.get("impact_value"))
        unit = row.get("impact_unit")
        data_type = row.get("data_type", "verified_document")
        confidence = row.get("confidence", "high")
        status = row.get("status", "documented")
        source_doc = row.get("source_document")
        doc_page = row.get("document_page")
        evidence = row.get("evidence_text")
        notes = row.get("notes")

        record = {
            "source_type": stype,
            "material_or_source": mat_src,
            "environmental_factor": factor,
            "impact_description": row.get("impact_description"),
            "impact_value": val,
            "impact_unit": unit,
            "impact_direction": row.get("impact_direction"),
            "source_document": source_doc,
            "document_page": doc_page,
            "evidence_text": evidence,
            "data_type": data_type,
            "confidence": confidence,
            "status": status,
            "notes": notes,
        }

        # Index under transport_mode if stype is a transport mode
        if stype in ("road", "rail", "marine"):
            transport_factors.setdefault(stype, []).append(record)
        else:
            # Index under source_type
            source_factors.setdefault(stype, []).append(record)
            # Also index under specific source ID / name tokens
            if "vad-q01" in mat_src.lower():
                source_factors.setdefault("vad-q01", []).append(record)
            if "vad-q03" in mat_src.lower():
                source_factors.setdefault("vad-q03", []).append(record)
            if "vad-m01" in mat_src.lower():
                source_factors.setdefault("vad-m01", []).append(record)
            if "vad-d01" in mat_src.lower():
                source_factors.setdefault("vad-d01", []).append(record)

    return source_factors, transport_factors


def _compute_env_score(factors: dict) -> float:
    """Compute a composite environmental impact score (0-1)."""
    dimensions = [
        factors.get("dust_emission", 0.0),
        factors.get("noise", 0.0),
        factors.get("water_impact", 0.0),
        factors.get("habitat_disruption", 0.0),
        factors.get("carbon_intensity", 0.0),
    ]
    return round(sum(dimensions) / len(dimensions), 3) if dimensions else 0.0


def _regulatory_level(sensitivity: str | None) -> int:
    """Map regulatory sensitivity string to numeric level."""
    mapping = {"low": 1, "medium": 2, "high": 3}
    return mapping.get((sensitivity or "").lower().strip(), 2)


def calculate_environmental_assessment(
    source: dict,
    route: dict,
    source_factors: dict[str, Any],
    transport_factors: dict[str, Any],
) -> dict[str, Any]:
    """Calculate environmental assessment for a source-route pair.

    Handles demo mode (numerical 0-1 scores) and verified mode (document-supported factors).
    """
    source_id = source.get("source_id", "unknown")
    source_name = source.get("source_name", "unknown")
    source_type = (source.get("source_type") or "unknown").lower()
    transport_mode = (route.get("transport_mode") or "road").lower()
    distance_km = _safe_float(route.get("distance_km"))

    src_entry = source_factors.get(source_type, {})
    trn_entry = transport_factors.get(transport_mode, {})

    # Check if this is verified data (stored as lists of factor records)
    is_verified = isinstance(src_entry, list) or isinstance(trn_entry, list)

    if not is_verified:
        # Demo calculation
        source_score = _compute_env_score(src_entry) if isinstance(src_entry, dict) and src_entry else 0.5
        transport_score = _compute_env_score(trn_entry) if isinstance(trn_entry, dict) and trn_entry else 0.5
        combined_score = round(0.6 * source_score + 0.4 * transport_score, 3)

        src_reg = _regulatory_level(src_entry.get("regulatory_sensitivity") if isinstance(src_entry, dict) else None)
        trn_reg = _regulatory_level(trn_entry.get("regulatory_sensitivity") if isinstance(trn_entry, dict) else None)
        max_reg = max(src_reg, trn_reg)
        reg_labels = {1: "low", 2: "medium", 3: "high"}

        carbon_note = None
        if distance_km and distance_km > 500:
            carbon_note = "Long transport distance increases carbon footprint"

        data_type = src_entry.get("data_type", "assumption") if isinstance(src_entry, dict) and src_entry else "unavailable"

        return {
            "source_id": source_id,
            "source_name": source_name,
            "source_type": source_type,
            "transport_mode": transport_mode,
            "distance_km": distance_km,
            "source_impact_score": source_score,
            "transport_impact_score": transport_score,
            "combined_impact_score": combined_score,
            "impact_category": (
                "low" if combined_score < 0.33
                else "medium" if combined_score < 0.66
                else "high"
            ),
            "regulatory_sensitivity": reg_labels.get(max_reg, "medium"),
            "carbon_note": carbon_note,
            "data_type": data_type,
        }

    # Verified document assessment
    applicable_factors: list[dict] = []

    # Check source_id specific factors first (e.g. VAD-Q01 has forest diversion)
    sid_lower = source_id.lower()
    if sid_lower in source_factors and isinstance(source_factors[sid_lower], list):
        applicable_factors.extend(source_factors[sid_lower])

    # Add general source_type factors
    if source_type in source_factors and isinstance(source_factors[source_type], list):
        for f in source_factors[source_type]:
            if f not in applicable_factors:
                applicable_factors.append(f)

    # Add transport_mode factors
    if transport_mode in transport_factors and isinstance(transport_factors[transport_mode], list):
        for f in transport_factors[transport_mode]:
            applicable_factors.append(f)

    # Primary factor and regulatory status
    has_forest_clearance = any("forest" in f.get("environmental_factor", "") for f in applicable_factors)
    has_benthic = any("benthic" in f.get("environmental_factor", "") for f in applicable_factors)

    regulatory_sensitivity = "high" if (has_forest_clearance or has_benthic or source_type == "marine_borrow") else "medium"
    status = "regulatory_dependency" if has_forest_clearance else "documented"

    primary_f = applicable_factors[0] if applicable_factors else {}

    return {
        "source_id": source_id,
        "source_name": source_name,
        "source_type": source_type,
        "transport_mode": transport_mode,
        "distance_km": distance_km,
        "source_impact_score": None,  # Left NULL to prevent fabrication of synthetic 0-1 scores
        "transport_impact_score": None,
        "combined_impact_score": None,
        "impact_category": "documented",
        "regulatory_sensitivity": regulatory_sensitivity,
        "carbon_note": "Documented road transport combustion emissions" if transport_mode == "road" else "Zero terrestrial impact via marine transport" if transport_mode == "marine" else None,
        "data_type": "verified_document",
        "status": status,
        "factor_count": len(applicable_factors),
        "primary_environmental_factor": primary_f.get("environmental_factor"),
        "primary_impact_value": primary_f.get("impact_value"),
        "primary_impact_unit": primary_f.get("impact_unit"),
        "source_document": primary_f.get("source_document"),
        "document_page": primary_f.get("document_page"),
        "evidence_text": primary_f.get("evidence_text"),
        "confidence": "high",
        "applicable_factor_names": [f.get("environmental_factor") for f in applicable_factors if f.get("environmental_factor")],
    }


# ===================================================================
# PHASE 3: Resilience Assessment
# ===================================================================

def load_disruption_scenarios(
    path: str | Path = DISRUPTION_DATA_PATH,
) -> list[dict[str, Any]]:
    """Load disruption scenarios."""
    rows = _load_csv(Path(path))
    scenarios: list[dict[str, Any]] = []

    is_verified = bool(rows and "source_or_material" in rows[0])

    if not is_verified:
        for row in rows:
            scenarios.append({
                "scenario_id": row.get("scenario_id"),
                "scenario_name": row.get("scenario_name"),
                "description": row.get("description"),
                "affected_source_types": [
                    s.strip().lower()
                    for s in (row.get("affected_source_types") or "").split(";")
                    if s.strip()
                ],
                "affected_transport_modes": [
                    s.strip().lower()
                    for s in (row.get("affected_transport_modes") or "").split(";")
                    if s.strip()
                ],
                "probability": _safe_float(row.get("probability")) or 0.0,
                "severity": _safe_float(row.get("severity")) or 0.0,
                "data_type": row.get("data_type", "assumption"),
            })
        return scenarios

    # Verified disruption scenarios
    for row in rows:
        tokens = [
            s.strip().lower()
            for s in (row.get("source_or_material") or "").split(";")
            if s.strip()
        ]
        scenarios.append({
            "scenario_id": row.get("scenario_id"),
            "scenario_name": row.get("scenario_name"),
            "source_or_material": tokens,
            "risk_type": row.get("risk_type"),
            "description": row.get("description"),
            "probability": _safe_float(row.get("probability")),  # None for verified to prevent fabrication
            "severity": _safe_float(row.get("severity")),        # None for verified to prevent fabrication
            "source_document": row.get("source_document"),
            "document_page": row.get("document_page"),
            "evidence_text": row.get("evidence_text"),
            "data_type": row.get("data_type", "verified_document"),
            "confidence": row.get("confidence", "high"),
            "status": row.get("status", "documented"),
            "notes": row.get("notes"),
        })

    return scenarios


def _find_applicable_scenarios(
    source_type: str,
    transport_mode: str,
    scenarios: list[dict],
    source_id: str | None = None,
    material_name: str | None = None,
) -> list[dict]:
    """Find disruption scenarios that affect this source/transport combo."""
    applicable: list[dict] = []
    src_type = source_type.lower().strip()
    trn_mode = transport_mode.lower().strip()
    sid = (source_id or "").upper().strip()
    mat = (material_name or "").lower().strip()

    for sc in scenarios:
        # Demo schema check
        if "affected_source_types" in sc or "affected_transport_modes" in sc:
            src_match = (
                not sc.get("affected_source_types")
                or src_type in sc.get("affected_source_types", [])
            )
            trn_match = (
                not sc.get("affected_transport_modes")
                or trn_mode in sc.get("affected_transport_modes", [])
            )
            if src_match or trn_match:
                applicable.append(sc)
            continue

        # Verified schema check
        tokens = sc.get("source_or_material", [])
        matched = False

        # Specific source-scenario linkages
        sc_id = sc.get("scenario_id")
        if sc_id == "VAD-RS01" and (src_type in ("marine_borrow", "dredging") or "breakwater" in mat or "rock" in mat):
            matched = True
        elif sc_id == "VAD-RS02" and sid in ("VAD-Q01", "VAD-Q03"):
            matched = True
        elif sc_id == "VAD-RS03" and src_type == "quarry":
            matched = True
        elif sc_id == "VAD-RS04" and (src_type == "marine_borrow" or "sand" in mat):
            matched = True
        elif sc_id == "VAD-RS05" and (trn_mode == "road" or src_type == "quarry"):
            matched = True
        elif sc_id == "VAD-RS06" and (src_type in ("marine_borrow", "dredging") or "breakwater" in mat or "rock" in mat):
            matched = True
        elif sc_id == "VAD-RS07" and (trn_mode == "rail" or "cement" in mat or "steel" in mat):
            matched = True
        elif sc_id == "VAD-RS08" and src_type == "quarry" and sid not in ("VAD-Q01", "VAD-Q03"):
            matched = True
        elif sc_id == "VAD-RS09" and (src_type == "dredging" or "channel" in mat):
            matched = True

        # Token overlap fallback
        if not matched:
            for token in tokens:
                if token in src_type or token in trn_mode or token in mat:
                    matched = True
                    break

        if matched:
            applicable.append(sc)

    return applicable


def _count_alternatives(
    source_id: str,
    material_name: str,
    all_sources: list[dict],
) -> int:
    """Count how many alternative sources exist for the same material."""
    mat_lower = material_name.lower()
    count = 0
    for s in all_sources:
        if s.get("source_id") == source_id:
            continue
        src_mat = (s.get("material_name") or "").lower()
        if src_mat == mat_lower or mat_lower in src_mat or src_mat in mat_lower:
            count += 1
    return count


def calculate_resilience_assessment(
    source: dict,
    route: dict,
    all_sources: list[dict],
    scenarios: list[dict],
) -> dict[str, Any]:
    """Calculate resilience assessment for a source-route pair."""
    source_id = source.get("source_id", "unknown")
    source_name = source.get("source_name", "unknown")
    source_type = (source.get("source_type") or "unknown").lower()
    transport_mode = (route.get("transport_mode") or "road").lower()
    material_name = source.get("material_name", "unknown")
    operational_status = (source.get("operational_status") or "").lower()
    source_status = (source.get("status") or "").lower()

    # Applicable scenarios
    applicable = _find_applicable_scenarios(
        source_type, transport_mode, scenarios, source_id, material_name
    )

    is_verified = bool(scenarios and scenarios[0].get("data_type") == "verified_document")

    alt_count = _count_alternatives(source_id, material_name, all_sources)

    if not is_verified:
        # Demo calculation
        if applicable:
            disruption_scores = [
                (sc.get("probability") or 0.0) * (sc.get("severity") or 0.0)
                for sc in applicable
            ]
            disruption_risk = sum(disruption_scores) / len(disruption_scores)
        else:
            disruption_risk = 0.1

        if operational_status == "operational":
            availability_risk = 0.0
        elif operational_status == "planned":
            availability_risk = 0.5
        else:
            availability_risk = 1.0

        if alt_count >= 2:
            dependency_risk = 0.2
        elif alt_count == 1:
            dependency_risk = 0.5
        else:
            dependency_risk = 1.0

        disruption_risk = min(disruption_risk, 1.0)
        resilience_score = round(
            1.0 - (0.4 * disruption_risk + 0.3 * availability_risk + 0.3 * dependency_risk),
            3,
        )
        resilience_score = max(0.0, min(1.0, resilience_score))

        return {
            "source_id": source_id,
            "source_name": source_name,
            "material_name": material_name,
            "source_type": source_type,
            "transport_mode": transport_mode,
            "disruption_risk": round(disruption_risk, 3),
            "availability_risk": round(availability_risk, 3),
            "dependency_risk": round(dependency_risk, 3),
            "resilience_score": resilience_score,
            "resilience_category": (
                "high" if resilience_score >= 0.7
                else "medium" if resilience_score >= 0.4
                else "low"
            ),
            "alternative_count": alt_count,
            "fallback_feasible": alt_count >= 1,
            "fallback_note": (
                f"{alt_count} alternative source(s) available"
                if alt_count > 0
                else "No alternative sources identified"
            ),
            "applicable_scenarios": [sc.get("scenario_name") for sc in applicable],
            "scenario_count": len(applicable),
            "data_type": "assumption",
        }

    # Verified document resilience assessment
    # Numerical probability and severity are NOT fabricated
    disruption_risk = None

    # Availability risk based on documented regulatory dependency
    if source_status == "regulatory_dependency" or source_id in ("VAD-Q01", "VAD-Q03"):
        availability_risk = 0.8  # Documented pending Forest Clearance Stage-I/II
    elif source_status == "requires_current_verification":
        availability_risk = 0.5
    elif operational_status == "operational":
        availability_risk = 0.1
    else:
        availability_risk = 0.4

    # Single-source dependency
    if alt_count == 0:
        dependency_risk = 1.0  # e.g. Single concession dependency for sand borrow VAD-M01
    elif alt_count == 1:
        dependency_risk = 0.5
    else:
        dependency_risk = 0.2

    # Deterministic composite score based on documented operational availability & dependency
    resilience_score = round(1.0 - (0.5 * availability_risk + 0.5 * dependency_risk), 3)

    fallback_feasible = alt_count >= 1
    fallback_note = (
        f"{alt_count} alternative source(s) available"
        if alt_count > 0
        else "CRITICAL: Single concession dependency - no alternative sources identified (VAD-RS04)"
    )

    primary_sc = applicable[0] if applicable else {}

    return {
        "source_id": source_id,
        "source_name": source_name,
        "material_name": material_name,
        "source_type": source_type,
        "transport_mode": transport_mode,
        "disruption_risk": disruption_risk,  # Left NULL to prevent numerical fabrication
        "availability_risk": availability_risk,
        "dependency_risk": dependency_risk,
        "resilience_score": resilience_score,
        "resilience_category": (
            "high" if resilience_score >= 0.7
            else "medium" if resilience_score >= 0.4
            else "low"
        ),
        "alternative_count": alt_count,
        "fallback_feasible": fallback_feasible,
        "fallback_note": fallback_note,
        "applicable_scenarios": [sc.get("scenario_name") for sc in applicable if sc.get("scenario_name")],
        "scenario_count": len(applicable),
        "primary_scenario_id": primary_sc.get("scenario_id"),
        "primary_risk_type": primary_sc.get("risk_type"),
        "evidence_text": primary_sc.get("evidence_text"),
        "data_type": "verified_document",
        "confidence": "high",
    }


# ===================================================================
# Source-material quantity matching
# ===================================================================

def _find_material_quantity(
    source_material_name: str,
    materials: list[dict],
) -> float | None:
    """Find the quantity for a material from Agent 1 output."""
    src_lower = source_material_name.lower()
    src_normalized = src_lower.replace("/", " ").replace("-", " ")
    src_keywords = {
        w for w in src_normalized.split()
        if w not in {"for", "and", "the", "of", "a", "from", "to"}
    }

    best_qty: float | None = None

    for mat in materials:
        mat_name = (mat.get("material_name") or "").lower()
        mat_normalized = mat_name.replace("/", " ").replace("-", " ")

        # Exact match
        if mat_name == src_lower:
            qty = _safe_float(mat.get("quantity"))
            if qty is not None:
                return qty
            continue

        # Source name in material name or vice versa
        if src_lower in mat_name or mat_name in src_lower:
            qty = _safe_float(mat.get("quantity"))
            if qty is not None:
                return qty
            continue

        # Keyword overlap
        mat_keywords = {
            w for w in mat_normalized.split()
            if w not in {"for", "and", "the", "of", "a", "from", "to"}
        }
        overlap = src_keywords & mat_keywords
        if overlap and len(overlap) >= min(len(src_keywords), 1):
            qty = _safe_float(mat.get("quantity"))
            if qty is not None and (best_qty is None or qty > best_qty):
                best_qty = qty

    return best_qty


# ===================================================================
# LangGraph node - Agent 3: Cost, Environment & Resilience
# ===================================================================

def run_cost_environment_resilience(state: InfraMinerState) -> dict:
    """LangGraph node for Agent 3.

    Consumes:
        - materials (from Agent 1)
        - sources, routes (from Agent 2)

    Produces:
        - cost_estimates
        - environmental_assessments
        - resilience_assessments
        - messages, errors, current_agent, completed_agents
    """
    materials = state.get("materials", [])
    sources = state.get("sources", [])
    routes = state.get("routes", [])

    if not sources:
        return {
            "errors": [
                "Agent 3: No sources found in state. "
                "Ensure Agent 2 has completed."
            ],
            "current_agent": "cost_environment_resilience",
        }

    if not routes:
        return {
            "errors": [
                "Agent 3: No routes found in state. "
                "Ensure Agent 2 has completed."
            ],
            "current_agent": "cost_environment_resilience",
        }

    # Build source-to-route lookup
    route_by_source: dict[str, dict] = {}
    for rt in routes:
        sid = rt.get("source_id")
        if sid:
            route_by_source[sid] = rt

    # Resolve dataset paths based on state
    cost_path, env_path, dis_path = get_default_agent3_datasets(state)

    # Load datasets
    cost_data = load_cost_data(cost_path)
    source_factors, transport_factors = load_environmental_data(env_path)
    scenarios = load_disruption_scenarios(dis_path)

    cost_estimates: list[dict] = []
    env_assessments: list[dict] = []
    res_assessments: list[dict] = []
    messages_list: list[str] = []
    errors_list: list[str] = []

    for source in sources:
        source_id = source.get("source_id", "unknown")
        material_name = source.get("material_name", "unknown")
        route = route_by_source.get(source_id, {})

        # Find quantity from Agent 1 materials
        quantity = _find_material_quantity(material_name, materials)

        # Cost
        try:
            cost_est = calculate_cost_estimate(
                source, route, quantity, cost_data
            )
            cost_estimates.append(cost_est)
        except Exception as exc:
            errors_list.append(
                f"Agent 3 cost error ({source_id}): {exc}"
            )

        # Environmental
        try:
            env_est = calculate_environmental_assessment(
                source, route, source_factors, transport_factors
            )
            env_assessments.append(env_est)
        except Exception as exc:
            errors_list.append(
                f"Agent 3 env error ({source_id}): {exc}"
            )

        # Resilience
        try:
            res_est = calculate_resilience_assessment(
                source, route, sources, scenarios
            )
            res_assessments.append(res_est)
        except Exception as exc:
            errors_list.append(
                f"Agent 3 resilience error ({source_id}): {exc}"
            )

    messages_list.append(
        f"Agent 3: Computed {len(cost_estimates)} cost estimate(s), "
        f"{len(env_assessments)} environmental assessment(s), "
        f"{len(res_assessments)} resilience assessment(s)."
    )

    result: dict = {
        "cost_estimates": cost_estimates,
        "environmental_assessments": env_assessments,
        "resilience_assessments": res_assessments,
        "messages": messages_list,
        "current_agent": "cost_environment_resilience",
        "completed_agents": ["cost_environment_resilience"],
    }

    if errors_list:
        result["errors"] = errors_list

    return result
