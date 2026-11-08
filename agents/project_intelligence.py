"""
InfraMiner AI - Agent 1: Project & Material Intelligence

Combines Project Intelligence and Material Requirement extraction.
Reads the persistent document index, retrieves relevant DPR context,
and extracts both project information and material requirements
using the configured LLM with Pydantic structured output.
"""

from __future__ import annotations

import json
import time

from pydantic import BaseModel, Field

from src.config import settings
from src.llm.factory import get_llm
from src.state import InfraMinerState
from src.utils.document_index import search_document_index


# ===================================================================
# Pydantic models - Project Intelligence
# ===================================================================

class ProjectLocation(BaseModel):
    """Project geographic coordinates."""

    lat: float | None = Field(
        default=None,
        description=(
            "Latitude in decimal degrees if explicitly present "
            "in the document; otherwise null."
        ),
    )
    lng: float | None = Field(
        default=None,
        description=(
            "Longitude in decimal degrees if explicitly present "
            "in the document; otherwise null."
        ),
    )


class ProjectInfoExtraction(BaseModel):
    """Structured project information extracted from a DPR."""

    project_name: str = Field(
        description="Official project name stated in the document."
    )
    project_type: str = Field(
        description=(
            "Type of infrastructure project stated or explicitly "
            "described in the document."
        )
    )
    project_location: ProjectLocation = Field(
        description=(
            "Project coordinates. Use only explicitly documented "
            "latitude and longitude values."
        )
    )
    project_scope: str = Field(
        description=(
            "Summary of major project components and development "
            "scope supported by the document."
        )
    )
    project_constraints: list[str] = Field(
        description=(
            "Environmental, regulatory, technical, climatic, "
            "seismic, and other constraints explicitly mentioned."
        )
    )
    project_timeline: str = Field(
        description=(
            "Project phases, construction schedule, completion dates, "
            "and target years explicitly mentioned."
        )
    )


# ===================================================================
# Pydantic models - Material Requirement
# ===================================================================

class MaterialRequirement(BaseModel):
    """A single material required for the infrastructure project."""

    material_name: str = Field(
        description="Name of the material."
    )
    quantity: float | None = Field(
        default=None,
        description=(
            "Quantity required. Null if not explicitly stated. "
            "Do NOT invent quantities."
        ),
    )
    unit: str | None = Field(
        default=None,
        description="Unit of measurement. Null if unknown.",
    )
    specification: str | None = Field(
        default=None,
        description=(
            "Material specification or grade. Null if not explicitly "
            "mentioned. Do NOT fabricate specifications."
        ),
    )
    purpose: str | None = Field(
        default=None,
        description="Construction purpose for this material.",
    )
    alternatives: list[str] = Field(
        default_factory=list,
        description="Documented alternative materials. Empty if none.",
    )


class MaterialListExtraction(BaseModel):
    """Wrapper for LLM extraction of a list of materials."""

    materials: list[MaterialRequirement] = Field(default_factory=list)


# ===================================================================
# System prompts
# ===================================================================

_PROJECT_SYSTEM_PROMPT = """\
You are the Project Intelligence Agent of InfraMiner AI.

Extract information ONLY from the supplied DPR context.

STRICT RULES:
1. Do not use outside knowledge.
2. Do not invent missing information.
3. Do not estimate or guess values.
4. Latitude and longitude must be explicitly present. If not, return null.
5. Never use 0.0 as a placeholder for missing coordinates.
6. Preserve documented numbers, dates, units, names, and terminology.
7. Project scope must contain only information supported by the context.
8. Project constraints must contain only explicitly documented constraints.
9. Project timeline must contain only documented phases and target years.
10. If a field is not supported, provide an empty or neutral value.
"""

_MATERIAL_SYSTEM_PROMPT = """\
You are the Material Requirement Agent in InfraMiner AI.

Extract ONLY material requirements explicitly documented in the DPR context.

Rules:
1. Use only the supplied context. Never use outside knowledge.
2. Never invent, estimate, calculate, infer, or guess quantities.
3. If quantity or unit is not explicitly stated, use null.
4. Preserve numerical values, units, grades, sizes, standards, and names.
5. Alternatives must be explicitly documented.
6. Exclude equipment, machinery, vehicles, labour, services, and software.
7. Do not treat an incidental mention as a requirement.
8. Do not combine separate quantities unless the source explicitly combines them.
"""


# ===================================================================
# Retrieval keywords
# ===================================================================

PROJECT_IDENTITY_KEYWORDS = [
    "project", "greenfield", "port", "project description",
    "project overview", "development",
]

PROJECT_LOCATION_KEYWORDS = [
    "location", "site", "latitude", "longitude",
    "coordinates", "geographic",
]

PROJECT_SCOPE_KEYWORDS = [
    "project scope", "development", "berth", "breakwater",
    "reclamation", "infrastructure", "terminal", "dredging",
]

PROJECT_TIMELINE_KEYWORDS = [
    "phase", "phases", "timeline", "construction",
    "completion", "implementation", "target year",
]

PROJECT_CONSTRAINT_KEYWORDS = [
    "constraint", "environmental", "regulatory", "CRZ",
    "seismic", "climate", "restriction", "clearance",
]

MATERIAL_KEYWORDS = [
    "material", "materials", "rock", "rock armour", "concrete",
    "cement", "aggregate", "sand", "steel", "reinforcement",
    "stone", "quarry", "reclamation", "fill", "armour",
    "breakwater", "dredged material", "accropode", "geotextile",
]


# ===================================================================
# LLM invocation with retry
# ===================================================================

def _invoke_llm_with_retry(structured_llm, messages, max_retries: int = 3):
    """Invoke the structured LLM with retry for temporary errors."""

    last_error = None

    for attempt in range(max_retries):
        try:
            return structured_llm.invoke(messages)
        except Exception as exc:
            last_error = exc
            error_text = str(exc).upper()

            temporary = any(
                marker in error_text
                for marker in [
                    "429", "RATE LIMIT", "RESOURCE_EXHAUSTED",
                    "503", "UNAVAILABLE", "TIMEOUT", "TIMED OUT",
                ]
            )

            if not temporary:
                raise

            if attempt < max_retries - 1:
                wait = 5 * (attempt + 1)
                print(
                    f"  LLM temporarily unavailable. "
                    f"Retrying in {wait}s..."
                )
                time.sleep(wait)

    raise RuntimeError(
        f"LLM remained unavailable after {max_retries} attempts: "
        f"{last_error}"
    )


# ===================================================================
# Retrieval functions
# ===================================================================

def _retrieve_project_context(
    max_pages_per_category: int = 4,
    max_total_chars: int = 20000,
) -> str:
    """Retrieve balanced project context from the persistent index."""

    keyword_groups = [
        ("Project Identity", PROJECT_IDENTITY_KEYWORDS),
        ("Project Location", PROJECT_LOCATION_KEYWORDS),
        ("Project Scope", PROJECT_SCOPE_KEYWORDS),
        ("Project Timeline", PROJECT_TIMELINE_KEYWORDS),
        ("Project Constraints", PROJECT_CONSTRAINT_KEYWORDS),
    ]

    selected: dict[tuple[str, int], dict] = {}

    for category, keywords in keyword_groups:
        results = search_document_index(
            keywords=keywords,
            max_pages=max_pages_per_category,
        )
        for result in results:
            key = (result["document_name"], result["page"])
            if key not in selected:
                selected[key] = {
                    "document_name": result["document_name"],
                    "page": result["page"],
                    "score": result["score"],
                    "text": result["text"],
                    "categories": [category],
                }
            else:
                if category not in selected[key]["categories"]:
                    selected[key]["categories"].append(category)

    # Organize pages by category
    category_pages: dict[str, list[dict]] = {
        cat: [] for cat, _ in keyword_groups
    }
    for page in selected.values():
        for cat in page["categories"]:
            category_pages[cat].append(page)
    for cat in category_pages:
        category_pages[cat].sort(key=lambda x: -x["score"])

    # Build ordered page list - guarantee representation from every category.
    # Round-robin: first add the #1 page for each category, then #2, then
    # fill remaining by score.  This prevents high-overlap categories
    # (Identity/Scope) from consuming all slots before Timeline/Constraints
    # get any dedicated pages.
    ordered_pages: list[dict] = []
    already_added: set[tuple[str, int]] = set()

    # Pass 1: best page per category (guarantees all 5 categories)
    for cat, _ in keyword_groups:
        for page in category_pages[cat]:
            key = (page["document_name"], page["page"])
            if key not in already_added:
                ordered_pages.append(page)
                already_added.add(key)
                break  # only 1 page per category in this pass

    # Pass 2: second-best page per category
    for cat, _ in keyword_groups:
        count = 0
        for page in category_pages[cat]:
            key = (page["document_name"], page["page"])
            if key not in already_added:
                ordered_pages.append(page)
                already_added.add(key)
                count += 1
                if count >= 1:
                    break

    # Pass 3: remaining high-relevance pages
    for page in sorted(selected.values(), key=lambda x: -x["score"]):
        key = (page["document_name"], page["page"])
        if key not in already_added:
            ordered_pages.append(page)
            already_added.add(key)

    # Build bounded context string
    context_parts: list[str] = []
    total_chars = 0

    for page in ordered_pages:
        page_ctx = (
            f"[Document: {page['document_name']} | "
            f"Page: {page['page']} | "
            f"Categories: {', '.join(page['categories'])}]\n"
            f"{page['text']}"
        )
        remaining = max_total_chars - total_chars
        if remaining <= 0:
            break
        if len(page_ctx) <= remaining:
            context_parts.append(page_ctx)
            total_chars += len(page_ctx)
        elif remaining > 500:
            context_parts.append(page_ctx[:remaining])
            total_chars += remaining
            break
        else:
            break

    return "\n\n---\n\n".join(context_parts)


def _retrieve_material_context(
    max_pages: int = 15,
    max_total_chars: int = 12000,
) -> str:
    """Retrieve material-relevant context from the persistent index."""

    pages = search_document_index(
        MATERIAL_KEYWORDS,
        max_pages=max_pages,
    )

    if not pages:
        raise ValueError(
            "No material-related context found in document index."
        )

    sections: list[str] = []
    total_chars = 0

    for page in pages:
        page_number = page.get("page", "?")
        text = page.get("text", "").strip()
        if not text:
            continue

        section = f"--- DPR Page {page_number} ---\n{text}\n"

        if total_chars + len(section) > max_total_chars:
            remaining = max_total_chars - total_chars
            if remaining > 100:
                sections.append(section[:remaining])
            break

        sections.append(section)
        total_chars += len(section)

    context = "\n".join(sections)
    if not context.strip():
        raise ValueError("Retrieved material context is empty.")

    return context


# ===================================================================
# Extraction functions
# ===================================================================

def _clean_unicode_str(val: str) -> str:
    """Normalize unicode characters that cause issues on Windows console (cp1252)."""
    if not isinstance(val, str):
        return val
    # Replace non-breaking hyphens, en-dashes, em-dashes
    s = val.replace("\u2011", "-").replace("\u2013", "-").replace("\u2014", "-")
    # Replace smart/curly quotes
    s = s.replace("\u2018", "'").replace("\u2019", "'").replace("\u201c", '"').replace("\u201d", '"')
    return s


def _clean_dict_strings(data: any) -> any:
    """Recursively clean unicode strings in dicts, lists, and primitives."""
    if isinstance(data, str):
        return _clean_unicode_str(data)
    elif isinstance(data, dict):
        return {k: _clean_dict_strings(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_clean_dict_strings(item) for item in data]
    return data


def _parse_and_validate_materials_json(json_text: str) -> list[dict]:
    """Safely parse a JSON string and validate against MaterialRequirement schema.

    Rejects malformed or truncated JSON. Does NOT fabricate missing values.
    """
    if not json_text or not json_text.strip():
        raise ValueError("JSON response is empty.")

    cleaned = json_text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        start_idx = 1
        end_idx = len(lines)
        if lines[-1].strip() == "```":
            end_idx = len(lines) - 1
        cleaned = "\n".join(lines[start_idx:end_idx]).strip()

    first_brace = cleaned.find("{")
    first_bracket = cleaned.find("[")

    parsed_data = None
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        last_brace = cleaned.rfind("}")
        if last_brace == -1 or last_brace < first_brace:
            raise ValueError("Truncated or malformed JSON object (missing closing brace).")
        json_slice = cleaned[first_brace : last_brace + 1]
        parsed_data = json.loads(json_slice)
    elif first_bracket != -1:
        last_bracket = cleaned.rfind("]")
        if last_bracket == -1 or last_bracket < first_bracket:
            raise ValueError("Truncated or malformed JSON array (missing closing bracket).")
        json_slice = cleaned[first_bracket : last_bracket + 1]
        parsed_data = json.loads(json_slice)
    else:
        parsed_data = json.loads(cleaned)

    materials_list = []
    if isinstance(parsed_data, dict):
        if "materials" in parsed_data and isinstance(parsed_data["materials"], list):
            materials_list = parsed_data["materials"]
        elif "requirements" in parsed_data and isinstance(parsed_data["requirements"], list):
            materials_list = parsed_data["requirements"]
        else:
            materials_list = [parsed_data]
    elif isinstance(parsed_data, list):
        materials_list = parsed_data
    else:
        raise ValueError(f"Unexpected JSON structure: {type(parsed_data)}")

    if not materials_list:
        raise ValueError("No material items found in parsed JSON.")

    validated = []
    for item in materials_list:
        if not isinstance(item, dict):
            continue
        norm_item = dict(item)
        if "name" in norm_item and "material_name" not in norm_item:
            norm_item["material_name"] = norm_item.pop("name")
        if "grade" in norm_item and "specification" not in norm_item:
            norm_item["specification"] = norm_item.pop("grade")

        # Safely convert numeric quantity string if applicable, without fabricating
        if "quantity" in norm_item and isinstance(norm_item["quantity"], str):
            try:
                norm_item["quantity"] = float(norm_item["quantity"].replace(",", "").strip())
            except ValueError:
                norm_item["quantity"] = None

        mat = MaterialRequirement.model_validate(norm_item)
        validated.append(mat.model_dump())

    if not validated:
        raise ValueError("Parsed JSON contained no valid MaterialRequirement objects.")

    return validated


def extract_project_info(document_text: str) -> dict:
    """Extract structured project information using the configured LLM with fallback."""

    if not document_text or not document_text.strip():
        raise ValueError("Document text is empty.")

    if not settings.is_llm_configured:
        raise RuntimeError(
            f"{settings.llm_provider.upper()} API key is not configured."
        )

    llm = get_llm()
    messages = [
        ("system", _PROJECT_SYSTEM_PROMPT),
        (
            "human",
            "Extract project intelligence from this DPR context:\n\n"
            + document_text,
        ),
    ]

    try:
        structured_llm = llm.with_structured_output(ProjectInfoExtraction)
        result: ProjectInfoExtraction = _invoke_llm_with_retry(
            structured_llm, messages
        )
        return _clean_dict_strings(result.model_dump())
    except Exception as primary_err:
        # Fallback to json_schema or json_mode
        for method in ["json_schema", "json_mode"]:
            try:
                sec_llm = llm.with_structured_output(ProjectInfoExtraction, method=method)
                sec_messages = list(messages)
                if method == "json_mode":
                    sec_messages = [
                        ("system", _PROJECT_SYSTEM_PROMPT + "\nRespond with a valid JSON object matching the ProjectInfoExtraction schema."),
                        ("human", "Extract project intelligence from this DPR context as JSON:\n\n" + document_text),
                    ]
                result = _invoke_llm_with_retry(sec_llm, sec_messages)
                extraction = (
                    result
                    if isinstance(result, ProjectInfoExtraction)
                    else ProjectInfoExtraction.model_validate(result)
                )
                return _clean_dict_strings(extraction.model_dump())
            except Exception:
                continue

        raise primary_err


def extract_material_requirements(document_text: str) -> list[dict]:
    """Extract material requirements using the configured LLM with multi-tier fallback."""

    if not document_text or not document_text.strip():
        raise ValueError("Document context cannot be empty.")

    if not settings.is_llm_configured:
        raise RuntimeError(
            f"{settings.llm_provider.upper()} API key is not configured."
        )

    llm = get_llm()
    messages = [
        ("system", _MATERIAL_SYSTEM_PROMPT),
        (
            "human",
            "Extract material requirements from this DPR context:\n\n"
            + document_text,
        ),
    ]

    attempts_errors: list[str] = []

    # Attempt 1: Standard structured output (tool/function calling)
    try:
        structured_llm = llm.with_structured_output(MaterialListExtraction)
        result = _invoke_llm_with_retry(structured_llm, messages)
        extraction = (
            result
            if isinstance(result, MaterialListExtraction)
            else MaterialListExtraction.model_validate(result)
        )
        if extraction.materials:
            return [_clean_dict_strings(mat.model_dump()) for mat in extraction.materials]
        attempts_errors.append("Attempt 1 (function_calling) returned 0 materials")
    except Exception as exc:
        attempts_errors.append(f"Attempt 1 (function_calling) failed: {exc}")

    # Attempt 2: Simpler structured-output mechanism (json_schema / json_mode)
    for method in ["json_schema", "json_mode"]:
        try:
            sec_llm = llm.with_structured_output(MaterialListExtraction, method=method)
            sec_messages = list(messages)
            if method == "json_mode":
                sec_messages = [
                    (
                        "system",
                        _MATERIAL_SYSTEM_PROMPT
                        + "\nRespond with a valid JSON object matching the MaterialListExtraction schema with a 'materials' list.",
                    ),
                    (
                        "human",
                        "Extract material requirements from this DPR context as JSON:\n\n"
                        + document_text,
                    ),
                ]
            result = _invoke_llm_with_retry(sec_llm, sec_messages)
            extraction = (
                result
                if isinstance(result, MaterialListExtraction)
                else MaterialListExtraction.model_validate(result)
            )
            if extraction.materials:
                return [_clean_dict_strings(mat.model_dump()) for mat in extraction.materials]
            attempts_errors.append(f"Attempt 2 ({method}) returned 0 materials")
        except Exception as exc:
            attempts_errors.append(f"Attempt 2 ({method}) failed: {exc}")

    # Attempt 3: Direct LLM completion with controlled JSON extraction fallback
    try:
        json_prompt = (
            f"{_MATERIAL_SYSTEM_PROMPT}\n\n"
            "CRITICAL: Output ONLY a single, valid JSON object. Do not include markdown commentary. "
            "Use this exact JSON structure:\n"
            "{\n"
            '  "materials": [\n'
            "    {\n"
            '      "material_name": "name of material",\n'
            '      "quantity": null or number,\n'
            '      "unit": null or "unit string",\n'
            '      "specification": null or "spec string",\n'
            '      "purpose": null or "purpose string",\n'
            '      "alternatives": []\n'
            "    }\n"
            "  ]\n"
            "}\n"
        )
        direct_messages = [
            ("system", json_prompt),
            (
                "human",
                "Extract all material requirements from this DPR context as JSON:\n\n"
                + document_text,
            ),
        ]
        response = _invoke_llm_with_retry(llm, direct_messages)
        content = getattr(response, "content", "")
        if isinstance(content, list):
            content = "".join(
                str(b.get("text", b)) if isinstance(b, dict) else str(b)
                for b in content
            )
        validated_materials = _parse_and_validate_materials_json(str(content))
        if validated_materials:
            return [_clean_dict_strings(m) for m in validated_materials]
        attempts_errors.append("Attempt 3 (direct JSON extraction) found 0 valid materials")
    except Exception as exc:
        attempts_errors.append(f"Attempt 3 (direct JSON extraction) failed: {exc}")

    raise RuntimeError(
        "Material extraction failed across all structured and fallback attempts:\n"
        + "\n".join(f"  - {err}" for err in attempts_errors)
    )


# ===================================================================
# LangGraph node - Agent 1: Project & Material Intelligence
# ===================================================================

def run_project_intelligence(state: InfraMinerState) -> dict:
    """LangGraph node for Agent 1 (Project & Material Intelligence).

    Step 1: Check LLM configuration.
    Step 2: Retrieve and extract project information.
    Step 3: Retrieve and extract material requirements.
    Step 4: Return combined partial state update.
    """

    # ----- 1. Check LLM -----
    if not settings.is_llm_configured:
        return {
            "errors": [
                f"Agent 1: {settings.llm_provider.upper()} API key "
                f"is not set."
            ],
            "current_agent": "project_material_intelligence",
        }

    # ----- 2. Project Intelligence -----
    try:
        project_context = _retrieve_project_context()
    except FileNotFoundError:
        return {
            "errors": [
                "Agent 1: Document index not found. "
                "Run: python src/utils/document_index.py"
            ],
            "current_agent": "project_material_intelligence",
        }
    except Exception as exc:
        return {
            "errors": [f"Agent 1: Project retrieval failed - {exc}"],
            "current_agent": "project_material_intelligence",
        }

    if not project_context.strip():
        return {
            "errors": [
                "Agent 1: No relevant project information found "
                "in the document index."
            ],
            "current_agent": "project_material_intelligence",
        }

    try:
        project_info = extract_project_info(project_context)
    except Exception as exc:
        return {
            "errors": [f"Agent 1: Project extraction failed - {exc}"],
            "current_agent": "project_material_intelligence",
        }

    # ----- 3. Material Requirement -----
    materials: list[dict] = []
    material_errors: list[str] = []

    try:
        material_context = _retrieve_material_context()
        materials = extract_material_requirements(material_context)
    except Exception as exc:
        material_errors.append(
            f"Agent 1 (materials): Extraction failed - {exc}"
        )

    # ----- 4. Combined result -----
    messages_list = [
        "Agent 1: Extracted project information successfully."
    ]
    if materials:
        messages_list.append(
            f"Agent 1: Identified {len(materials)} material(s) "
            f"from project documents."
        )

    result: dict = {
        **project_info,
        "materials": materials,
        "messages": messages_list,
        "current_agent": "project_material_intelligence",
        "completed_agents": ["project_material_intelligence"],
    }

    if material_errors:
        result["errors"] = material_errors

    return _clean_dict_strings(result)