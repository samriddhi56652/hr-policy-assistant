"""embeddings — turn text into vectors (lists of numbers) using Jina."""

from langchain_community.embeddings import JinaEmbeddings

from hr_assistant import config


def get_embeddings_model():
    """Return the Jina embeddings model (768 numbers per text)."""
    return JinaEmbeddings(
        jina_api_key=config.JINA_API_KEY,
        model_name=config.EMBEDDING_MODEL_NAME,
    )