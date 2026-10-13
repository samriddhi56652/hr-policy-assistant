"""app.py — the chat window in your browser.

    python -m streamlit run app.py --server.address=localhost

With .streamlit/secrets.toml present, visitors must log in with Google and be on
ALLOWED_EMPLOYEE_EMAILS. Without it: open mode on the laptop, refusal on Cloud Run.
"""

import logging
import os
import uuid

import streamlit as st

from hr_assistant import config
from hr_assistant.pipeline import ask, build_hr_assistant

# Our own status lines (guardrail pass/block, cache hits, backup model, access
# decisions) go to the server console — on Cloud Run, that's the service's logs.
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("hr_assistant").setLevel(logging.INFO)
logger = logging.getLogger("hr_assistant.app")

ON_CLOUD_RUN = bool(os.getenv("K_SERVICE"))  # Cloud Run sets K_SERVICE in every container

st.set_page_config(page_title="HR Policy Assistant", page_icon="🤖")
st.title("🤖 HR Policy Assistant")
st.caption("Ask me anything about company HR policy — leave, WFH, notice period, and more.")


# ── Login gate: runs BEFORE the assistant is built, so refused visitors cost nothing ──

def _login_configured() -> bool:
    """True when .streamlit/secrets.toml has an [auth] section — the laptop file,
    or the copy Secret Manager places inside the container on Cloud Run."""
    try:
        return "auth" in st.secrets
    except Exception:  # no secrets file at all
        return False


if _login_configured():
    if not st.user.is_logged_in:
        st.info("Please log in with your company Google account.")
        st.button("Log in with Google", on_click=st.login)
        st.stop()

    email = (st.user.email or "").lower()
    if not st.user.get("email_verified", False) or email not in config.ALLOWED_EMPLOYEE_EMAILS:
        logger.warning("ACCESS DENIED for %s", email or "<no email>")
        st.error(f"'{st.user.email}' isn't on the approved employee list.")
        st.button("Log out", on_click=st.logout)
        st.stop()

    if not st.session_state.get("access_logged"):  # log once per browser session
        logger.info("ACCESS GRANTED for %s", email)
        st.session_state.access_logged = True
    st.sidebar.caption(f"Logged in as {st.user.email}")
    st.sidebar.button("Log out", on_click=st.logout)

elif ON_CLOUD_RUN:
    # On the internet, never run without a login — fail closed.
    logger.error("Login settings missing on Cloud Run — refusing to serve the assistant.")
    st.error("Login is not configured on this server, so the assistant is unavailable.")
    st.stop()

else:
    st.sidebar.warning("Open local mode — Google login is not configured.")


@st.cache_resource(show_spinner="Setting up the assistant (only happens once)...")
def get_agent():
    return build_hr_assistant()


agent, cache = get_agent()

# Each browser tab gets its own conversation ID and its own visible history.
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []

if st.sidebar.button("New conversation"):
    st.session_state.thread_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.rerun()

# Redraw the conversation so far.
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle a new question.
if question := st.chat_input("Ask a question about HR policy..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            answer = ask(agent, cache, question, st.session_state.thread_id)
        st.markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})