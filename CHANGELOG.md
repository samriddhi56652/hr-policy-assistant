# Changelog

Which files were created or changed in each step, what changed, and who made the change.

- **Made by:** *You* = written by hand following the instructions · *Claude* = edited by Claude on request.
- Why each step exists: [PROGRESS.md](PROGRESS.md) · how it was tested: [TESTS.md](TESTS.md) · errors met: [ERRORS.md](ERRORS.md).

---

## Setup (steps 1–12)

| Step | File | Change | Made by |
|---|---|---|---|
| 10 | `requirements.txt` | Created — every package the project uses | You |
| 11 | `.env` | Created with Google Cloud values; keys added afterwards | Claude (template) · You (keys) |
| 12 | `.gitignore` | Created — keeps `.env`, `.venv/`, caches out of GitHub | You |
| 12 | `data/` | Copied in: 10 HR policies + 8 noise documents | Claude |
| — | `PROGRESS.md`, `ERRORS.md` | Created; updated after every step | Claude |

## Phase 1 — Basic RAG

| Step | File | Change | Made by |
|---|---|---|---|
| 13 | `hr_assistant/__init__.py` | Created (empty) — makes the folder a package | You |
| 13 | `hr_assistant/config.py` | Created — reads every setting from `.env` | You |
| 14 | `hr_assistant/processor.py` | Created — extracts text from txt/pdf/docx/pptx, saves JSON with category | You |
| 14 | `hr_assistant/document_loader.py` | Created — uploads `data/` to the bucket, loads processed documents | You |
| 15 | `hr_assistant/splitter.py` | Created — 500-character chunks, 60 overlap | You |
| 15 | `hr_assistant/embeddings.py` | Created — Jina embeddings (renamed from `embeddings`, ERRORS.md #6) | You |
| 15 | `hr_assistant/processor.py` | Windows line endings `\r\n` → `\n` (ERRORS.md #7) | Claude |
| 16 | `hr_assistant/vector_store.py` | Created — Qdrant hybrid store: build, load, check | You |
| 16 | `hr_assistant/ingestion.py` | Created — runs upload → process → chunk → embed → store | You |
| 16 | `ingest.py` | Created — `python ingest.py [--force] [--hr-only]` | You |
| 17 | `hr_assistant/vector_store.py` | Added `get_retriever` | You |
| 17 | `hr_assistant/reranker.py` | Created — Jina reranker, returns (chunk, score) | You |
| 17 | `hr_assistant/tools.py` | Created — `search_hr_policy` tool: 12 → rerank → best 5, cited | You |
| 18 | `.env` | `LOCATION=global`, `LLM_MODEL_NAME=gemini-3.8-flash` (ERRORS.md #8) | You |
| 18 | `hr_assistant/llm.py` | Created — Gemini through LiteLLM, region in `model_kwargs` (ERRORS.md #9) | You |
| 18 | `hr_assistant/prompts.py` | Created — the system prompt | You |
| 18 | `hr_assistant/agent.py` | Created — Gemini + prompt + tools + memory | You |
| 19 | `hr_assistant/pipeline.py` | Created — `build_hr_assistant()` and `ask()` | You |
| 19 | `main.py` | Created — terminal chat (moved out of `hr_assistant/`, ERRORS.md #11) | You |
| 19 | `app.py` | Created — Streamlit chat window (moved out of `hr_assistant/`) | You |

## Phase 2 — Security & reliability

| Step | File | Change | Made by |
|---|---|---|---|
| 20 | `hr_assistant/config.py` | Added `HR_POLICY_CATEGORIES`, `RELEVANCE_THRESHOLD = 0.35` | Claude |
| 20 | `hr_assistant/vector_store.py` | `get_retriever` can filter by category | Claude |
| 20 | `hr_assistant/tools.py` | Added `NOT_FOUND_SENTINEL`, `create_guarded_search_tool` | Claude |
| 20 | `hr_assistant/prompts.py` | Rules: how to handle NOT_FOUND; never guess Finance/Sales data | Claude |
| 20 | `hr_assistant/pipeline.py` | `build_hr_assistant(collection_name, guarded)` — guarded by default | Claude |
| 8 | *(no files)* | gcloud setting `api_endpoint_overrides/modelarmor`; template `hr-assistant-guardrail` created in Google Cloud | You |
| 21 | `hr_assistant/config.py` | Model Armor settings, `GUARDRAIL_HISTORY_TURNS = 6` | Claude |
| 21 | `hr_assistant/prompts.py` | Identity lock; conversation questions allowed | Claude |
| 21 | `hr_assistant/pipeline.py` | `ask()`: input check → agent → output check | Claude |
| 21 | `hr_assistant/guardrails.py` | Created — Model Armor checks; input fails closed, output fails open | You |
| 21 | `hr_assistant/thread_memory.py` | Created — read recent user messages, replace a blocked answer | You |
| — | `.gitignore` | Added `DIFFERENCES.md` (kept off GitHub) | Claude |
| — | `DIFFERENCES.md`, `TESTS.md`, `CHANGELOG.md` | Created; updated as we go | Claude |
| 22 | `hr_assistant/config.py` | Groq settings; cache settings (0.93, 500 entries, 1 hour) | Claude |
| 22 | `hr_assistant/llm.py` | Replaced — LiteLLM Router: Gemini first, Groq after 2 failed retries | Claude |
| 22 | `hr_assistant/tools.py` | Reranker fallback to search order | Claude |
| 22 | `hr_assistant/semantic_cache.py` | Created — the semantic cache | Claude |
| 22 | `hr_assistant/thread_memory.py` | Added `record_turn` (cached answers saved to memory) | Claude |
| 22 | `hr_assistant/pipeline.py` | Cache in `ask()` (first question only); `build_hr_assistant` returns `(agent, cache)` | Claude |
| 22 | `main.py` | Uses the cache; prints status lines (`[CACHE HIT …]`) | Claude |
| 22 | `app.py` | Uses the cache | Claude |
| 23b | `hr_assistant/llm.py` | `_BackupWatcher` callback: logs `BACKUP MODEL USED` whenever Groq answers; registered once with the Router | Claude |
| 23c | `hr_assistant/config.py` | Evaluation settings: `GROQ_BASE_URL`, `JUDGE_MODEL_NAME`, `EVAL_DATASET_NAME` | Claude |
| 23c | `hr_assistant/evaluation_dataset.py` | Created — 21 test questions with reference answers from the policy files | You |
| 23c | `hr_assistant/evaluation.py` | Created — runs the agent, grades correctness + groundedness with the Groq judge, uploads to LangSmith | You |
| 23c | `evaluate.py` | Created — `python evaluate.py` | You |
| 23c | `hr_assistant/evaluation.py` | Graders return "not graded" (`score: None`) when there's no answer; summary shows PASS / FAIL / **ERROR** separately (ERRORS.md #16) | Claude |
| 23c | `hr_assistant/evaluation.py` | Groundedness = **N/A** for refusal-type questions (`not_covered`, `out_of_scope`); summary counts N/A separately and reports passed out of *graded* | Claude |
| 23d | `hr_assistant/redteam.py` | Created — 10 attacks, plain vs guarded on the noisy collection; leak markers + Groq judge; saves `results/redteam_results.json` | You |
| 23d | `redteam_test.py` | Created — `python redteam_test.py` | You |
| 23d | `hr_assistant/guardrails.py` | `GuardrailUnavailable`: a Model Armor outage on the question check raises this instead of looking like a block (still fails closed) (ERRORS.md #17) | Claude |
| 23d | `hr_assistant/pipeline.py` | `INPUT_UNAVAILABLE_MESSAGE` ("safety check temporarily unavailable…") returned on an outage | Claude |
| 23d | `hr_assistant/redteam.py` | Attacks hit by an outage reported as **ERROR — not tested**, excluded from the held totals | Claude |
| 24a | `Dockerfile` | Created — Python 3.11 + uv, BM25 model baked in at build time (`/app/models`), only `app.py` + `hr_assistant/` copied; Streamlit CORS/XSRF protections left on | You |
| 24a | `.dockerignore` | Created — keeps `.env`, secrets, `.venv`, data and notes out of the upload and the image | You |
| 24b | *(no files)* | Google Cloud: service account `hr-assistant-run` created with `roles/aiplatform.user` + `roles/modelarmor.user` only | You |
| 24c | `push_secrets.py` | Created — copies Jina/Qdrant/Groq keys from `.env` into Secret Manager, grants read access to `hr-assistant-run` per secret, verifies each against `.env` without printing it | You |
| 24c | `deploy.env.yaml` | Created — non-secret Cloud Run settings (project, `LOCATION=global`, Qdrant URL, model, Model Armor, tracing off, allow-list empty) | You |
| 24c | `.gitignore` | Added `deploy.env.yaml` | You |
| 24d | *(no files)* | Billing: project relinked from own billing account (`<own-billing-account>`, free trial ending 2026-10-14) to a friend's billing account (`<friends-billing-account>`) | You |
| 24d | *(no files)* | Google Cloud: Cloud Run service `hr-rag-assistant` (us-central1) deployed **private**, as `hr-assistant-run`, 2 GiB, max 2 instances, session affinity; image built by Cloud Build; `cloud-run-proxy` gcloud component installed locally | You |
| 24e | *(no files)* | Google Auth Platform: consent screen "HR Policy Assistant" (External, **Testing**), 2 test users, Web client `hr-assistant-streamlit` with redirect URIs `http://localhost:8501/oauth2callback` + `<service-url>/oauth2callback` | You |
| 24e | `.streamlit/secrets.toml` | Created — Google login settings for the laptop (`redirect_uri` = localhost); private | You |
| 24e | `.streamlit/secrets.cloud.toml` | Created — same settings with the Cloud Run `redirect_uri`; for Secret Manager | You |
| 24e | `.gitignore`, `.dockerignore` | `.streamlit/secrets.toml` → whole `.streamlit/` folder | You |
| 24e | `hr_assistant/config.py` | `ALLOWED_EMPLOYEE_EMAILS` — lower-cased set from settings | Claude |
| 24e | `app.py` | Login gate before the assistant is built (Google login, `email_verified`, case-insensitive allow-list); fails closed on Cloud Run without login settings; status lines + access decisions logged | Claude |
| 24e | `.env` | `ALLOWED_EMPLOYEE_EMAILS=approved-user-1@example.com,approved-user-2@example.com` (only that line touched) | Claude |
| 24e | *(no files)* | Secret Manager: `streamlit-auth` created from `.streamlit/secrets.cloud.toml` (settings verified identical), readable only by `hr-assistant-run` | Claude |
| 24e | `deploy.env.yaml` | `ALLOWED_EMPLOYEE_EMAILS: "approved-user-1@example.com,approved-user-2@example.com"` (only that line touched) | Claude |
| 24e | `Dockerfile` | `--browser.gatherUsageStats=false` added to the start command | Claude |

## Cleanup (step 25 — light tidy-up)

| Step | File | Change | Made by |
|---|---|---|---|
| 25 | *(no files)* | Google Cloud: deleted old revision `hr-rag-assistant-00001` and 2 unused container images (kept the live one, `latest`); disabled version 1 of `groq-api-key` and `qdrant-api-key` (duplicates; reversible); switched off the Cloud Quotas API | Claude |

## Publishing

| Step | File | Change | Made by |
|---|---|---|---|
| GitHub | `README.md` | Created — overview, architecture diagrams (mermaid), tech stack, measured results, design decisions, structure, how to run/deploy | Claude |
| GitHub | `.env.example`, `deploy.env.example.yaml`, `secrets.toml.example` | Created — settings templates with placeholders only | Claude |
| GitHub | `TESTS.md`, `PROGRESS.md`, `CHANGELOG.md` | Personal details replaced with placeholders (emails, billing IDs, live URL) | Claude |
| GitHub | *(git)* | Repository initialised; first commit `ec84e05` (57 files) after scanning for keys/emails | Claude |
| GitHub | *(git)* | Pushed to `github.com/samriddhi56652/hr-policy-assistant` (public) | You |
