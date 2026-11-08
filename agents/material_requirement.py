"""
InfraMiner AI — Agent 2: Material Requirement

Identifies the materials required for the infrastructure project by
analysing project documentation.  Uses Google Gemini with Pydantic
structured output to extract material names, quantities, units,
specifications, purposes, and alternatives.

This module defines:
- MaterialRequirement      : Pydantic model for a single material
- MaterialListExtraction   : Pydantic wrapper for the LLM response
- extract_material_requirements : Core extraction (text → list[dict])
- run_material_requirement : LangGraph-compatible node function
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import settings
from src.state import InfraMinerState


# ---------------------------------------------------------------------------
# Pydantic models for structured LLM output validation
# ---------------------------------------------------------------------------

class MaterialRequirement(BaseModel):
    """A single material required for the infrastructure project."""

    material_name: str = Field(
        description="Name of the material (e.g., 'Reinforced Concrete', 'Rock Armour')"
    )
    quantity: float | None = Field(
        default=None,
        description=(
            "Quantity required. Set to null if the document does not "
            "explicitly state a quantity. Do NOT invent quantities."
        ),
    )
    unit: str | None = Field(
        default=None,
        description="Unit of measurement (e.g., 'tonnes', 'm³', 'Ha'). Null if unknown.",
    )
    specification: str | None = Field(
        default=None,
        description=(
            "Material specification or grade (e.g., 'M40 grade', 'IS 456'). "
            "Null if not explicitly mentioned. Do NOT fabricate specifications."
        ),
    )
    purpose: str | None = Field(
        default=None,
        description="Construction purpose (e.g., 'breakwater armour layer', 'berth piling')",
    )
    alternatives: list[str] = Field(
        default_factory=list,
        description=(
            "Possible alternative materials mentioned in the document. "
            "Empty list if none are mentioned."
        ),
    )


class MaterialListExtraction(BaseModel):
    """Wrapper for the list of materials extracted by the LLM."""

    materials: list[MaterialRequirement] = Field(
        description="List of materials identified in the project document."
    )


# ---------------------------------------------------------------------------
# System prompt for Agent 2
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are the Material Requirement Agent for InfraMiner AI, a framework
for sustainable resource sourcing in large-scale infrastructure projects.

Your task is to identify all materials required for the project based
on the provided document text.

Instructions:

- Extract ONLY materials explicitly mentioned in the document.
- For each material, identify the quantity and unit if stated.
- If a quantity is NOT explicitly stated, set quantity to null.
- If a specification/grade is NOT explicitly stated, set it to null.
- Do NOT invent, estimate, or fabricate any quantities or specs.
- Identify the construction purpose for each material.
- List any alternative materials mentioned in the document.
- Include major construction materials: concrete, steel, rock,
  sand, aggregate, armour units, fill material, geotextile, etc.
- Do NOT include equipment, machinery, or labour.
"""


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------

def extract_material_requirements(document_text: str) -> list[dict]:
    """Extract material requirements from document text using Gemini.

    Parameters
    ----------
    document_text : str
        Relevant text content (full document or retrieved chunks).

    Returns
    -------
    list[dict]
        List of material requirement dictionaries, each containing:
        material_name, quantity, unit, specification, purpose, alternatives.

    Raises
    ------
    ValueError
        If document_text is empty.
    RuntimeError
        If GOOGLE_API_KEY is not configured.
    """
    if not document_text or not document_text.strip():
        raise ValueError(
            "Document text is empty. Cannot extract material requirements."
        )

    if not settings.is_llm_configured:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to .env to use Agent 2."
        )

    llm = ChatGoogleGenerativeAI(
        model=settings.google_model,
        google_api_key=settings.google_api_key,
        temperature=settings.llm_temperature,
    )

    structured_llm = llm.with_structured_output(MaterialListExtraction)

    user_message = (
        "Identify all materials required for this infrastructure project "
        "based on the following document text:\n\n"
        f"{document_text}"
    )

    result: MaterialListExtraction = structured_llm.invoke(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", user_message),
        ]
    )

    return [mat.model_dump() for mat in result.materials]


# ---------------------------------------------------------------------------
# LangGraph node function
# ---------------------------------------------------------------------------

def run_material_requirement(state: InfraMinerState) -> dict:
    """LangGraph node for Agent 2: Material Requirement.

    Reads project scope from shared state and extracts material
    requirements from the project documents.

    Parameters
    ----------
    state : InfraMinerState
        Current shared workflow state.  Expected to contain
        project_scope (from Agent 1) for context.

    Returns
    -------
    dict
        Partial state update with materials list and workflow metadata.
    """
    from src.utils.pdf_loader import load_all_pdfs
    from src.utils.document_retriever import (
        retrieve_relevant_chunks,
        MATERIAL_REQUIREMENT_KEYWORDS,
    )

    # 1. Check Gemini configuration
    if not settings.is_llm_configured:
        return {
            "errors": [
                "Agent 2: GOOGLE_API_KEY is not set. "
                "Add it to .env before running this agent."
            ],
            "current_agent": "material_requirement",
        }

    # 2. Check for project documents
    raw_dir = settings.documents_dir / "raw"
    if not raw_dir.exists() or not list(raw_dir.glob("*.pdf")):
        return {
            "errors": [
                "Agent 2: No PDF documents found in documents/raw/."
            ],
            "current_agent": "material_requirement",
        }

    # 3. Load PDFs and retrieve relevant chunks
    pdf_texts = load_all_pdfs(raw_dir)
    combined_text = "\n\n".join(pdf_texts.values())

    relevant_chunks = retrieve_relevant_chunks(
        document_text=combined_text,
        keywords=MATERIAL_REQUIREMENT_KEYWORDS,
        max_chunks=15,
        max_total_chars=50000,
    )

    if not relevant_chunks:
        return {
            "errors": [
                "Agent 2: No material-relevant sections found in documents."
            ],
            "current_agent": "material_requirement",
        }

    # Add project context from Agent 1 if available
    context_parts: list[str] = []
    project_scope = state.get("project_scope")
    if project_scope:
        context_parts.append(f"[Project Scope]\n{project_scope}")
    context_parts.extend(relevant_chunks)
    context_text = "\n\n---\n\n".join(context_parts)

    # 4. Extract materials via Gemini
    try:
        materials = extract_material_requirements(context_text)
    except Exception as e:
        return {
            "errors": [
                f"Agent 2: Material extraction failed — {e}"
            ],
            "current_agent": "material_requirement",
        }

    return {
        "materials": materials,
        "messages": [
            f"Agent 2: Identified {len(materials)} material(s) "
            f"from project documents."
        ],
        "current_agent": "material_requirement",
        "completed_agents": ["material_requirement"],
    }

