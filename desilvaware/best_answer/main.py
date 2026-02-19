"""LLM Arena — pits multiple LLM providers against each other on a user question and ranks them."""

import asyncio
import sys

from dotenv import load_dotenv
from openai import OpenAI

from arena import Provider, display, judge_all, query_provider, validate_api_keys

MAX_CLARIFICATION_ROUNDS = 5

PROVIDERS: list[Provider] = [
    Provider(
        name="GPT-5.2",
        model="gpt-5.2",
        kind="openai",
        env_var="OPENAI_API_KEY",
        prefix_len=8,
        optional=False,
    ),
    Provider(
        name="GPT-5-mini",
        model="gpt-5-mini",
        kind="openai",
        env_var="OPENAI_API_KEY",
        prefix_len=8,
        optional=False,
    ),
    Provider(
        name="Claude Opus 4.6",
        model="claude-opus-4-6",
        kind="anthropic",
        env_var="ANTHROPIC_API_KEY",
        prefix_len=7,
    ),
    Provider(
        name="Gemini 3.0 Flash",
        model="gemini-3.0-flash",
        kind="openai",
        env_var="GOOGLE_API_KEY",
        prefix_len=2,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    ),
    Provider(
        name="DeepSeek Chat",
        model="deepseek-chat",
        kind="openai",
        env_var="DEEPSEEK_API_KEY",
        prefix_len=3,
        base_url="https://api.deepseek.com/v1",
    ),
    Provider(
        name="Groq GPT-OSS-120B",
        model="openai/gpt-oss-120b",
        kind="openai",
        env_var="GROQ_API_KEY",
        prefix_len=4,
        base_url="https://api.groq.com/openai/v1",
    ),
]


def get_user_question() -> str:
    """Prompt the user for a question. Exit if none provided."""
    question = input("\nEnter your question: ").strip()
    if not question:
        print("No question provided. Exiting.")
        sys.exit(0)
    return question


def clarify_question(question: str) -> str:
    """Use GPT-5.2 to iteratively clarify the user's question until it is clear."""
    client = OpenAI()
    current_question = question

    for _ in range(MAX_CLARIFICATION_ROUNDS):
        response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a question analyst. Evaluate if the following question "
                        "is clear and specific enough to get a meaningful answer from an LLM. "
                        "If the question is clear, respond with exactly 'CLEAR'. "
                        "If not, ask 1-2 short clarifying questions to help refine it."
                    ),
                },
                {"role": "user", "content": current_question},
            ],
        )
        reply = (response.choices[0].message.content or "").strip()

        if reply.upper() == "CLEAR":
            return current_question

        display(f"### Clarifying questions\n\n{reply}")
        user_answer = input("\nYour answer: ").strip()
        if not user_answer:
            display("*No answer provided — proceeding with the current question.*")
            return current_question

        refine_response = client.chat.completions.create(
            model="gpt-5.2",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Rewrite the user's original question incorporating their "
                        "clarifying answers into a single, clear, refined question. "
                        "Respond only with the refined question."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Original question: {current_question}\n"
                        f"Clarifying answers: {user_answer}"
                    ),
                },
            ],
        )
        current_question = (refine_response.choices[0].message.content or "").strip()
        display(f"### Refined question\n\n{current_question}")

    return current_question


async def main() -> None:
    """Orchestrate the arena: get a user question, query all providers concurrently, and judge."""
    load_dotenv()
    validate_api_keys()

    question = get_user_question()
    question = clarify_question(question)
    display(f"## Final Question\n\n{question}")

    available = [p for p in PROVIDERS if p.has_api_key()]
    skipped = [p for p in PROVIDERS if not p.has_api_key()]
    for p in skipped:
        display(f"*Skipping {p.name} — API key not set*")

    display("### Querying all providers concurrently...")

    async def _query_one(provider: Provider) -> tuple[Provider, str | None]:
        try:
            answer = await asyncio.wait_for(
                asyncio.to_thread(query_provider, provider, question),
                timeout=30.0,
            )
            return provider, answer
        except asyncio.TimeoutError:
            display(f"**{provider.name} timed out**")
            return provider, None
        except Exception as e:
            display(f"**Error querying {provider.name}:** {e}")
            return provider, None

    results = await asyncio.gather(*[_query_one(p) for p in available])

    competitors: list[str] = []
    answers: list[str] = []
    judges: list[Provider] = []

    for provider, answer in results:
        if answer is None:
            continue
        display(f"## {provider.name}\n\n{answer}")
        competitors.append(provider.name)
        answers.append(answer)
        judges.append(provider)

    if len(competitors) < 2:
        display("**Not enough competitors to judge (need at least 2).**")
        return

    display("## Judging (each model judges all answers concurrently)...")
    per_judge, averaged = await judge_all(question, competitors, answers, judges)

    for judge_name, ranking in per_judge.items():
        if ranking:
            lines = ", ".join(f"{rank}. {name}" for rank, name in ranking)
            display(f"**{judge_name}'s ranking:** {lines}")
        else:
            display(f"**{judge_name}:** *failed to judge*")

    display("## Final Averaged Rankings\n")
    for position, (avg_rank, name) in enumerate(averaged, start=1):
        display(f"**{position}.** {name} (avg rank: {avg_rank:.2f})")

    if averaged:
        _, winner_name = averaged[0]
        winner_idx = competitors.index(winner_name)
        display(f"## Winning Response — {winner_name}\n\n{answers[winner_idx]}")


if __name__ == "__main__":
    asyncio.run(main())
