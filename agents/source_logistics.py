"""
InfraMiner AI — Agent 2: Source & Logistics

Discovers candidate material sources and calculates logistics
information for each material requirement from Agent 1.

This agent:
1. Reads material requirements from shared state (Agent 1 output).
2. Matches materials to candidate sources from the source dataset.
3. Calculates distances using the Haversine formula.
4. Determines transport mode, route, and logistics details.
5. Returns structured source and route information.

Does NOT fabricate source data — uses only the dataset records.
"""

from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.config import settings
from src.state import InfraMinerState


# ===================================================================
# PYDANTIC MODELS
# ===================================================================

class MaterialSource(BaseModel):
    """A candidate source for a specific material."""

    source_id: str = Field(description="Unique source identifier.")
    source_name: str = Field(description="Name of the source.")
    source_type: str = Field(
        description="Type: quarry, supplier, marine_borrow, dredging, etc."
    )
    material_name: str = Field(description="Material this source provides.")
    material_specification: str | None = Field(
        default=None,
        description="Material specification/grade if known.",
    )
    latitude: float | None = Field(default=None)
    longitude: float | None = Field(default=None)
    available_quantity: float | None = Field(
        default=None,
        description="Available quantity. Null if unknown.",
    )
    quantity_unit: str | None = Field(default=None)
    availability_status: str | None = Field(default=None)
    status: str | None = Field(default=None)
    operational_status: str | None = Field(default=None)
    quality_notes: str | None = Field(default=None)
    source_reference: str | None = Field(default=None)
    data_type: str = Field(
        default="demonstration",
        description="Provenance: document_evidence, demonstration, etc.",
    )
    project_document: str | None = Field(default=None)
    document_page: int | str | None = Field(default=None)
    evidence_text: str | None = Field(default=None)
    confidence: str | float | None = Field(default=None)
    location_description: str | None = Field(default=None)


class LogisticsRoute(BaseModel):
    """Logistics information for a source-to-project route."""

    source_id: str = Field(description="Source identifier.")
    source_name: str = Field(description="Source name.")
    material_name: str = Field(description="Material being transported.")
    origin_lat: float | None = Field(default=None)
    origin_lng: float | None = Field(default=None)
    destination_lat: float | None = Field(default=None)
    destination_lng: float | None = Field(default=None)
    distance_km: float | None = Field(
        default=None,
        description="Distance in km (Haversine or from dataset).",
    )
    transport_mode: str | None = Field(
        default=None,
        description="road, rail, marine, or multimodal.",
    )
    logistics_notes: str | None = Field(default=None)
    distance_source: str = Field(
        default="haversine_calculation",
        description="How distance was determined.",
    )


# ===================================================================
# CONSTANTS
# ===================================================================

# Default project location (Vadhavan Port site)
# Used when project_location is not available from Agent 1
DEFAULT_PROJECT_LOCATION = {"lat": 19.82, "lng": 72.71}

DEMO_SOURCE_DATA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "sources" / "material_sources.csv"
)

VERIFIED_SOURCE_DATA_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "sources" / "verified_material_sources.csv"
)

# Default dataset for Vadhavan project
SOURCE_DATA_PATH = VERIFIED_SOURCE_DATA_PATH


def get_default_source_dataset(state: InfraMinerState | dict | None = None) -> Path:
    """Determine the source dataset path based on state and project context.

    Precedence:
    1. Explicit 'source_dataset_path' in state (allows explicit demo or custom data).
    2. Verified Vadhavan dataset if project is Vadhavan or default.
    3. Fallback to demonstration dataset if verified dataset is missing.
    """
    if state and isinstance(state, dict):
        explicit_path = state.get("source_dataset_path")
        if explicit_path:
            return Path(explicit_path)

        proj_name = (state.get("project_name") or "").lower()
        if "vadhavan" in proj_name:
            if VERIFIED_SOURCE_DATA_PATH.exists():
                return VERIFIED_SOURCE_DATA_PATH

    if VERIFIED_SOURCE_DATA_PATH.exists():
        return VERIFIED_SOURCE_DATA_PATH

    return DEMO_SOURCE_DATA_PATH


# ===================================================================
# HAVERSINE DISTANCE
# ===================================================================

def haversine_distance(
    lat1: float, lng1: float,
    lat2: float, lng2: float,
) -> float:
    """Calculate distance between two points using Haversine formula.

    Returns distance in kilometres.
    """
    R = 6371.0  # Earth radius in km

    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r)
        * math.sin(dlng / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return round(R * c, 2)


# ===================================================================
# SOURCE DATA LOADING
# ===================================================================

def load_source_data(
    csv_path: str | Path = SOURCE_DATA_PATH,
) -> list[dict[str, Any]]:
    """Load material source records from CSV.

    Returns
    -------
    list[dict]
        List of source records. Empty list if file not found.
    """
    path = Path(csv_path).resolve()

    if not path.exists():
        return []

    sources: list[dict[str, Any]] = []

    with path.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse numeric fields
            record: dict[str, Any] = {}
            for key, value in row.items():
                if key is None:
                    continue
                key = key.strip()
                value = value.strip() if value else ""

                if key in (
                    "latitude",
                    "longitude",
                    "available_quantity",
                    "capacity_or_quantity",
                    "distance_km",
                ):
                    record[key] = float(value) if value else None
                elif key == "document_page":
                    try:
                        record[key] = int(value) if value else None
                    except ValueError:
                        record[key] = value if value else None
                elif key == "confidence":
                    try:
                        record[key] = float(value) if value else None
                    except ValueError:
                        record[key] = value if value else None
                else:
                    record[key] = value if value else None

            # Fallback alias mappings so both demo and verified schemas work seamlessly
            if not record.get("material_name") and record.get("material"):
                record["material_name"] = record["material"]
            if not record.get("material_specification") and record.get("specification"):
                record["material_specification"] = record["specification"]
            if record.get("available_quantity") is None and record.get("capacity_or_quantity") is not None:
                record["available_quantity"] = record["capacity_or_quantity"]
            if not record.get("quantity_unit") and record.get("capacity_unit"):
                record["quantity_unit"] = record["capacity_unit"]
            if not record.get("status") and record.get("operational_status"):
                record["status"] = record["operational_status"]
            if not record.get("operational_status") and record.get("status"):
                record["operational_status"] = record["status"]
            if not record.get("quality_notes") and record.get("notes"):
                record["quality_notes"] = record["notes"]
            if not record.get("data_type"):
                if record.get("project_document"):
                    record["data_type"] = "document_evidence"
                else:
                    record["data_type"] = "demonstration"

            sources.append(record)

    return sources


# ===================================================================
# SOURCE MATCHING
# ===================================================================

def _normalize(name: str) -> str:
    """Normalize a material name for fuzzy matching."""
    return name.lower().strip().replace("-", " ").replace("/", " ")


def _material_matches(
    source_material: str,
    required_material: str,
) -> bool:
    """Check if a source material matches a required material.

    Uses simple keyword overlap matching.
    """
    src = _normalize(source_material)
    req = _normalize(required_material)

    # Exact match
    if src == req:
        return True

    # Check if key words overlap
    src_words = set(src.split())
    req_words = set(req.split())

    # If any significant word overlaps
    common = src_words & req_words
    # Filter out very generic words and role/purpose words
    stopwords = {
        "for", "and", "the", "of", "a", "in", "material", "type",
        "reclamation", "construction", "purpose", "suitable", "works",
    }
    significant = common - stopwords

    return len(significant) >= 1


def find_sources_for_material(
    material_name: str,
    material_spec: str | None,
    all_sources: list[dict],
) -> list[dict]:
    """Find source records matching a required material."""

    matches: list[dict] = []

    for source in all_sources:
        src_material = source.get("material_name", "")
        if not src_material:
            continue

        if _material_matches(src_material, material_name):
            # Optionally filter by spec if both are available
            src_spec = source.get("material_specification")
            if material_spec and src_spec:
                if _normalize(material_spec) not in _normalize(src_spec):
                    # Spec mismatch — still include but note it
                    source = {**source, "quality_notes": (
                        f"{source.get('quality_notes', '')}; "
                        f"Spec mismatch: required={material_spec}"
                    ).strip("; ")}

            matches.append(source)

    return matches


# ===================================================================
# LOGISTICS CALCULATION
# ===================================================================

def calculate_logistics(
    source: dict,
    project_location: dict,
) -> dict:
    """Calculate logistics for a source-to-project route."""

    src_lat = source.get("latitude")
    src_lng = source.get("longitude")
    dst_lat = project_location.get("lat")
    dst_lng = project_location.get("lng")

    distance_km = None
    distance_source = "unavailable"

    # Use dataset distance if available
    if source.get("distance_km"):
        distance_km = source["distance_km"]
        distance_source = "dataset"

    # Calculate Haversine distance if coordinates available
    elif (
        src_lat is not None and src_lng is not None
        and dst_lat is not None and dst_lng is not None
    ):
        distance_km = haversine_distance(src_lat, src_lng, dst_lat, dst_lng)
        distance_source = "haversine_calculation"

    transport_mode = source.get("transport_mode")

    # Generate logistics notes
    notes_parts: list[str] = []
    if source.get("data_type") == "demonstration":
        notes_parts.append("DEMO DATA: Source record is demonstration data")
    if source.get("operational_status") == "planned":
        notes_parts.append("Source is planned, not yet operational")
    if distance_km and distance_km > 500:
        notes_parts.append("Long-distance transport — consider rail or marine")

    route = LogisticsRoute(
        source_id=source.get("source_id", "unknown"),
        source_name=source.get("source_name", "unknown"),
        material_name=source.get("material_name", "unknown"),
        origin_lat=src_lat,
        origin_lng=src_lng,
        destination_lat=dst_lat,
        destination_lng=dst_lng,
        distance_km=distance_km,
        transport_mode=transport_mode,
        logistics_notes="; ".join(notes_parts) if notes_parts else None,
        distance_source=distance_source,
    )

    return route.model_dump()


# ===================================================================
# CORE DISCOVERY FUNCTION
# ===================================================================

def discover_sources(
    materials: list[dict],
    project_location: dict | None = None,
    source_data_path: str | Path = SOURCE_DATA_PATH,
) -> tuple[list[dict], list[dict], list[str]]:
    """Discover sources and logistics for given material requirements.

    Parameters
    ----------
    materials : list[dict]
        Material requirements from Agent 1.
    project_location : dict | None
        Project coordinates {"lat": float, "lng": float}.
    source_data_path : str | Path
        Path to source data CSV.

    Returns
    -------
    tuple[list[dict], list[dict], list[str]]
        (sources, routes, messages)
    """
    # Load source dataset
    all_sources = load_source_data(source_data_path)

    if not all_sources:
        return [], [], [
            "Agent 2: No source data found. "
            "Populate data/sources/material_sources.csv."
        ]

    # Determine project location
    loc = project_location or DEFAULT_PROJECT_LOCATION
    if loc.get("lat") is None or loc.get("lng") is None:
        loc = DEFAULT_PROJECT_LOCATION

    sources: list[dict] = []
    routes: list[dict] = []
    messages: list[str] = []
    matched_materials: set[str] = set()
    unmatched_materials: list[str] = []

    for material in materials:
        mat_name = material.get("material_name", "")
        mat_spec = material.get("specification")

        matches = find_sources_for_material(
            mat_name, mat_spec, all_sources
        )

        if matches:
            matched_materials.add(mat_name)
            for src in matches:
                # Build MaterialSource
                ms = MaterialSource(
                    source_id=src.get("source_id", "unknown"),
                    source_name=src.get("source_name", "unknown"),
                    source_type=src.get("source_type", "unknown"),
                    material_name=src.get("material_name", mat_name),
                    material_specification=src.get("material_specification"),
                    latitude=src.get("latitude"),
                    longitude=src.get("longitude"),
                    available_quantity=src.get("available_quantity"),
                    quantity_unit=src.get("quantity_unit"),
                    availability_status=src.get("availability_status"),
                    status=src.get("status") or src.get("operational_status"),
                    operational_status=src.get("operational_status") or src.get("status"),
                    quality_notes=src.get("quality_notes"),
                    source_reference=src.get("source_reference"),
                    data_type=src.get("data_type", "demonstration"),
                    project_document=src.get("project_document"),
                    document_page=src.get("document_page"),
                    evidence_text=src.get("evidence_text"),
                    confidence=src.get("confidence"),
                    location_description=src.get("location_description"),
                )
                sources.append(ms.model_dump())

                # Calculate logistics
                route = calculate_logistics(src, loc)
                routes.append(route)
        else:
            unmatched_materials.append(mat_name)

    messages.append(
        f"Agent 2: Matched {len(matched_materials)} material(s) "
        f"to {len(sources)} source(s)."
    )

    if unmatched_materials:
        messages.append(
            f"Agent 2: No sources found for: "
            f"{', '.join(unmatched_materials[:5])}"
            + (f" (+{len(unmatched_materials)-5} more)"
               if len(unmatched_materials) > 5 else "")
        )

    return sources, routes, messages


# ===================================================================
# LANGGRAPH NODE — Agent 2: Source & Logistics
# ===================================================================

def run_source_logistics(state: InfraMinerState) -> dict:
    """LangGraph node: Agent 2 — Source & Logistics.

    Reads materials from Agent 1's output, discovers sources,
    and calculates logistics.
    """

    # 1. Get materials from state
    materials = state.get("materials", [])

    if not materials:
        return {
            "errors": [
                "Agent 2: No materials found in state. "
                "Ensure Agent 1 has completed successfully."
            ],
            "current_agent": "source_logistics",
        }

    # 2. Get project location
    project_location = state.get("project_location")

    # 3. Determine source dataset path (configurable via state, defaults to verified Vadhavan dataset)
    source_data_path = get_default_source_dataset(state)

    # 4. Discover sources
    try:
        sources, routes, messages = discover_sources(
            materials=materials,
            project_location=project_location,
            source_data_path=source_data_path,
        )
    except Exception as exc:
        return {
            "errors": [f"Agent 2: Source discovery failed — {exc}"],
            "current_agent": "source_logistics",
        }

    # 4. Build result
    result: dict = {
        "sources": sources,
        "routes": routes,
        "messages": messages,
        "current_agent": "source_logistics",
        "completed_agents": ["source_logistics"],
    }

    if not sources:
        result["errors"] = [
            "Agent 2: No matching sources found for any material."
        ]

    return result

