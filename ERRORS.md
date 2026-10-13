# Errors & Fixes Log

Every problem we hit while building, what caused it, and how we fixed it.
Newest at the bottom.

---

### 1. `gcloud` is not recognized (first time)
- **Step:** 1 — Install Google Cloud CLI
- **Error:** `gcloud : The term 'gcloud' is not recognized as the name of a cmdlet...`
- **Cause:** The Google Cloud CLI wasn't installed on the computer at all.
- **Fix:** Installed it from cloud.google.com/sdk (or `winget install --id Google.CloudSDK -e`), then opened a new terminal.

### 2. Compute Engine error during `gcloud init`
- **Step:** 2 — `gcloud init`
- **Error:** `Compute Engine API has not been used in project hr-rag-assistant-510309 before or it is disabled.`
- **Cause:** At the end of setup, `gcloud init` tries to pick a default region for virtual machines, which needs the Compute Engine service. We don't use virtual machines.
- **Fix:** None needed — harmless. Setup still finished. Do not enable Compute Engine just to clear it.

### 3. `gcloud` is not recognized (after installing)
- **Step:** 3 — `gcloud auth application-default login`
- **Error:** `'gcloud' is not recognized as an internal or external command`
- **Cause:** gcloud was installed, but the terminal had been opened *before* the install. A terminal reads the list of program folders (PATH) only when it opens, so it didn't know about gcloud.
- **Fix:** Closed and reopened the terminal (if inside VS Code: quit and reopen VS Code completely).

### 4. Package download failed — "No such host is known"
- **Step:** 10 — `uv pip install -r requirements.txt`
- **Error:** `Failed to download numpy==2.4.6 ... dns error ... No such host is known. (os error 11001)`
- **Cause:** A brief internet drop — for a few seconds the computer couldn't look up the download server's address.
- **Fix:** Ran the same install command again. Nothing was wrong with the setup.

### 5. Package download timed out — onnxruntime
- **Step:** 10 — `uv pip install -r requirements.txt`
- **Error:** `Failed to download onnxruntime==1.30.0 ... network timeout. Try increasing UV_HTTP_TIMEOUT (current value: 30s).`
- **Cause:** onnxruntime is a large file; on a slow connection it didn't finish within uv's 30-second limit.
- **Fix:** Gave downloads more time and fewer at once, then re-ran:
  `set UV_HTTP_TIMEOUT=300` and `set UV_CONCURRENT_DOWNLOADS=2`

### 6. No module named `hr_assistant.embeddings`
- **Step:** 15 — Chunking + embeddings test
- **Error:** `ModuleNotFoundError: No module named 'hr_assistant.embeddings'`
- **Cause:** The file was saved as `embeddings` instead of `embeddings.py`. Python only treats files ending in `.py` as code. Windows hides file extensions by default, so it was easy to miss.
- **Fix:** Renamed it to `embeddings.py`. Turned on File Explorer → View → Show → **File name extensions** to avoid this again.

### 7. Paragraph breaks not recognised — Windows line endings (`\r\n`)
- **Step:** 15 — Chunking (found while checking step 15's output)
- **Error:** No crash. The chunk text showed `\r\n\r\n` between paragraphs instead of `\n\n`.
- **Cause:** The policy files were saved on Windows, which ends each line with two hidden characters (`\r\n`) instead of one (`\n`). The splitter looks for `\n\n` to find blank lines between sections, and `\r\n\r\n` doesn't contain `\n\n` — so it couldn't see where sections ended.
- **Fix:** One line in `hr_assistant/processor.py`, right after the text is extracted:
  `text = text.replace("\r\n", "\n")`
  Then rebuilt the processed files (`process_raw_to_json()`). Now each chunk is exactly one policy section (e.g. "3. Sick Leave").
- **Lesson:** Always look at the actual chunk text, not just the count — the count barely changed (69 → 68), but chunk quality did.

### 8. Gemini model "not found" in `us-central1`
- **Step:** 18 — Connect Gemini (found while testing before writing the step)
- **Error:** `404 ... Publisher model .../locations/us-central1/.../gemini-3.8-flash was not found or your project does not have access to it.`
- **Cause:** The newest Gemini models are only served from Google's **global** endpoint, not from individual regions like `us-central1`.
- **Fix:** In `.env`, set `LOCATION=global`. `LOCATION` is only used for Gemini — the bucket (`us-central1`) and Cloud Run (`REGION`) are unaffected.

### 9. Region setting ignored by `ChatLiteLLM`
- **Step:** 18 — Connect Gemini (found while testing)
- **Error:** Same 404 as #8, even after asking for `global` — the request still went to `us-central1`.
- **Cause:** Passing `vertex_location=...` directly to `ChatLiteLLM(...)` was silently ignored, so LiteLLM fell back to its default region.
- **Fix:** Pass the Google settings inside `model_kwargs`:
  `model_kwargs={"vertex_project": config.PROJECT_ID, "vertex_location": config.LOCATION}`
- **Also noticed:** Gemini 3+ warns that `temperature` is being phased out, so `llm.py` doesn't set it.

### 10. `can't open file '...\main.pyHow'`
- **Step:** 19 — Running `main.py`
- **Error:** `python.exe: can't open file '...\HR_AI_Assistant\main.pyHow': [Errno 2] No such file or directory`
- **Cause:** The question was typed on the same line as the command (`python main.py` + `How many days...`) before pressing Enter, so Python looked for a file literally called `main.pyHow`.
- **Fix:** Type `python main.py`, press **Enter**, wait for `Ready!` and the `You:` prompt, *then* type the question.

### 11. `main.py` and `app.py` in the wrong folder
- **Step:** 19 — `main.py` / `app.py`
- **Error:** (Would have been) `can't open file '...\HR_AI_Assistant\main.py'` — the root folder had no `main.py`.
- **Cause:** Both files were created inside `hr_assistant/` instead of the main `HR_AI_Assistant` folder. `hr_assistant/` is for building blocks; files you *run* (`ingest.py`, `main.py`, `app.py`) go in the main folder.
- **Fix:** Moved both into `HR_AI_Assistant/` (drag them out of `hr_assistant` in the VS Code Explorer). `pipeline.py` correctly stays in `hr_assistant/`.

### 12. `streamlit.exe` blocked by Device Guard policy
- **Step:** 19 — `streamlit run app.py`
- **Error:** `'...\.venv\Scripts\streamlit.exe' was blocked by your organization's Device Guard policy.`
- **Cause:** Windows security (Smart App Control / Device Guard) blocks small unsigned `.exe` launcher files, like the `streamlit.exe` that pip/uv creates inside `.venv\Scripts`. `python.exe` itself is allowed, which is why `python main.py` worked.
- **Fix:** Run Streamlit through Python instead of its launcher:
  `python -m streamlit run app.py`
  (`-m` = "run this installed package as a program". Same result, no blocked `.exe`.) Don't turn off the Windows security setting.

### 13. `DLL load failed while importing cygrpc: An Application Control policy has blocked this file`
- **Step:** 20 — running the checkpoints
- **Error:** `ImportError: DLL load failed while importing cygrpc: An Application Control policy has blocked this file.` (the traceback runs through `qdrant_client` → `grpc`)
- **Cause:** Windows security (the same Smart App Control / Device Guard as #12) blocked a compiled file inside the `grpc` package, which the Qdrant library loads. It was **temporary**: seconds later the same file loaded fine, twice in a row. Most likely Windows was still checking the file's reputation the first time.
- **Fix:** Simply ran the command again. If it ever keeps failing, don't switch off the Windows security setting — tell me, and we'll look at the alternatives (e.g. reinstalling the package).

### 14. Model Armor: "Read access to project was denied"
- **Step:** 8 — Model Armor template (found while checking before the step)
- **Error:** `PERMISSION_DENIED: Read access to project 'hr-rag-assistant-510309' was denied.`
- **Cause:** Misleading message — the account is the project **owner** and the Model Armor service is enabled. Model Armor only answers on a **regional address** (`modelarmor.us.rep.googleapis.com`); gcloud was calling Google's general address, which refuses.
- **Fix:** Point gcloud at the regional address once (saved in gcloud's settings):
  `gcloud config set api_endpoint_overrides/modelarmor https://modelarmor.us.rep.googleapis.com/`
- **Lesson:** "Permission denied" doesn't always mean a permissions problem — check the role and the service first.

### 15. `--rai-settings-filters: Invalid choice: high filtertype=hate-speech`
- **Step:** 8 — Model Armor template (running the command in **PowerShell**)
- **Error:** `argument --rai-settings-filters: Invalid choice: high filtertype=hate-speech. Valid choices are: [... high, ...]`
- **Cause:** In PowerShell, a comma means "make a list". So `confidenceLevel=high,filterType=HATE_SPEECH` was split into two pieces and re-joined with a **space**, and gcloud received `high filterType=...` as one broken value. The Command Prompt (cmd) doesn't do this, which is why the command looked correct.
- **Fix:** Put each value containing a comma in quotes:
  `--rai-settings-filters="confidenceLevel=high,filterType=HATE_SPEECH"`
- **Lesson:** In PowerShell, quote any argument that contains a comma (or other special characters like `;`, `@`, `{ }`).

### 16. Evaluation: every question "FAIL", `getaddrinfo failed`, `KeyError: 'answer'`
- **Step:** 23c — first `python evaluate.py` run
- **Error:** `qdrant_client ... ResponseHandlingException: [Errno 11001] getaddrinfo failed`, then for every question `KeyError: 'answer'` / `KeyError: 'context'`, all 20 shown as `FAIL`, ending with `Failed to resolve 'api.smith.langchain.com'`.
- **Cause:** The internet connection dropped during the run (`getaddrinfo failed` = the computer couldn't look up any server's address — Qdrant, then LangSmith). The assistant couldn't run at all, so it returned no answer; the graders then crashed looking for one, and the summary counted those crashes as `FAIL`. **No answer was actually graded** — the FAILs say nothing about answer quality.
- **Fix:** Re-run once the connection is back (checked: all servers reachable again, and the 21 test questions were uploaded correctly before the drop). Plus a change to `evaluation.py` so a question that never produced an answer shows as **ERROR**, not FAIL.
- **Lesson:** A test that can't run must never look like a test that failed.

### 17. Model Armor `504 Deadline Exceeded` — and it looked like a block
- **Step:** 23d — first `python redteam_test.py` run
- **Error:** `Model Armor error on input check — failing closed` … `google.api_core.exceptions.DeadlineExceeded: 504 Deadline Exceeded`
- **Cause:** Model Armor didn't answer in time (a slow moment on Google's side) for the `persona_override` attack. As designed, the question check **failed closed** and refused the question — but it used the **same** message as a real block ("flagged by the safety check"). So the report said Model Armor *stopped* the attack, when Model Armor never actually looked at it (earlier probes show Model Armor lets this attack through; the identity lock is what stops it).
- **Fix:** Give an outage its own message ("the safety check is temporarily unavailable — please try again") and mark such attacks **ERROR / not tested** in the red-team report, instead of "held".
- **Lesson:** "Refused because unsafe" and "refused because the checker was down" must look different — to users and in test reports.

### 18. `deploy.env.yaml` can't be read — `expected <block end>, but found '<scalar>'`
- **Step:** 24c — checking `deploy.env.yaml`
- **Error:** `yaml.parser.ParserError: while parsing a block mapping … line 9, column 26`
- **Cause:** The `QDRANT_URL` line was missing its **closing quote** (`QDRANT_URL: "https://…` with no `"` at the end). In YAML an opening `"` runs until the next `"`, so the reader swallowed the next line and got confused — the error points at line 9, one line *after* the real mistake.
- **Fix:** Added the closing `"`. Checked: file reads correctly (11 settings), the URL matches `.env`, no API keys in the file.
- **Lesson:** A YAML error's line number can point just *past* the real problem — check the line above it too.

### 19. `Invalid Origin: URIs must not contain a path or end with "/"`
- **Step:** 24e part 1 — creating the OAuth login client
- **Error:** Shown under both addresses when they were typed into **Authorized JavaScript origins**.
- **Cause:** Wrong box. The client form has two look-alike sections: *JavaScript origins* accepts only bare site addresses (no path); *Authorized redirect URIs* is where the full `…/oauth2callback` addresses go.
- **Fix:** Deleted both entries from JavaScript origins (left empty — not needed) and added them under **Authorized redirect URIs**.
- **Lesson:** Redirect URIs are full addresses ending in `/oauth2callback`; they never go in the "origins" box.

### 20. OAuth client secret copied without its `GOCSPX-` prefix
- **Step:** 24e part 2 — `.streamlit/secrets.toml`
- **Error:** No error yet — caught by the file check: `client_secret starts GOCSPX-: False`, length 28 instead of 35.
- **Cause:** Only the part after `GOCSPX-` was copied (double-click selection stops at the dash). Google would have rejected the login as an invalid client.
- **Fix:** Re-copied the full secret from the downloaded JSON into both `secrets.toml` and `secrets.cloud.toml` → 35 characters, starts with `GOCSPX-`.
- **Lesson:** Copy secrets from the JSON / with select-all, not double-click — and check the expected format before testing.
