"""document_loader — move documents between local disk, Cloud Storage and Python.

    upload_corpus_to_gcs()      local data/  ->  raw/ zone
    load_processed_documents()  processed/ zone  ->  LangChain Documents
"""

import glob
import json
import os

from google.cloud import storage
from langchain_core.documents import Document

from hr_assistant import config

# local folder pattern -> bucket folder
_LOCAL_TO_RAW = [
    (os.path.join("data", "*.txt"), config.GCS_PREFIX),        # HR policies
    (os.path.join("data", "noise", "*"), config.NOISE_GCS_PREFIX),  # noise docs
]


def upload_corpus_to_gcs() -> int:
    """Copy local data/ files into the bucket's raw/ zone (overwrites).
    Returns how many files were uploaded."""
    bucket = storage.Client(project=config.PROJECT_ID).bucket(config.GCS_BUCKET_NAME)

    count = 0
    for local_glob, prefix in _LOCAL_TO_RAW:
        for path in glob.glob(local_glob):
            if os.path.isfile(path):
                bucket.blob(prefix + os.path.basename(path)).upload_from_filename(path)
                count += 1
    return count


def load_processed_documents(
    prefixes: tuple[str, ...] = (config.PROCESSED_HR_PREFIX,),
) -> list[Document]:
    """Read processed JSON records back as LangChain Documents.

    Default = HR only. Pass both prefixes for HR + noise:
        load_processed_documents((config.PROCESSED_HR_PREFIX, config.PROCESSED_NOISE_PREFIX))
    """
    bucket = storage.Client(project=config.PROJECT_ID).bucket(config.GCS_BUCKET_NAME)

    documents = []
    for prefix in prefixes:
        for blob in bucket.list_blobs(prefix=prefix):
            if not blob.name.endswith(".json"):
                continue
            record = json.loads(blob.download_as_text())
            documents.append(Document(
                page_content=record["text"],
                metadata={
                    "source": record["source"],
                    "policy_category": record["policy_category"],
                    "gcs_path": record["raw_gcs_path"],
                },
            ))
    return documents