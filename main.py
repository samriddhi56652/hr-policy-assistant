"""main.py — chat with the HR assistant in the terminal.

    python main.py
    Type 'new' for a fresh conversation, 'quit' to exit.
"""

import logging
import uuid

from hr_assistant.pipeline import ask, build_hr_assistant


def main():
    print("Setting up the HR assistant...")
    # Show our own status lines (cache hits, guardrail blocks) — but not every library's chatter.
    logging.basicConfig(level=logging.WARNING, format="  [%(message)s]")
    logging.getLogger("hr_assistant").setLevel(logging.INFO)

    agent, cache = build_hr_assistant()
    thread_id = str(uuid.uuid4())  # a random ID for this conversation

    print("Ready! Ask about HR policy. Type 'new' for a fresh conversation, 'quit' to exit.\n")
    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in {"quit", "exit"}:
            break
        if question.lower() == "new":
            thread_id = str(uuid.uuid4())  # new ID = forgets the old conversation
            print("(new conversation)\n")
            continue

        print(f"\nAssistant: {ask(agent, cache, question, thread_id)}\n")


if __name__ == "__main__":
    main()