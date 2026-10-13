"""evaluate.py — grade the assistant's answers (correctness + groundedness) in LangSmith.

    python evaluate.py
Takes ~6-8 minutes. Needs LANGSMITH_API_KEY and GROQ_API_KEY in .env.
"""

import logging

from hr_assistant.evaluation import run_evaluation

logging.basicConfig(level=logging.WARNING, format="  [%(message)s]")

if __name__ == "__main__":
    run_evaluation()