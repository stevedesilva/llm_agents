from openai import OpenAI

from display import display
from judge import judge_answers
from providers import PROVIDERS, query_provider, validate_api_keys


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


def main():
    validate_api_keys()

    question = generate_question()
    display(f"## Question\n\n{question}")

    competitors: list[str] = []
    answers: list[str] = []

    for provider in PROVIDERS:
        display(f"### Querying {provider.name}...")
        try:
            answer = query_provider(provider, question)
        except Exception as e:
            display(f"**Error querying {provider.name}:** {e}")
            continue

        if answer is None:
            display(f"*Skipping {provider.name} — API key not set*")
            continue

        display(f"## {provider.name}\n\n{answer}")
        competitors.append(provider.name)
        answers.append(answer)

    if len(competitors) < 2:
        display("**Not enough competitors to judge (need at least 2).**")
        return

    display("## Judging...")
    ranked = judge_answers(question, competitors, answers)
    display("## Rankings\n")
    for rank, competitor in ranked:
        display(f"**Rank {rank}:** {competitor}")


if __name__ == "__main__":
    main()
