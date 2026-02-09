import json

from openai import OpenAI


def build_judge_prompt(question: str, competitors: list[str], answers: list[str]) -> str:
    """Construct the judging prompt with all competitor answers."""
    parts = [
        f"You are judging a competition between {len(competitors)} AI models.\n",
        f"The question was: {question}\n",
    ]
    for index, answer in enumerate(answers):
        parts.append(f"# Response from competitor {index + 1}\n\n{answer}\n")

    parts.append(
        "\nPlease rank the responses from best to worst. "
        "Return your answer as JSON in this exact format:\n"
        '{"results": [<competitor numbers from best to worst>]}\n'
        "Return ONLY the JSON, no other text."
    )
    return "\n".join(parts)


def judge_answers(
    question: str,
    competitors: list[str],
    answers: list[str],
    model: str = "gpt-5-mini",
) -> list[tuple[int, str]]:
    """Call the judge model and return ranked results as (rank, competitor_name) tuples."""
    prompt = build_judge_prompt(question, competitors, answers)

    client = OpenAI()
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
    )
    results_text = response.choices[0].message.content or "{}"

    results_dict = json.loads(results_text)
    ranks = results_dict["results"]

    ranked: list[tuple[int, str]] = []
    for rank_index, competitor_number in enumerate(ranks):
        competitor = competitors[int(competitor_number) - 1]
        ranked.append((rank_index + 1, competitor))

    return ranked
