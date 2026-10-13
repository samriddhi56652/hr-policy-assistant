"""redteam_test.py — run the attack set against PLAIN and GUARDED, side by side.

    python redteam_test.py
Takes ~8-10 minutes. Results: results/redteam_results.json
"""

import logging

from hr_assistant.redteam import run_redteam

logging.basicConfig(level=logging.WARNING, format="  [%(message)s]")

if __name__ == "__main__":
    run_redteam()