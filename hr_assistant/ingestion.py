"""ingestion — the one place documents get loaded into Qdrant.

    data/ --upload--> raw/ --parse--> processed/ --load--> chunk --> embed --> Qdrant
"""

import logging

from hr_assistant import config
from hr_assistant.document_loader import load_processed_documents, upload_corpus_to_gcs
from hr_assistant.processor import process_raw_to_json
from hr_assistant.splitter import split_into_chunks
from hr_assistant.vector_store import build_vector_store, collection_exists

logger = logging.getLogger(__name__)

# Which processed folders feed each collection.
_COLLECTIONS = {
    # the real one, used by the chatbot: HR only
    config.QDRANT_COLLECTION_NAME: (config.PROCESSED_HR_PREFIX,),
    # the test one: HR + Finance/Sales/Ops noise mixed together
    config.QDRANT_NOISY_COLLECTION_NAME: (config.PROCESSED_HR_PREFIX, config.PROCESSED_NOISE_PREFIX),
}


def run_ingestion(force: bool = False, hr_only: bool = False) -> None:
    """Build every collection that's missing (or all of them, with force=True)."""
    config.check_api_keys()

    names = [config.QDRANT_COLLECTION_NAME] if hr_only else list(_COLLECTIONS)
    to_build = [name for name in names if force or not collection_exists(name)]
    if not to_build:
        logger.info("All collections already built — nothing to do (use --force to rebuild).")
        return

    logger.info("Uploaded %d file(s) to raw/.", upload_corpus_to_gcs())
    logger.info("Processed %d file(s) into processed/.", process_raw_to_json())

    for name in to_build:
        documents = load_processed_documents(_COLLECTIONS[name])
        chunks = split_into_chunks(documents)
        build_vector_store(chunks, collection_name=name)
        logger.info("Built '%s': %d document(s) -> %d chunk(s).", name, len(documents), len(chunks))