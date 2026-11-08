"""
InfraMiner AI — PDF Loading Utility

Provides efficient page-level PDF text extraction for large project
documents such as DPRs, EIAs, feasibility reports, and technical reports.

The loader supports:
- Reading individual PDF pages
- Loading all pages when required
- Loading only selected pages for efficient retrieval
"""

from __future__ import annotations

from pathlib import Path

import pymupdf


def load_pdf_page(file_path: str | Path, page_number: int) -> str:
    """Extract text from one PDF page.

    Parameters
    ----------
    file_path : str | Path
        Path to the PDF file.
    page_number : int
        Zero-based page index.

    Returns
    -------
    str
        Extracted page text.
    """

    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a .pdf file, got: {path.suffix!r}"
        )

    with pymupdf.open(path) as document:

        if page_number < 0 or page_number >= len(document):
            raise IndexError(
                f"Page number {page_number} is outside the PDF range "
                f"0-{len(document) - 1}."
            )

        page = document[page_number]

        try:
            text = page.get_text("text")
        except Exception as exc:
            return (
                f"[Page {page_number + 1}: "
                f"text extraction failed — {exc}]"
            )

        if text and text.strip():
            return text

        return f"[Page {page_number + 1}: no extractable text]"


def iter_pdf_pages(file_path: str | Path):
    """Yield PDF pages one at a time.

    This avoids building the entire PDF text in memory at once.

    Yields
    ------
    tuple[int, str]
        Zero-based page index and extracted page text.
    """

    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    if path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Expected a .pdf file, got: {path.suffix!r}"
        )

    with pymupdf.open(path) as document:

        for page_number, page in enumerate(document):

            try:
                text = page.get_text("text")
            except Exception as exc:
                text = (
                    f"[Page {page_number + 1}: "
                    f"text extraction failed — {exc}]"
                )

            if not text or not text.strip():
                text = (
                    f"[Page {page_number + 1}: "
                    f"no extractable text]"
                )

            yield page_number, text


def load_pdf(file_path: str | Path) -> str:
    """Extract text from an entire PDF.

    This function is retained for compatibility with existing code.
    For large PDFs, prefer iter_pdf_pages().
    """

    pages: list[str] = []

    for _, text in iter_pdf_pages(file_path):
        pages.append(text)

    return "\n\n".join(pages)


def load_all_pdfs(directory: str | Path) -> dict[str, str]:
    """Extract text from all PDFs in a directory.

    This function is retained for compatibility with existing agents.
    Large-document agents should prefer page-level processing.
    """

    dir_path = Path(directory).resolve()

    if not dir_path.exists():
        raise FileNotFoundError(
            f"Directory not found: {dir_path}"
        )

    if not dir_path.is_dir():
        raise ValueError(
            f"Expected a directory, got a file: {dir_path}"
        )

    results: dict[str, str] = {}

    for pdf_file in sorted(dir_path.glob("*.pdf")):
        results[pdf_file.name] = load_pdf(pdf_file)

    return results