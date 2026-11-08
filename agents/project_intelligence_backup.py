"""
InfraMiner AI — Agent 1: Project Intelligence

Reads project documentation (DPR / charter) and extracts structured
project information into the InfraMinerState. Uses Google Gemini with
Pydantic structured output validation to ensure the LLM returns
well-formed data.

This module defines:
- ProjectInfoExtraction   : Pydantic model for validated LLM output
- ProjectLocation         : Pydantic model for latitude/longitude
- extract_project_info    : Core extraction function (text → dict)
- run_project_intelligence : LangGraph-compatible node function
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI

from src.config import settings
from src.state import InfraMinerState


# ---------------------------------------------------------------------------
# Pydantic models for structured LLM output validation
# ---------------------------------------------------------------------------

class ProjectLocation(BaseModel):
    """Geographic coordinates of the project site."""

    lat: float = Field(
        description="Latitude in decimal degrees (e.g., 19.8169)"
    )
    lng: float = Field(
        description="Longitude in decimal degrees (e.g., 72.7103)"
    )


class ProjectInfoExtraction(BaseModel):
    """Structured project information extracted from a DPR or project charter.

    Pydantic validates the LLM output so malformed responses are caught
    before they enter the multi-agent workflow.
    """

    project_name: str = Field(
        description="Official project name as stated in the document"
    )

    project_type: str = Field(
        description=(
            "Type or category of infrastructure project, such as "
            "port, highway, dam, railway, airport, bridge, or another "
            "appropriate infrastructure category"
        )
    )

    project_location: ProjectLocation = Field(
        description="Geographic coordinates of the project site"
    )

    project_scope: str = Field(
        description=(
            "Summary of the project's major components, capacity, "
            "phases, and important infrastructure elements. "
            "Write 3-5 sentences."
        )
    )

    project_constraints: list[str] = Field(
        description=(
            "List of regulatory, environmental, seismic, climatic, "
            "and technical constraints explicitly mentioned in "
            "the document. Each item should be a short phrase."
        )
    )

    project_timeline: str = Field(
        description=(
            "Construction timeline including project phases and "
            "target dates mentioned in the document"
        )
    )


# ---------------------------------------------------------------------------
# System prompt for Agent 1
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """
You are the Project Intelligence Agent for InfraMiner AI, a framework
for sustainable resource sourcing in large-scale infrastructure projects.

Your task is to read a Detailed Project Report (DPR) or project charter
and extract key project information into a structured format.

Instructions:

- Extract information ONLY from the provided document text.
- Do NOT invent, assume, or infer information that is not present.
- For project_location, convert coordinates to decimal degrees when
  coordinates are available in the document.
- For project_constraints, identify regulatory, environmental, seismic,
  climatic, and technical constraints explicitly mentioned.
- For project_scope, summarize the major project components concisely.
- For project_timeline, include the project phases and target dates
  mentioned in the document.
- Preserve important numerical values and dates from the document.
"""


# ---------------------------------------------------------------------------
# Core extraction function
# ---------------------------------------------------------------------------

def extract_project_info(document_text: str) -> dict:
    """Extract structured project information from document text using Gemini.

    Parameters
    ----------
    document_text : str
        Text content extracted from the project document.

    Returns
    -------
    dict
        Dictionary containing:
        project_name
        project_type
        project_location
        project_scope
        project_constraints
        project_timeline

    Raises
    ------
    ValueError
        If document_text is empty.

    RuntimeError
        If GOOGLE_API_KEY is not configured.
    """

    # Validate input before calling the LLM
    if not document_text or not document_text.strip():
        raise ValueError(
            "Document text is empty. Cannot extract project information."
        )

    # Check whether Gemini is configured
    if not settings.is_llm_configured:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to .env to use Agent 1."
        )

    # Initialize Gemini
    llm = ChatGoogleGenerativeAI(
        model=settings.google_model,
        google_api_key=settings.google_api_key,
        temperature=settings.llm_temperature,
    )

    # Request Pydantic-validated structured output
    structured_llm = llm.with_structured_output(ProjectInfoExtraction)

    user_message = (
        "Extract the project information from the following document:\n\n"
        f"{document_text}"
    )

    # Invoke the model
    result: ProjectInfoExtraction = structured_llm.invoke(
        [
            ("system", _SYSTEM_PROMPT),
            ("human", user_message),
        ]
    )

    # Convert Pydantic model into the shared-state format
    return {
        "project_name": result.project_name,
        "project_type": result.project_type,
        "project_location": result.project_location.model_dump(),
        "project_scope": result.project_scope,
        "project_constraints": result.project_constraints,
        "project_timeline": result.project_timeline,
    }


# ---------------------------------------------------------------------------
# LangGraph node function
# ---------------------------------------------------------------------------

def run_project_intelligence(state: InfraMinerState) -> dict:
    """LangGraph node for Agent 1: Project Intelligence.

    Loads project PDFs, extracts project information using Gemini,
    and returns a partial update to InfraMinerState.

    Parameters
    ----------
    state : InfraMinerState
        Current shared workflow state.

    Returns
    -------
    dict
        Partial state update containing extracted project information
        and workflow metadata.
    """

    from src.utils.pdf_loader import load_all_pdfs

    # 1. Check whether Gemini is configured BEFORE loading PDFs
    if not settings.is_llm_configured:
        return {
            "errors": [
                "Agent 1: GOOGLE_API_KEY is not set. "
                "Add it to .env before running this agent."
            ],
            "current_agent": "project_intelligence",
        }

    # 2. Check whether project PDFs exist
    raw_dir = settings.documents_dir / "raw"
    if not raw_dir.exists() or not list(raw_dir.glob("*.pdf")):
        return {
            "errors": [
                "Agent 1: No PDF documents found in documents/raw/. "
                "Please add a project DPR or charter document."
            ],
            "current_agent": "project_intelligence",
        }

    # 3. Only now perform expensive PDF loading
    pdf_texts = load_all_pdfs(raw_dir)

    # Combine document text (typically one DPR)
    combined_text = "\n\n---\n\n".join(
        f"[Document: {name}]\n{text}"
        for name, text in pdf_texts.items()
    )

    # 4. Extract project information via Gemini
    try:
        project_info = extract_project_info(combined_text)

    except Exception as e:
        return {
            "errors": [
                f"Agent 1: Project information extraction failed — {e}"
            ],
            "current_agent": "project_intelligence",
        }

    # Build partial state update
    num_docs = len(pdf_texts)
    num_constraints = len(project_info["project_constraints"])

    return {
        **project_info,
        "messages": [
            (
                f"Agent 1: Extracted project information from "
                f"{num_docs} document(s). "
                f"Found {num_constraints} constraints."
            )
        ],
        "current_agent": "project_intelligence",
        "completed_agents": ["project_intelligence"],
    }