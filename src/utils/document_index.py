"""
InfraMiner AI — Persistent Document Index

Processes project PDFs once and stores page-level text locally.
Agents can then search the cached index instead of repeatedly
extracting text from the original large PDF.
"""

from __future__ import annotations

import json
from pathlib import Path

import pymupdf


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DOCUMENTS_DIR = PROJECT_ROOT / "documents" / "raw"
INDEX_DIR = PROJECT_ROOT / "data" / "document_index"

INDEX_FILE = INDEX_DIR / "pdf_pages.json"


# ---------------------------------------------------------------------------
# PDF indexing
# ---------------------------------------------------------------------------

def build_document_index(
    raw_documents_dir: str | Path = RAW_DOCUMENTS_DIR,
    index_file: str | Path = INDEX_FILE,
) -> Path:
    """Build a persistent page-level index for all PDFs.

    The PDF is processed only when the index is built.
    Agents subsequently read the cached JSON index.
    """

    raw_dir = Path(raw_documents_dir).resolve()
    output_file = Path(index_file).resolve()

    if not raw_dir.exists():
        raise FileNotFoundError(
            f"Document directory not found: {raw_dir}"
        )

    pdf_files = sorted(raw_dir.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in: {raw_dir}"
        )

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    documents: list[dict] = []

    for pdf_file in pdf_files:

        print(f"Indexing: {pdf_file.name}")

        with pymupdf.open(pdf_file) as pdf:

            pages: list[dict] = []

            total_pages = len(pdf)

            for page_number, page in enumerate(pdf):

                try:
                    text = page.get_text("text")
                except Exception as exc:
                    text = (
                        f"[Text extraction failed: {exc}]"
                    )

                text = text.strip() if text else ""

                pages.append(
                    {
                        "page": page_number + 1,
                        "text": text,
                    }
                )

                # Small progress indicator for the one-time operation.
                if (
                    (page_number + 1) % 50 == 0
                    or page_number + 1 == total_pages
                ):
                    print(
                        f"  Processed "
                        f"{page_number + 1}/{total_pages} pages"
                    )

            documents.append(
                {
                    "document_name": pdf_file.name,
                    "document_path": str(pdf_file),
                    "page_count": total_pages,
                    "pages": pages,
                }
            )

    index_data = {
        "version": 1,
        "documents": documents,
    }

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            index_data,
            file,
            ensure_ascii=False,
        )

    print()
    print("Document indexing completed.")
    print(f"Documents indexed: {len(documents)}")
    print(f"Index file: {output_file}")

    return output_file


# ---------------------------------------------------------------------------
# Index loading
# ---------------------------------------------------------------------------

def load_document_index(
    index_file: str | Path = INDEX_FILE,
) -> dict:
    """Load the persistent document index."""

    path = Path(index_file).resolve()

    if not path.exists():
        raise FileNotFoundError(
            "Document index not found. "
            "Run build_document_index() first."
        )

    with path.open(
        "r",
        encoding="utf-8",
    ) as file:

        return json.load(file)


# ---------------------------------------------------------------------------
# Page search
# ---------------------------------------------------------------------------

def search_document_index(
    keywords: list[str],
    max_pages: int = 20,
) -> list[dict]:
    """Search indexed PDF pages using keyword relevance.

    Returns the most relevant pages while preserving document
    and page information.
    """

    index = load_document_index()

    keyword_list = [
        keyword.lower()
        for keyword in keywords
        if keyword.strip()
    ]

    results: list[dict] = []

    for document in index.get("documents", []):

        document_name = document.get(
            "document_name",
            "unknown",
        )

        for page in document.get("pages", []):

            text = page.get("text", "")

            if not text.strip():
                continue

            lower_text = text.lower()

            score = sum(
                lower_text.count(keyword)
                for keyword in keyword_list
            )

            if score > 0:
                results.append(
                    {
                        "document_name": document_name,
                        "page": page.get("page"),
                        "score": score,
                        "text": text,
                    }
                )

    # Highest relevance first.
    results.sort(
        key=lambda item: (
            -item["score"],
            item["document_name"],
            item["page"],
        )
    )

    return results[:max_pages]


# ---------------------------------------------------------------------------
# Simple test / command-line execution
# ---------------------------------------------------------------------------

if __name__ == "__main__":

    build_document_index()