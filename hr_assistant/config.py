"""config — every setting, read from .env. Every other file imports this."""

import os
from dotenv import load_dotenv

load_dotenv()  # reads .env into environment variables

## GOOGLE CLOUD
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")  # Vertex AI region
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")

# Folders inside the bucket.
# raw/       = original files, untouched
# processed/ = extracted plain text + labels, one JSON per file
GCS_PREFIX = "raw/hr-policies/"
NOISE_GCS_PREFIX = "raw/other-data/"
PROCESSED_HR_PREFIX = "processed/hr-policies/"
PROCESSED_NOISE_PREFIX = "processed/other-data/"

## API KEYS
JINA_API_KEY = os.getenv("JINA_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

## QDRANT COLLECTIONS
QDRANT_COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "hr_policies")
QDRANT_NOISY_COLLECTION_NAME = os.getenv("QDRANT_NOISY_COLLECTION_NAME", "hr_policies_noisy_demo")

## MODELS
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-3.8-flash")
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "jina-embeddings-v2-base-en")
RERANKER_MODEL_NAME = os.getenv("RERANKER_MODEL_NAME", "jina-reranker-v2-base-multilingual")

## CHUNKING
CHUNK_SIZE = 500     # characters per chunk
CHUNK_OVERLAP = 60   # characters shared between neighbouring chunks

## RETRIEVAL
RERANK_CANDIDATE_K = 12  # how many chunks the first search fetches
TOP_K_RESULTS = 5        # how many survive re-ranking and reach Gemini

## SCOPE GUARDRAIL (step 20)

# The exact "Policy Category:" values of the 10 HR files. Search is
# hard-filtered to these — Finance/Sales/Operations/Business chunks can
# never be returned, however similar they look.
HR_POLICY_CATEGORIES = {
    "Leave", "Work From Home", "Probation", "Notice Period", "Reimbursement",
    "Code of Conduct", "Holidays", "Maternity Paternity", "Travel Expense", "Exit Process",
}

# If even the BEST reranked chunk scores below this, report "not found".
# Calibrated 2026-10-08: real HR questions scored 0.54–0.74 at the top;
# unanswerable ones 0.28 or lower. Re-check if the documents or reranker change.
RELEVANCE_THRESHOLD = 0.35

## SAFETY GUARDRAIL — Model Armor (step 21)
GUARDRAIL_PROVIDER = os.getenv("GUARDRAIL_PROVIDER", "model_armor")  # "model_armor" or "none" (off)
MODEL_ARMOR_LOCATION = os.getenv("MODEL_ARMOR_LOCATION", "us")
MODEL_ARMOR_TEMPLATE_ID = os.getenv("MODEL_ARMOR_TEMPLATE_ID", "hr-assistant-guardrail")

# How many of the user's earlier messages are checked together with the new one.
GUARDRAIL_HISTORY_TURNS = 6

## BACKUP MODEL — Groq (step 22)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FALLBACK_MODEL_NAME = os.getenv("FALLBACK_MODEL_NAME", "openai/gpt-oss-20b")

## SEMANTIC CACHE (step 22)
# Two questions with similarity >= this count as "the same question".
# Calibrated 2026-10-13: rewordings of one question scored 0.92–0.99;
# DIFFERENT questions with similar wording (sick vs annual vs casual leave) up to 0.88.
SEMANTIC_CACHE_THRESHOLD = 0.93
SEMANTIC_CACHE_MAX_ENTRIES = 500    # oldest answer dropped beyond this
SEMANTIC_CACHE_TTL_SECONDS = 3600   # answers older than 1 hour are ignored

## EVALUATION (step 23c)
# A different model family from Gemini grades the answers, so the
# assistant isn't marking its own homework.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"
JUDGE_MODEL_NAME = os.getenv("JUDGE_MODEL_NAME", "openai/gpt-oss-120b")
EVAL_DATASET_NAME = "hr-policy-qa"  # the question set's name in LangSmith

## ACCESS CONTROL (step 24e)
# Emails allowed past the Google login: comma-separated in .env (laptop) and
# deploy.env.yaml (Cloud Run). Stored in lower case, because email addresses
# are not case-sensitive.
ALLOWED_EMPLOYEE_EMAILS = {
    email.strip().lower()
    for email in os.getenv("ALLOWED_EMPLOYEE_EMAILS", "").split(",")
    if email.strip()
}


def check_api_keys() -> None:
    """Stop early with a clear message if a required value is missing."""
    missing = [
        name for name, value in [
            ("PROJECT_ID", PROJECT_ID),
            ("GCS_BUCKET_NAME", GCS_BUCKET_NAME),
            ("JINA_API_KEY", JINA_API_KEY),
            ("QDRANT_URL", QDRANT_URL),
            ("QDRANT_API_KEY", QDRANT_API_KEY),
        ]
        if not value
    ]
    if missing:
        raise ValueError(f"Missing required .env values: {', '.join(missing)}")