"""
InfraMiner AI — PDF Loading Utility

Extracts text from PDF documents using pypdf.  This module is a shared
utility used by any agent that needs to read PDF files (primarily
Agent 1: Project Intelligence for DPR/charter ingestion).

Usage
-----
    from src.utils.pdf_loader import load_pdf

    text = load_pdf("documents/raw/vadhavan_port_dpr.pdf")
"""

from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


def load_pdf(file_path: str | Path) -> str:
    """Read a PDF file and return its full text content.

    Parameters
    ----------
    file_path : str | Path
        Absolute or relative path to the PDF file.

    Returns
    -------
    str
        Concatenated text from all pages, separated by double newlines.
        Pages where text extraction fails are represented as
        "[Page N: text extraction failed]" so downstream consumers know
        content was present but unreadable.

    Raises
    ------
    FileNotFoundError
        If the file does not exist at the given path.
    ValueError
        If the file is not a PDF (based on extension).
    """
    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a .pdf file, got: {path.suffix!r}")

    reader = PdfReader(path)

    pages: list[str] = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text()
        except Exception:
            text = None
        if text and text.strip():
            pages.append(text)
        else:
            pages.append(f"[Page {i}: text extraction failed]")

    return "\n\n".join(pages)


def load_all_pdfs(directory: str | Path) -> dict[str, str]:
    """Load all PDF files from a directory.

    Parameters
    ----------
    directory : str | Path
        Path to a directory containing one or more PDF files.

    Returns
    -------
    dict[str, str]
        Mapping of filename → extracted text for each PDF found.
        Empty dict if no PDFs are present in the directory.

    Raises
    ------
    FileNotFoundError
        If the directory does not exist.
    """
    dir_path = Path(directory).resolve()

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {dir_path}")

    if not dir_path.is_dir():
        raise ValueError(f"Expected a directory, got a file: {dir_path}")

    results: dict[str, str] = {}
    for pdf_file in sorted(dir_path.glob("*.pdf")):
        results[pdf_file.name] = load_pdf(pdf_file)

    return results

