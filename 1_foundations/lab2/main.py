"""LLM Arena — pits multiple LLM providers against each other on a generated question and ranks them."""

import asyncio

from dotenv import load_dotenv
from openai import OpenAI

from arena import Provider, display, judge_all, query_provider, validate_api_keys

PROVIDERS: list[Provider] = [
    Provider(
        name="GPT-5-mini",
        model="gpt-5-mini",
        kind="openai",
        env_var="OPENAI_API_KEY",
        prefix_len=8,
        optional=False,
    ),
    Provider(
        name="GPT-5-nano",
        model="gpt-5-nano",
        kind="openai",
        env_var="OPENAI_API_KEY",
        prefix_len=8,
        optional=False,
    ),
    Provider(
        name="Claude Sonnet 4.5",
        model="claude-sonnet-4-5",
        kind="anthropic",
        env_var="ANTHROPIC_API_KEY",
        prefix_len=7,
    ),
    Provider(
        name="Gemini 2.5 Flash",
        model="gemini-2.5-flash",
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
    Provider(
        name="Ollama Llama 3.2",
        model="llama3.2",
        kind="openai",
        env_var="",
        base_url="http://localhost:11434/v1",
        api_key_value="ollama",
    ),
]


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


async def main() -> None:
    """Orchestrate the arena: generate a question, query all providers concurrently, and judge."""
    load_dotenv()
    validate_api_keys()

    question = generate_question()
    display(f"## Question\n\n{question}")

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


if __name__ == "__main__":
    asyncio.run(main())
