"""ingest.py — run once to load the documents into Qdrant.

    python ingest.py            build any collection that's missing
    python ingest.py --force    rebuild everything from scratch
    python ingest.py --hr-only  only the main HR collection
"""

import argparse
import logging

from hr_assistant.ingestion import run_ingestion

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)  # hide one-line-per-web-request noise

parser = argparse.ArgumentParser(description="Load the HR documents into Qdrant.")
parser.add_argument("--force", action="store_true", help="rebuild collections even if they exist")
parser.add_argument("--hr-only", action="store_true", help="skip the noisy test collection")
args = parser.parse_args()

run_ingestion(force=args.force, hr_only=args.hr_only)