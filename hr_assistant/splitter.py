"""splitter — cut documents into small, overlapping chunks."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from hr_assistant import config


def split_into_chunks(documents):
    """Split documents into ~500-character chunks with 60 characters of overlap.
    Each chunk keeps its document's metadata (source, policy_category)."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
    )
    return splitter.split_documents(documents)