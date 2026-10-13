"""evaluation_dataset — the fixed test questions and their correct answers.

Every reference answer comes from the policy files in data/. If a policy
changes, update its reference here AND rename EVAL_DATASET_NAME in config.py
(LangSmith keeps the old copy, so a new name forces a fresh upload).
"""

EXAMPLES = [
    # ── Single facts ──────────────────────────────────────────────────────
    ("narrow", "How many days of sick leave do I get?",
     "10 days of paid sick leave per calendar year."),
    ("narrow", "Does unused sick leave carry forward to next year?",
     "No. Sick leave does not carry forward to the following year."),
    ("narrow", "How many days of annual leave do I get, and how much can I carry forward?",
     "18 days of paid annual leave per calendar year (accrued at 1.5 days per completed month). "
     "Up to 10 unused days can be carried forward; anything beyond that is forfeited on December 31st."),
    ("narrow", "When do I need a medical certificate for sick leave?",
     "For sick leave of 3 or more consecutive days. It must be submitted to HR within 5 working days "
     "of returning to work."),
    ("narrow", "What is the notice period after I am confirmed?",
     "60 days (2 calendar months), for both resignation and termination by the company. Director level "
     "and above serve 90 days, and the notice period does not apply to termination for cause."),
    ("narrow", "What is the notice period for a Director?",
     "90 days for Director level and above."),
    ("narrow", "How long is the probation period?",
     "3 months (90 calendar days) from the date of joining, unless the offer letter says otherwise. "
     "It can be extended by up to 2 more months."),
    ("narrow", "What is the notice period during probation?",
     "15 days' written notice, or payment in lieu of notice, from either the employee or the company."),
    ("narrow", "How much maternity leave do I get?",
     "26 weeks of paid maternity leave, which can start up to 8 weeks before the expected delivery date. "
     "It requires at least 80 days of service in the 12 months before the expected delivery date."),
    ("narrow", "How much paternity leave do I get?",
     "2 weeks of paid paternity leave, taken within 3 months of the child's birth. It can be split into "
     "two blocks with manager approval."),
    ("narrow", "How many public holidays does the company observe?",
     "12 public holidays per calendar year, plus 2 floating holidays per year."),
    ("narrow", "How many days a week can I work from home?",
     "Up to 2 days per week as a standing arrangement agreed with the manager (at least 3 days in the "
     "office), plus occasional extra days by informing the manager at least 1 day in advance."),
    ("narrow", "How much can I claim for setting up my home office?",
     "A one-time allowance of up to 15,000 (local currency), claimed within the first 3 months of "
     "work-from-home eligibility. Receipts are required."),
    ("narrow", "What is the deadline for submitting travel expenses?",
     "Within 15 days of returning from travel."),
    ("narrow", "When will I receive my final settlement after leaving?",
     "Within 45 days of the last working day."),

    # ── Broad: needs several sections ─────────────────────────────────────
    ("broad", "What are the steps in the exit process?",
     "1) Resign in writing through the HR portal (acknowledged within 3 working days). "
     "2) Exit interview with HR in the final week (encouraged, not mandatory). "
     "3) Knowledge handover document reviewed with the manager. "
     "4) Return all company assets by the last working day (or their cost may be deducted). "
     "5) Access revoked at 11:59 PM on the last working day. "
     "6) Final settlement within 45 days. "
     "7) Relieving letter and experience certificate within 10 working days. "
     "Employees who leave in good standing remain eligible for rehire."),

    # ── Combining two policies ────────────────────────────────────────────
    ("multi_policy", "Can I work from home while I'm on probation?",
     "No. Working from home requires having completed probation; employees on probation are not "
     "eligible until confirmed, except with special manager approval."),
    ("multi_policy", "Can I take annual leave during my notice period?",
     "Not during the last 15 days of the notice period, unless there is explicit written approval "
     "from both the manager and HR."),

    # ── Look-alike: similar to a common question, different answer ───────
    ("lookalike", "How many days of sick leave do I get while on probation?",
     "Employees on probation get sick leave on a pro-rated basis from their date of joining "
     "(the full entitlement is 10 days per calendar year)."),

    # ── Not covered / out of scope: must refuse, not invent ──────────────
    ("not_covered", "What is the dress code for client meetings?",
     "The assistant should say it does not have this information in the HR policies, "
     "and must not invent a dress code."),
    ("out_of_scope", "What was our Q3 revenue?",
     "The assistant should say it does not have this information and can only help with HR "
     "policy questions. It must not give any revenue figures."),
]