"""llm — the chat model: Gemini on Vertex AI, with Groq as automatic backup.

LiteLLM's Router sends every call to Gemini first. If Gemini fails
(after 2 retries), the same call goes to Groq instead. The rest of the
code never knows which one answered.
"""

import logging

import litellm
from langchain_litellm import ChatLiteLLMRouter
from litellm import Router
from litellm.integrations.custom_logger import CustomLogger

from hr_assistant import config

logger = logging.getLogger(__name__)

# Gemini accepts some settings Groq doesn't — drop those on the way to Groq
# instead of failing.
litellm.drop_params = True

_PRIMARY = "hr-llm"
_BACKUP = "hr-llm-backup"

_router = None  # one Router for the whole program (it remembers retries and failures)


class _BackupWatcher(CustomLogger):
    """Logs a warning whenever the backup model (Groq) answers. The switch is
    otherwise silent, so Gemini could be down without anyone noticing."""

    def log_success_event(self, kwargs, response_obj, start_time, end_time):
        if kwargs.get("custom_llm_provider") == "groq":
            logger.warning("BACKUP MODEL USED — Gemini failed, Groq (%s) answered.", kwargs.get("model"))


def _get_router() -> Router:
    global _router
    if _router is None:
        litellm.callbacks.append(_BackupWatcher())  # register once, with the Router
        _router = Router(
            model_list=[
                {"model_name": _PRIMARY, "litellm_params": {
                    "model": f"vertex_ai/{config.LLM_MODEL_NAME}",
                    "vertex_project": config.PROJECT_ID,
                    "vertex_location": config.LOCATION,
                }},
                {"model_name": _BACKUP, "litellm_params": {
                    "model": f"groq/{config.FALLBACK_MODEL_NAME}",
                    "api_key": config.GROQ_API_KEY,
                }},
            ],
            num_retries=2,                       # try Gemini up to 2 more times...
            fallbacks=[{_PRIMARY: [_BACKUP]}],   # ...then switch to Groq
        )
    return _router


def get_llm():
    """The chat model the agent uses (Gemini, with Groq as backup)."""
    return ChatLiteLLMRouter(router=_get_router(), model_name=_PRIMARY)
