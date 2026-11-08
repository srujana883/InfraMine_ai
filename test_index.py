from src.utils.document_index import search_document_index

keywords = [
    "project",
    "location",
    "scope",
    "capacity",
    "timeline",
    "coordinates",
    "constraints",
]

results = search_document_index(
    keywords=keywords,
    max_pages=20,
)

print("Results:", len(results))

for result in results:
    text = result["text"].replace("\n", " ")

    print(
        f"Page {result['page']} | "
        f"Score {result['score']} | "
        f"{text[:200]}"
    )