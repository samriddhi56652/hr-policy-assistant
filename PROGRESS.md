# HR AI Assistant — Build Progress

Project ID: `hr-rag-assistant-510309` · Region: `us-central1` · Bucket: `hr-rag-assistant-510309-docs`

Each step: **What** it is, and **Why** we're doing it.

## Setup — Google Cloud

- [x] **1. Install Google Cloud CLI (gcloud)**
  - What: The command-line tool for controlling Google Cloud from your terminal.
  - Why: Every cloud setup step (login, services, bucket, deploy) is a gcloud command.

- [x] **2. `gcloud init`**
  - What: Signs gcloud in as you and sets `hr-rag-assistant-510309` as the default project.
  - Why: So every later command acts on the right account and project without repeating them. (The Compute Engine error is harmless — we don't use VMs.)

- [x] **3. `gcloud auth application-default login`**
  - What: A second login, this one for your Python code (not the gcloud tool).
  - Why: The code needs credentials to reach Cloud Storage, Vertex AI (Gemini) and Model Armor.

- [x] **4. Set quota project**
  - What: Attaches the Python code's login to `hr-rag-assistant-510309`.
  - Why: Google needs to know which project to bill and count usage against when the code calls its services.

- [x] **5. Check billing is linked**
  - What: Confirms the project has a billing account.
  - Why: Gemini, Model Armor, Storage and Cloud Run refuse to work without one.

- [x] **6. Enable the 7 services**
  - What: Switches on Vertex AI, Storage, Model Armor, Cloud Run, Cloud Build, Artifact Registry, Secret Manager.
  - Why: Google Cloud services are off by default in a new project; calls to a disabled one fail.

- [x] **7. Create the storage bucket**
  - What: A cloud folder, `gs://hr-rag-assistant-510309-docs`, in `us-central1`.
  - Why: Holds the original documents (`raw/`) and their extracted text (`processed/`) so documents are parsed once and the deployed app can reach them.

- [x] **8. Create the Model Armor template** *(created 2026-10-13: `hr-assistant-guardrail` in `us`; gcloud pointed at the regional address, see ERRORS.md #14–15)*
  - What: A saved set of safety rules (`hr-assistant-guardrail`) that Model Armor checks text against: jailbreaks/prompt injection, sensitive data, harmful content, malicious links.
  - Why: The app screens every question before Gemini sees it, and every answer before the user sees it.

## Setup — Outside services and local

- [x] **9. Get API keys: Jina AI, Qdrant Cloud, Groq**
  - What: Accounts and keys for three services outside Google.
  - Why: Jina turns text into vectors and re-ranks results; Qdrant stores and searches those vectors; Groq is the backup model if Gemini fails (and the judge in step 23).

- [x] **10. Python virtual environment + install packages** *(144 packages installed; langchain 1.4.3, langgraph 1.2.12)*
  - What: A `.venv` folder with its own Python 3.11 and the packages from `requirements.txt`.
  - Why: Keeps this project's packages separate from everything else on your PC; 3.11 matches the original project and avoids packages that lag on newer Python.

- [x] **11. Create `.env`** *(Jina, Qdrant, Groq keys in; Gemini model ID added at step 18, LangSmith key at step 23)*
  - What: A text file of settings and secret keys (project ID, bucket, region, API keys).
  - Why: Keeps secrets out of the code; the code reads them at startup, and changing a value needs no code edit.

- [x] **12. `.gitignore` + `data/` folder** *(10 HR policies + 8 noise docs in `data/`)*
  - What: A file listing what git must never save, plus the 10 HR policies and 8 "noise" documents.
  - Why: `.gitignore` stops your keys leaking to GitHub. The data is what the assistant answers from; the noise docs test that it stays on HR topics.

## Build — Phase 1: Basic RAG (first working answer)

- [x] **13. `config.py`**
  - What: One file that reads every setting from `.env`.
  - Why: Every other file imports settings from one place instead of reading `.env` itself.

- [x] **14. Document loading + processing** *(18 uploaded/processed/loaded; all categories found)*
  - What: Reads txt/pdf/docx/pptx files, uploads originals to the bucket, saves extracted text as JSON with a policy category label.
  - Why: The model can only work with plain text; the category label is what lets step 20 restrict searches to HR.

- [x] **15. Chunking + Jina embeddings** *(68 chunks from 10 HR docs, one per policy section; Windows `\r\n` line endings normalised in processor.py)*
  - What: Splits text into 500-character pieces (60 overlapping) and turns each into 768 numbers (a vector).
  - Why: Searching small pieces finds the exact relevant passage; vectors let the computer compare meaning, not just words.

- [x] **16. Qdrant vector store + `ingest.py`** *(hr_policies: 68 chunks · hr_policies_noisy_demo: 82 chunks)*
  - What: Stores every chunk with both a meaning vector and a keyword (BM25) vector; `ingest.py` runs the whole load once.
  - Why: Hybrid search catches both "similar meaning" and "exact term" matches (like "casual leave").

- [x] **17. Jina reranker + `search_hr_policy` tool** *("sick leave" → "3. Sick Leave" ranked first, 0.69)*
  - What: Fetches 12 candidate chunks, re-scores them, keeps the best 5 with `[Source: file]` citations.
  - Why: The first search is fast but rough; re-ranking is slower but more accurate, so the model gets the best evidence.

- [x] **18. Gemini + system prompt + agent** *(gemini-3.8-flash via LOCATION=global; agent searches then answers with citation)*
  - What: Connects Gemini 3.x Flash on Vertex AI, writes its instructions, and builds an agent that decides when to call the search tool.
  - Why: Gemini writes the final answer using only what the search returns. (Not 2.5 Flash — it retires ~2026-10-20. Use `gemini-3.8-flash`: latest Flash, released 2026-09-02, no retirement date announced as of 2026-10-03.)

- [x] **19. `main.py` + `app.py`** *(both work — cited answers, memory, reset, adaptive length, out-of-scope refusal. Run the UI with `python -m streamlit run app.py --server.address=localhost`)*

**✅ Phase 1 complete (2026-10-07).**
  - What: A terminal question-and-answer script, then a Streamlit chat window.
  - Why: The first end-to-end test of the whole pipeline, then a usable interface.

## Build — Phase 2: Security & reliability

- [x] **20. Scope guardrail** *(noisy collection: plain tool leaks Q3 revenue $18.4M, guarded tool → NOT_FOUND; sick leave still 0.69; dress code → "don't have that information")*
  - What: Search only returns the 10 HR categories; weak matches return NOT_FOUND.
  - Why: Finance/Sales data becomes impossible to retrieve, and the model declines instead of guessing.
  - Calibration (2026-10-08, 15 test questions on the noisy collection): real HR questions' top score 0.54–0.74; HR-sounding but unanswered 0.07–0.28; out-of-scope with filter ≤ 0.05 → threshold **0.35**. Gate on the TOP score only — a per-chunk cut-off would strip relevant sections from broad answers (e.g. exit process sections scored 0.32 / 0.25).

- [x] **21. Model Armor guardrail + conversation memory** *(jailbreak + card number blocked by Model Armor; "You are Drishti" declined by the identity lock; "what was my previous question?" now answered)*
  - What: Screens questions and answers using the step 8 template; remembers earlier turns per conversation.
  - Why: Blocks attacks and harmful output; memory makes follow-ups like "tell me more" work.
  - Also: the Phase 1 prompt refuses harmless questions about the conversation itself ("What was my previous question?") as "not HR". Allow those, then re-run the red-team tests to check it doesn't open a loophole.

- [x] **22. Semantic cache + Groq fallback** *(cache: reworded question 16.4 s → 1.0 s, look-alike "annual leave" correctly not cached; Groq answered when Gemini was broken; reranker failure → search order, still correct)*
  - What: Reuses answers to near-identical questions; switches to Groq if Gemini errors.
  - Why: Faster and cheaper for repeat questions; keeps working during a Gemini outage. (Avoid the original's cross-user follow-up bug.)
  - Also: if the Jina reranker fails or times out, fall back to the top 5 search results instead of failing the whole question (try/except in `tools.py`).

- [x] **23. Evaluation + red-team tests** — **✅ Phase 2 complete (2026-10-13)** *(LangSmith key verified 2026-10-13; Groq judge `gpt-oss-120b` reachable)*
  - [x] 23a. Timing — find out why uncached answers take 16–22 s *(measured: Jina embeddings 0.5–13.5 s per call ×2, Gemini 3.5–8.9 s. Jina limits fine (free key: 100 RPM / 100k TPM). Small fixes (Model Armor warm-up, Gemini low reasoning) **deferred**; local embeddings (option C) to be decided after the 23c quality baseline)*
  - [x] 23b. Log a warning when Groq answers instead of Gemini *(`[BACKUP MODEL USED …]` appears only when Groq answers)*
  - [x] 23c. Answer-quality evaluation in LangSmith (correctness + groundedness, Groq judge) *(baseline confirmed after N/A fix: correctness 21/21, groundedness 19/19 + 2 N/A — experiment `hr-assistant-673c9129`)*
  - [x] 23d. Red-team: fixed attack set (incl. multi-message), plain vs guarded *(run 2: both held 10/10; guarded: confidential text reached Gemini 0×; Model Armor outage now shown as "unavailable", not "flagged")*
  - What: A different model scores answers for correctness and grounding in LangSmith; attack prompts test the guardrails.
  - Why: Measures quality with numbers instead of impressions, and proves the safety layers actually hold.

## Build — Phase 3: Deployment

- [x] **24. Docker → Cloud Run + Google login** — **✅ live at <service-url> (2026-10-14)**
  - [x] 24a. Dockerfile + `.dockerignore` — the recipe for the container image
  - [x] 24b. A dedicated service account with only the permissions the app needs *(`hr-assistant-run`: aiplatform.user + modelarmor.user only — the default account has Editor)*
  - [x] 24c. API keys into Secret Manager; non-secret settings in `deploy.env.yaml` *(3 secrets, each readable only by `hr-assistant-run`, verified against `.env`; `deploy.env.yaml` valid, git-ignored)*
  - [x] 24d. First deploy — **private** (only you can reach it), tested through `gcloud run services proxy` *(deployed first try; strangers get 403; chat via tunnel: sick leave ✅, follow-up ✅, revenue refused ✅; logs clean)*
  - [x] 24e. Google login + employee allow-list, then make it public *(allowed: approved-user-1@example.com, approved-user-2@example.com)*
    - [x] 1. Consent screen (Testing) + 2 test users + Web client with localhost and run.app redirect URIs
    - [x] 2. `.streamlit/secrets.toml` (laptop) + `secrets.cloud.toml` (cloud) — client ID/secret, cookie secret; `.streamlit/` git- and docker-ignored
    - [x] 3. Login check + cloud status logs in `app.py`; allow-list in `config.py` *(gate tested: logged-out → login button only; Cloud Run without login settings → refuses)*
    - [x] 4. Test login on the laptop *(real Google sign-in → chat, "Logged in as approved-user-1@example.com"; refused case moved to part 6, in the cloud)*
    - [x] 5. Login settings → Secret Manager; redeploy public (usage stats off, timeout 900 s) *(revision 00002; stranger sees only the login page)*
    - [x] 6. Test: allowed email in, other email refused *(live app: GRANTED / DENIED both logged; Google's test-user list did not block the unlisted account — the app's allow-list is the effective gate)*
  - [x] 24f. Final checks: logs, allowed vs. not-allowed email *(full question traced in the cloud logs; no errors)*
  - What: Packages the app in a container, hosts it on Cloud Run, requires company Google login plus an email allow-list.
  - Why: Makes it available to employees at a URL, and only to approved employees.
  - Course lectures: "Writing Docker file", "Deployment". Also review the original Dockerfile's disabled CORS/XSRF protection.

- [x] **Published on GitHub** — https://github.com/samriddhi56652/hr-policy-assistant (public, 2026-10-14)
  - What: README with architecture diagrams, results and design decisions; example settings files; personal details in the notes replaced with placeholders.
  - Why: To show the project (code + how it was built and tested) to interviewers. Secrets and private notes stay out via `.gitignore` — checked before the first push.

- [ ] **25. Cleanup** *(full shutdown on hold — app kept live for interviews; cost control: allow-list, max 2 instances, 900 s timeout, scale to zero, budget alert on the paying account)*
  - [x] Light tidy-up (2026-10-14): old revision `00001` and 2 unused images deleted; old secret versions disabled; Cloud Quotas API switched off. BigQuery APIs left on (on by default in every project, unused, free)
  - What: Delete or stop the cloud resources once you're done (Cloud Run service, container images, bucket, Model Armor template, secrets, Qdrant cluster, API keys).
  - Why: Things left running keep costing money and leave keys and data online. Course lecture: "Cleanup".
