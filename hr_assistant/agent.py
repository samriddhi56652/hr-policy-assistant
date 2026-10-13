"""agent — Gemini + system prompt + tools, with memory of the conversation."""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from hr_assistant.prompts import SYSTEM_PROMPT


def create_hr_agent(llm, tools, checkpointer=None):
    """Build the agent. The checkpointer is its memory: it stores each
    conversation's messages, keyed by a thread_id, so follow-up questions
    ('and casual leave?') make sense."""
    return create_agent(
        llm,
        tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer or InMemorySaver(),
    )