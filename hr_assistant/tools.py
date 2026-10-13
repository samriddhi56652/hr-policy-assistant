"""tools — the search tool the agent calls.

    question -> search Qdrant (12 candidates) -> rerank (best 5) -> cited text
"""

import logging

import requests
from langchain.tools import tool

from hr_assistant import config
from hr_assistant.reranker import rerank_with_scores
from hr_assistant.vector_store import get_retriever

logger = logging.getLogger(__name__)

NOT_FOUND_SENTINEL = "NOT_FOUND: no relevant HR policy content matched this question."

def create_search_tool(vector_store):
    """Build the search_hr_policy tool around one Qdrant collection."""
    retriever = get_retriever(vector_store, k=config.RERANK_CANDIDATE_K)

    @tool
    def search_hr_policy(question: str) -> str:
        """Search the company HR policy documents. Use this for any question about
        leave, work from home, probation, notice period, reimbursement, code of
        conduct, holidays, maternity/paternity leave, travel expenses, or the exit
        process."""
        candidates = retriever.invoke(question)
        ranked = rerank_with_scores(question, candidates, top_n=config.TOP_K_RESULTS)

        return "\n\n".join(
            f"[Source: {chunk.metadata['source']}] (relevance: {score:.2f})\n{chunk.page_content}"
            for chunk, score in ranked
        )

    return search_hr_policy


def create_guarded_search_tool(vector_store):
    """The search tool with the scope guardrail:
      1. only the 10 HR categories can be retrieved (category filter)
      2. if the best match is weak, report NOT_FOUND instead of guessing (relevance floor)
    """
    retriever = get_retriever(
        vector_store,
        k=config.RERANK_CANDIDATE_K,
        filter_categories=config.HR_POLICY_CATEGORIES,
    )

    @tool
    def search_hr_policy(question: str) -> str:
        """Search the company HR policy documents. Use this for any question about
        leave, work from home, probation, notice period, reimbursement, code of
        conduct, holidays, maternity/paternity leave, travel expenses, or the exit
        process. It cannot find Finance, Sales, Operations or Business information."""
        candidates = retriever.invoke(question)
        if not candidates:
            return NOT_FOUND_SENTINEL

        try:
            ranked = rerank_with_scores(question, candidates, top_n=config.TOP_K_RESULTS)
        except requests.RequestException:
            # Reranker down or too slow: use the search order instead of failing.
            # No scores means no relevance floor — but the category filter above
            # still guarantees HR-only text.
            logger.warning("Reranker failed — using search order instead.")
            return "\n\n".join(
                f"[Source: {chunk.metadata['source']}] (relevance: unknown)\n{chunk.page_content}"
                for chunk in candidates[: config.TOP_K_RESULTS]
            )

        # Gate on the TOP score only — broad questions need the weaker-scoring
        # sections too (see PROGRESS.md step 20 calibration).
        if not ranked or ranked[0][1] < config.RELEVANCE_THRESHOLD:
            return NOT_FOUND_SENTINEL

        return "\n\n".join(
            f"[Source: {chunk.metadata['source']}] (relevance: {score:.2f})\n{chunk.page_content}"
            for chunk, score in ranked
        )

    return search_hr_policy