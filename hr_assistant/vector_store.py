"""vector_store — save chunks into Qdrant Cloud and connect to them later.

Hybrid search = two kinds of vectors per chunk:
  dense  (Jina, 768 numbers) -> matches MEANING     ("time off when ill" ~ "sick leave")
  sparse (BM25 keywords)     -> matches EXACT WORDS ("casual leave")
"""

from functools import lru_cache

from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode
from qdrant_client import QdrantClient
from qdrant_client.models import FieldCondition, Filter, MatchAny, PayloadSchemaType

from hr_assistant import config
from hr_assistant.embeddings import get_embeddings_model

_SPARSE_MODEL = "Qdrant/bm25"  # the keyword-search model


@lru_cache(maxsize=1)
def _client() -> QdrantClient:
    """One Qdrant connection for the whole program, reused every time."""
    return QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY)


def collection_exists(name: str) -> bool:
    """True only if the collection exists AND has at least one chunk in it."""
    client = _client()
    return client.collection_exists(name) and client.count(name).count > 0


def build_vector_store(chunks, collection_name: str) -> QdrantVectorStore:
    """Embed every chunk and save it into a FRESH collection.
    If a collection with this name already exists, it is deleted first."""
    store = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=get_embeddings_model(),
        sparse_embedding=FastEmbedSparse(model_name=_SPARSE_MODEL),
        retrieval_mode=RetrievalMode.HYBRID,
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
        collection_name=collection_name,
        force_recreate=True,
    )
    # Index the category label so step 20 can filter by it.
    # (Qdrant refuses to filter on a field that has no index.)
    store.client.create_payload_index(
        collection_name=collection_name,
        field_name="metadata.policy_category",
        field_schema=PayloadSchemaType.KEYWORD,
    )
    return store


def load_vector_store(collection_name: str = config.QDRANT_COLLECTION_NAME) -> QdrantVectorStore:
    """Connect to a collection that's ALREADY built — no embedding, no uploading.
    The chatbot uses this; only ingestion uses build_vector_store()."""
    if not collection_exists(collection_name):
        raise RuntimeError(
            f"Collection '{collection_name}' is missing or empty — run `python ingest.py` first."
        )
    return QdrantVectorStore.from_existing_collection(
        collection_name=collection_name,
        embedding=get_embeddings_model(),
        sparse_embedding=FastEmbedSparse(model_name=_SPARSE_MODEL),
        retrieval_mode=RetrievalMode.HYBRID,
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
    )

def get_retriever(
    vector_store: QdrantVectorStore,
    k: int = config.RERANK_CANDIDATE_K,
    filter_categories: set[str] | None = None,
):
    """Turn the vector store into a retriever (question in, k chunks out).

    filter_categories = only return chunks whose policy_category is in this set.
    Qdrant applies it INSIDE the search, so other chunks are never even considered."""
    search_kwargs = {"k": k}
    if filter_categories:
        search_kwargs["filter"] = Filter(
            must=[FieldCondition(
                key="metadata.policy_category",
                match=MatchAny(any=list(filter_categories)),
            )]
        )
    return vector_store.as_retriever(search_kwargs=search_kwargs)