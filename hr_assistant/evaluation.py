"""evaluation — grade the assistant's answers with a judge model, in LangSmith.

    For each test question: run the agent -> grade the answer twice:
      correctness  : does it match the reference answer?
      groundedness : is every claim supported by the policy text it retrieved?

Runs the agent directly — no cache (it would hide repeated questions) and no
Model Armor (these are normal questions; attacks are tested separately).
"""

import uuid

from langchain_openai import ChatOpenAI
from langsmith import Client
from openevals.llm import create_llm_as_judge
from openevals.prompts import CORRECTNESS_PROMPT, RAG_GROUNDEDNESS_PROMPT

from hr_assistant import config
from hr_assistant.evaluation_dataset import EXAMPLES
from hr_assistant.pipeline import build_hr_assistant

# ── The judge ─────────────────────────────────────────────────────────────
_judge = ChatOpenAI(
    model=config.JUDGE_MODEL_NAME,
    base_url=config.GROQ_BASE_URL,
    api_key=config.GROQ_API_KEY,
    max_retries=6,  # Groq's free tier can say "slow down" — wait and retry
)
_correctness = create_llm_as_judge(prompt=CORRECTNESS_PROMPT, judge=_judge, feedback_key="correctness")
_groundedness = create_llm_as_judge(prompt=RAG_GROUNDEDNESS_PROMPT, judge=_judge, feedback_key="groundedness")

_agent = None  # built once, on the first question


def _ensure_dataset(client: Client) -> None:
    """Upload the test questions to LangSmith the first time. After that the
    existing dataset is reused (rename EVAL_DATASET_NAME after editing questions)."""
    if client.has_dataset(dataset_name=config.EVAL_DATASET_NAME):
        return
    dataset = client.create_dataset(config.EVAL_DATASET_NAME, description="HR policy Q&A with reference answers")
    client.create_examples(
        dataset_id=dataset.id,
        inputs=[{"question": q} for _, q, _ in EXAMPLES],
        outputs=[{"answer": a} for _, _, a in EXAMPLES],
        metadata=[{"type": t} for t, _, _ in EXAMPLES],
    )


def _run_assistant(inputs: dict) -> dict:
    """The thing being tested: one question in, the answer + the text it retrieved out."""
    global _agent
    if _agent is None:
        _agent, _cache = build_hr_assistant()
    result = _agent.invoke(
        {"messages": [{"role": "user", "content": inputs["question"]}]},
        config={"configurable": {"thread_id": str(uuid.uuid4())}},  # fresh conversation each time
    )
    messages = result["messages"]
    return {
        "answer": messages[-1].text,
        # Exactly the policy text Gemini saw — so groundedness is checked against real evidence.
        "context": "\n\n".join(m.text for m in messages if m.type == "tool"),
    }


_NO_ANSWER = "Not graded — the assistant produced no answer (it crashed; see the error above)."


def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict:
    if "answer" not in outputs:
        return {"key": "correctness", "score": None, "comment": _NO_ANSWER}
    return _correctness(inputs=inputs, outputs={"answer": outputs["answer"]}, reference_outputs=reference_outputs)


_REFUSAL_TYPES = {"not_covered", "out_of_scope"}  # correct answer = a refusal; nothing to ground


def _is_refusal(example) -> bool:
    return (example.metadata or {}).get("type") in _REFUSAL_TYPES


def groundedness(outputs: dict, example) -> dict:
    if "answer" not in outputs:
        return {"key": "groundedness", "score": None, "comment": _NO_ANSWER}
    if _is_refusal(example):
        # A refusal makes no claims about policy, so "is every claim supported?"
        # doesn't apply. Correctness still checks that it refused properly.
        return {"key": "groundedness", "score": None,
                "comment": "Not applicable — the correct answer is a refusal, which makes no claims to ground."}
    return _groundedness(context={"documents": outputs["context"]}, outputs={"answer": outputs["answer"]})


def run_evaluation(experiment_prefix: str = "hr-assistant"):
    """Run every test question, grade it, upload to LangSmith, print a summary."""
    config.check_api_keys()
    client = Client()
    _ensure_dataset(client)

    results = client.evaluate(
        _run_assistant,
        data=config.EVAL_DATASET_NAME,
        evaluators=[correctness, groundedness],
        experiment_prefix=experiment_prefix,
        max_concurrency=1,  # one at a time — gentle on Groq's free-tier limits
        metadata={
            "llm": config.LLM_MODEL_NAME,
            "embeddings": config.EMBEDDING_MODEL_NAME,
            "reranker": config.RERANKER_MODEL_NAME,
            "relevance_threshold": config.RELEVANCE_THRESHOLD,
        },
    )

    # ── Summary in the terminal ───────────────────────────────────────────
    counts = {k: {"PASS": 0, "FAIL": 0, "ERROR": 0, "N/A": 0} for k in ("correctness", "groundedness")}
    for row in results:
        scores = {r.key: r.score for r in row["evaluation_results"]["results"]}
        answered = "answer" in (row["run"].outputs or {})
        marks = []
        for key in counts:
            score = scores.get(key)
            if score is not None:
                mark = "PASS" if score else "FAIL"
            elif key == "groundedness" and answered and _is_refusal(row["example"]):
                mark = "N/A"
            else:
                mark = "ERROR"
            counts[key][mark] += 1
            marks.append(f"{key}: {mark:5}")
        print(f"{'  '.join(marks)}  |  {row['example'].inputs['question']}")
    print()
    for key, c in counts.items():
        graded = c["PASS"] + c["FAIL"]
        notes = []
        if c["N/A"]:
            notes.append(f"{c['N/A']} N/A")
        if c["ERROR"]:
            notes.append(f"{c['ERROR']} not graded — see errors above")
        extra = f"  ({', '.join(notes)})" if notes else ""
        print(f"{key.capitalize():13}: {c['PASS']}/{graded} passed{extra}")
    print(f"Full results in LangSmith: experiment '{results.experiment_name}'")
    return results