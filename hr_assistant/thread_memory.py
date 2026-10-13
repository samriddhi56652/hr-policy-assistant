"""thread_memory — small helpers that read and edit the agent's conversation memory."""

from langchain_core.messages import AIMessage, HumanMessage

from hr_assistant import config


def _thread(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def recent_user_messages(agent, thread_id: str, limit: int = config.GUARDRAIL_HISTORY_TURNS) -> list[str]:
    """The last `limit` things the USER said in this conversation.
    Only the user's own words — never the assistant's answers or the policy text,
    which would make every check bigger and could cause false alarms."""
    messages = agent.get_state(_thread(thread_id)).values.get("messages", [])
    return [m.text for m in messages if m.type == "human"][-limit:]


def replace_answer(agent, thread_id: str, answer_message, new_text: str) -> None:
    """Swap an answer already saved in memory for new_text.
    Same message id = REPLACE, not add — so a blocked answer doesn't stay in
    memory where Gemini could repeat it in a later turn."""
    agent.update_state(
        _thread(thread_id),
        {"messages": [AIMessage(id=answer_message.id, content=new_text)]},
    )


def record_turn(agent, thread_id: str, question: str, answer: str) -> None:
    """Save a (question, answer) pair to memory WITHOUT running the agent —
    used on a cache hit, so a follow-up ('does that carry forward?') still works."""
    agent.update_state(
        _thread(thread_id),
        {"messages": [HumanMessage(content=question), AIMessage(content=answer)]},
    )