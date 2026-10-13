# HR Policy Assistant — the container image Cloud Run runs.
# Built in Google Cloud by `gcloud run deploy --source .` (no local Docker needed).

FROM python:3.11-slim
WORKDIR /app

# uv: the fast installer we use locally, copied from its official image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 1. Libraries first. Docker caches this step, so later code-only changes rebuild fast.
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# 2. Download the BM25 keyword-search model NOW, at build time, into a fixed folder.
#    Without this, every cold start downloads it from HuggingFace — which rate-limits
#    Cloud Run and crashes startup ("Could not load model Qdrant/bm25").
ENV FASTEMBED_CACHE_PATH=/app/models
RUN python -c "from fastembed import SparseTextEmbedding; SparseTextEmbedding(model_name='Qdrant/bm25')"

# 3. The app itself — only what the chat window needs.
COPY hr_assistant/ ./hr_assistant/
COPY app.py .

# Cloud Run tells the container which port to use, through $PORT.
ENV PORT=8080
# gatherUsageStats=false: don't send anonymous usage data from users' browsers to Streamlit.
CMD ["sh", "-c", "streamlit run app.py --server.port=${PORT} --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false"]