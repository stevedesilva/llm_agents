"""LLM Arena — pits multiple LLM providers against each other on a generated question and ranks them."""

import asyncio
import os

from openai import OpenAI

from display import display
from judge import judge_all
from providers import PROVIDERS, Provider, query_provider, validate_api_keys


def generate_question() -> str:
    """Generate a challenging question using OpenAI to evaluate LLM intelligence."""
    request = (
        "Please come up with a challenging, nuanced question that I can ask "
        "a number of LLMs to evaluate their intelligence. "
        "Answer only with the question, no explanation."
    )
    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": request}],
    )
    return response.choices[0].message.content or ""


def has_api_key(provider: Provider) -> bool:
    """Check whether a provider's API key is available without making an API call."""
    if provider.api_key_value:
        return True
    if not provider.env_var:
        return True
    return bool(os.getenv(provider.env_var))


async def main():
    """Orchestrate the arena: generate a question, query all providers concurrently, and judge."""
    validate_api_keys()

    question = generate_question()
    display(f"## Question\n\n{question}")

    # Filter to providers with available keys
    available = [p for p in PROVIDERS if has_api_key(p)]
    skipped = [p for p in PROVIDERS if not has_api_key(p)]
    for p in skipped:
        display(f"*Skipping {p.name} — API key not set*")

    # Query all available providers concurrently
    display("### Querying all providers concurrently...")

    async def _query_one(provider: Provider) -> tuple[Provider, str | None]:
        try:
            answer = await asyncio.to_thread(query_provider, provider, question)
            return provider, answer
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

    # Judge concurrently
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


if __name__ == "__main__":
    asyncio.run(main())
