"""pipeline — build the assistant once, then ask it questions.

    build_hr_assistant()  connect Qdrant + tool + Gemini + agent   (slow, do once)
    ask()                 one question in, one answer out          (every question)
"""

from hr_assistant import config
from hr_assistant.agent import create_hr_agent
from hr_assistant.llm import get_llm
from hr_assistant.tools import create_guarded_search_tool, create_search_tool
from hr_assistant.vector_store import load_vector_store
from hr_assistant.guardrails import GuardrailUnavailable, check_input, check_output
from hr_assistant.semantic_cache import SemanticCache
from hr_assistant.thread_memory import record_turn, recent_user_messages, replace_answer

INPUT_BLOCKED_MESSAGE = "I can't process that request — it was flagged by the safety check."
OUTPUT_BLOCKED_MESSAGE = "I can't share that answer — it was flagged by the safety check."
INPUT_UNAVAILABLE_MESSAGE = ("The safety check is temporarily unavailable, so I can't answer right now — "
                             "please try again in a moment.")


def build_hr_assistant(collection_name: str = config.QDRANT_COLLECTION_NAME, guarded: bool = True):
    """Wire everything together and return a ready-to-use agent.

    collection_name: the clean HR collection by default; pass
        config.QDRANT_NOISY_COLLECTION_NAME to test against HR + noise.
    guarded: True = scope guardrail on (always, for real use).
        False = the unprotected baseline, only for before/after testing."""
    config.check_api_keys()
    vector_store = load_vector_store(collection_name)
    make_tool = create_guarded_search_tool if guarded else create_search_tool
    agent = create_hr_agent(get_llm(), [make_tool(vector_store)])
    return agent, SemanticCache()


def ask(agent, cache, question: str, thread_id: str = "default") -> str:
    """Ask one question and return the answer text:

        1. input check   (new question + the user's recent messages)
        2. cache         (first question of a conversation only)
        3. agent         (search + Gemini, Groq as backup)
        4. output check  (the answer)
        5. save to cache (first question of a conversation only)

    Same thread_id = same conversation. New thread_id = fresh start.
    cache=None turns caching off."""
    history = recent_user_messages(agent, thread_id)

    # 1. Check the new question TOGETHER with the user's recent messages,
    #    so an attack split across several harmless-looking messages is still caught.
    #    Either way, a refused question never reaches Gemini and is never saved in memory.
    try:
        allowed = check_input("\n".join([*history, question]))
    except GuardrailUnavailable:
        return INPUT_UNAVAILABLE_MESSAGE  # failed closed — but say why
    if not allowed:
        return INPUT_BLOCKED_MESSAGE

    # 2. Cache — ONLY for the first question of a conversation. A follow-up like
    #    "does that carry forward?" means something different in every conversation,
    #    so it must never be answered from (or saved to) the cache.
    first_question = not history
    if cache is not None and first_question:
        cached_answer, question_vector = cache.lookup(question)
        if cached_answer is not None:
            record_turn(agent, thread_id, question, cached_answer)  # so follow-ups still work
            return cached_answer

    # 3. Search + Gemini.
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config={"configurable": {"thread_id": thread_id}},
    )
    answer_message = result["messages"][-1]
    # .text (not .content): Gemini can return the answer as a list of pieces;
    # .text always gives back one plain string.
    answer = answer_message.text

    # 4. Check the answer before the user sees it.
    if not check_output(answer):
        replace_answer(agent, thread_id, answer_message, OUTPUT_BLOCKED_MESSAGE)
        return OUTPUT_BLOCKED_MESSAGE

    # 5. Save for next time — only safe answers to first questions get here.
    if cache is not None and first_question:
        cache.store(question_vector, question, answer)
    return answer