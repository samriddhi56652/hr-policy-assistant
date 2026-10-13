"""reranker — re-score search results with Jina's reranker.

Search is fast but rough. The reranker reads the question and each chunk
TOGETHER and gives each a relevance score (0 to 1). Plain web request — no extra library.
"""

import requests

from hr_assistant import config

JINA_RERANK_URL = "https://api.jina.ai/v1/rerank"


def rerank_with_scores(question: str, candidates: list, top_n: int = config.TOP_K_RESULTS) -> list[tuple]:
    """Return the best top_n candidates as (chunk, score) pairs, best first."""
    if not candidates:
        return []

    response = requests.post(
        JINA_RERANK_URL,
        headers={"Authorization": f"Bearer {config.JINA_API_KEY}"},
        json={
            "model": config.RERANKER_MODEL_NAME,
            "query": question,
            "documents": [c.page_content for c in candidates],
            "top_n": top_n,
            "return_documents": False,  # we already have the text; just send back positions + scores
        },
        timeout=30,
    )
    response.raise_for_status()  # turn an HTTP error (bad key, etc.) into a clear Python error

    # Each result says "candidate number X scored Y", already sorted best-first.
    return [(candidates[r["index"]], r["relevance_score"]) for r in response.json()["results"]]