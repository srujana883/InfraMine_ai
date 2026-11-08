"""
InfraMiner AI — Deterministic Document Retriever

Provides simple keyword-based chunking and retrieval for large
documents.  This avoids sending the entire DPR text to Gemini when
only specific sections are relevant.

No vector databases, embeddings, or external APIs are used.

Usage
-----
    from src.utils.document_retriever import retrieve_relevant_chunks

    chunks = retrieve_relevant_chunks(
        document_text=full_text,
        keywords=["scope", "capacity", "berth"],
        max_chunks=10,
        chunk_size=2000,
    )
    context = "\\n\\n".join(chunks)
"""

from __future__ import annotations

import re
from typing import Optional


# ---------------------------------------------------------------------------
# Default keyword sets for each agent
# ---------------------------------------------------------------------------

PROJECT_INTELLIGENCE_KEYWORDS: list[str] = [
    "project", "location", "coordinates", "latitude", "longitude",
    "scope", "capacity", "construction", "phase", "timeline",
    "constraints", "environmental", "seismic", "CRZ", "regulatory",
    "climate", "berth", "reclamation", "breakwater",
]

MATERIAL_REQUIREMENT_KEYWORDS: list[str] = [
    "material", "concrete", "steel", "rock", "sand", "aggregate",
    "cement", "reinforcement", "armour", "accropode", "geotextile",
    "quantity", "volume", "tonnage", "specification", "grade",
    "dredging", "reclamation", "fill", "quarry", "pile",
]


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def split_into_chunks(
    text: str,
    chunk_size: int = 2000,
    overlap: int = 200,
) -> list[str]:
    """Split text into overlapping chunks of approximately chunk_size chars.

    Parameters
    ----------
    text : str
        Full document text.
    chunk_size : int
        Target number of characters per chunk.
    overlap : int
        Number of overlapping characters between consecutive chunks.

    Returns
    -------
    list[str]
        List of text chunks.
    """
    if not text or not text.strip():
        return []

    chunks: list[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)

        # Try to break at a paragraph or sentence boundary
        if end < text_len:
            # Look for paragraph break within last 20% of chunk
            search_start = max(start, end - chunk_size // 5)
            para_break = text.rfind("\n\n", search_start, end)
            if para_break > start:
                end = para_break + 2  # include the newlines
            else:
                # Fall back to sentence boundary
                sent_break = text.rfind(". ", search_start, end)
                if sent_break > start:
                    end = sent_break + 2

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < text_len else text_len

    return chunks


def score_chunk(chunk: str, keywords: list[str]) -> int:
    """Score a chunk by counting keyword occurrences (case-insensitive).

    Parameters
    ----------
    chunk : str
        Text chunk to score.
    keywords : list[str]
        Keywords to search for.

    Returns
    -------
    int
        Total number of keyword matches found.
    """
    chunk_lower = chunk.lower()
    score = 0
    for kw in keywords:
        score += len(re.findall(re.escape(kw.lower()), chunk_lower))
    return score


def retrieve_relevant_chunks(
    document_text: str,
    keywords: list[str],
    chunk_size: int = 2000,
    overlap: int = 200,
    max_chunks: int = 15,
    min_score: int = 1,
    max_total_chars: Optional[int] = 50000,
) -> list[str]:
    """Retrieve the most relevant chunks from a document using keyword scoring.

    Parameters
    ----------
    document_text : str
        Full text of the document.
    keywords : list[str]
        Keywords to search for in each chunk.
    chunk_size : int
        Target size of each chunk in characters.
    overlap : int
        Overlap between consecutive chunks.
    max_chunks : int
        Maximum number of chunks to return.
    min_score : int
        Minimum keyword score for a chunk to be included.
    max_total_chars : int | None
        Maximum total characters across all returned chunks.
        None means no limit.

    Returns
    -------
    list[str]
        List of relevant text chunks, ordered by relevance score
        (highest first).
    """
    if not document_text or not keywords:
        return []

    # Split into chunks
    chunks = split_into_chunks(document_text, chunk_size, overlap)

    # Score each chunk
    scored = [
        (score_chunk(chunk, keywords), i, chunk)
        for i, chunk in enumerate(chunks)
    ]

    # Filter by minimum score and sort by score descending
    relevant = [
        (score, idx, chunk)
        for score, idx, chunk in scored
        if score >= min_score
    ]
    relevant.sort(key=lambda x: (-x[0], x[1]))

    # Select top chunks within limits
    selected: list[str] = []
    total_chars = 0
    for score, idx, chunk in relevant[:max_chunks]:
        if max_total_chars and total_chars + len(chunk) > max_total_chars:
            break
        selected.append(chunk)
        total_chars += len(chunk)

    return selected

