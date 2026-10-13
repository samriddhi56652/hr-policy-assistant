"""guardrails — Model Armor safety check on text going IN to and OUT of the assistant.

Different from step 20's scope guardrail (which limits WHAT can be searched).
This one screens the raw text for attacks and unsafe content:
    check_input()   before the question reaches Gemini
    check_output()  before the answer reaches the user

If Model Armor itself fails (outage, timeout):
    input  -> fail CLOSED (refuse): an unchecked question must never reach Gemini.
              Raises GuardrailUnavailable, so the caller can say "unavailable"
              instead of "flagged" (see ERRORS.md #17).
    output -> fail OPEN (allow):    don't throw away a good answer over a hiccup
"""

import logging
from functools import lru_cache

from google.cloud import modelarmor_v1

from hr_assistant import config

logger = logging.getLogger(__name__)


class GuardrailUnavailable(Exception):
    """Model Armor itself failed (outage, timeout) — different from a real block."""

_MATCH = modelarmor_v1.FilterMatchState.MATCH_FOUND  # Model Armor's "something was found"


@lru_cache(maxsize=1)
def _client():
    """One Model Armor connection, on its regional address (see ERRORS.md #14)."""
    return modelarmor_v1.ModelArmorClient(
        client_options={"api_endpoint": f"modelarmor.{config.MODEL_ARMOR_LOCATION}.rep.googleapis.com"}
    )


def _template() -> str:
    return (
        f"projects/{config.PROJECT_ID}/locations/{config.MODEL_ARMOR_LOCATION}"
        f"/templates/{config.MODEL_ARMOR_TEMPLATE_ID}"
    )


def _is_safe(text: str, direction: str) -> bool:
    """Ask Model Armor about one piece of text. True = nothing harmful found."""
    data = modelarmor_v1.DataItem(text=text)
    if direction == "input":
        request = modelarmor_v1.SanitizeUserPromptRequest(name=_template(), user_prompt_data=data)
        result = _client().sanitize_user_prompt(request=request).sanitization_result
    else:
        request = modelarmor_v1.SanitizeModelResponseRequest(name=_template(), model_response_data=data)
        result = _client().sanitize_model_response(request=request).sanitization_result
    return result.filter_match_state != _MATCH


def _check(text: str, direction: str, fail_open: bool) -> bool:
    if config.GUARDRAIL_PROVIDER == "none":
        return True
    try:
        safe = _is_safe(text, direction)
    except Exception:
        # Model Armor itself broke — decide by direction (see top of file).
        logger.exception("Model Armor error on %s check — failing %s",
                         direction, "open" if fail_open else "closed")
        if fail_open:
            return True
        raise GuardrailUnavailable(direction)
    logger.info("%s GUARDRAIL: %s", direction.upper(), "pass" if safe else "BLOCK")
    return safe


def check_input(text: str) -> bool:
    """True = the question may go to Gemini. Raises GuardrailUnavailable if Model Armor is down."""
    return _check(text, "input", fail_open=False)


def check_output(text: str) -> bool:
    """True = the answer may be shown to the user."""
    return _check(text, "output", fail_open=True)