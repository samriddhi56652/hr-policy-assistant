"""semantic_cache — reuse answers to questions that MEAN the same thing.

Each question is turned into numbers (the same Jina embeddings used for search).
A new question is compared with stored ones; if one is similar enough
(config.SEMANTIC_CACHE_THRESHOLD), its answer is reused — no search, no Gemini.

In memory only: lost when the program stops.
"""

import logging
import time
from collections import deque

import numpy as np

from hr_assistant import config
from hr_assistant.embeddings import get_embeddings_model

logger = logging.getLogger(__name__)


class SemanticCache:
    def __init__(
        self,
        threshold: float = config.SEMANTIC_CACHE_THRESHOLD,
        max_entries: int = config.SEMANTIC_CACHE_MAX_ENTRIES,
        ttl_seconds: int = config.SEMANTIC_CACHE_TTL_SECONDS,
    ):
        self.threshold = threshold
        self.ttl_seconds = ttl_seconds
        self._embeddings = get_embeddings_model()
        self._entries = deque(maxlen=max_entries)  # oldest drops out automatically when full

    def _vector(self, text: str) -> np.ndarray:
        """Question -> numbers, scaled to length 1 so a dot product = similarity."""
        v = np.asarray(self._embeddings.embed_query(text), dtype=float)
        return v / (np.linalg.norm(v) or 1.0)

    def lookup(self, question: str):
        """Return (cached answer or None, the question's vector).
        The vector is handed back so store() doesn't have to compute it again."""
        vector = self._vector(question)
        cutoff = time.monotonic() - self.ttl_seconds
        fresh = [e for e in self._entries if e["time"] >= cutoff]
        if fresh:
            scores = np.array([e["vector"] for e in fresh]) @ vector
            best = int(np.argmax(scores))
            if scores[best] >= self.threshold:
                logger.info("CACHE HIT (similarity %.3f with %r)", scores[best], fresh[best]["question"])
                return fresh[best]["answer"], vector
        logger.info("CACHE MISS")
        return None, vector

    def store(self, vector: np.ndarray, question: str, answer: str) -> None:
        self._entries.append({"vector": vector, "question": question,
                              "answer": answer, "time": time.monotonic()})
