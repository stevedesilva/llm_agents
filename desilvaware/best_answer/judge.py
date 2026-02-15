"""Judging logic — every competing provider judges all answers, then rankings are averaged."""

import asyncio
import json
import re

from providers import Provider, query_provider


def build_judge_prompt(question: str, competitors: list[str], answers: list[str]) -> str:
    """Construct the judging prompt with all competitor answers."""
    parts = [
        f"You are judging a competition between {len(competitors)} AI models.\n",
        f"The question was: {question}\n",
    ]
    for index, answer in enumerate(answers):
        parts.append(f"# Response from competitor {index + 1}\n\n{answer}\n")

    example_nums = list(range(1, len(competitors) + 1))
    parts.append(
        "\nPlease rank the responses from best to worst. "
        "You MUST respond with ONLY a JSON object, no markdown, no explanation, no code fences.\n"
        f'Exact format: {{"results": {example_nums}}}\n'
        "The array must contain each competitor number exactly once, ordered from best to worst.\n"
        "Your entire response must be valid JSON and nothing else."
    )
    return "\n".join(parts)


def extract_json(text: str) -> str:
    """Extract a JSON object from text that may contain markdown fences or surrounding prose."""
    # Try the raw text first
    stripped = text.strip()
    if stripped.startswith("{"):
        return stripped

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", stripped, re.DOTALL)
    if match:
        return match.group(1)

    # Find the first { ... } substring
    match = re.search(r"\{.*\}", stripped, re.DOTALL)
    if match:
        return match.group(0)

    return stripped


def parse_ranking(
    response_text: str, competitors: list[str]
) -> list[tuple[int, str]]:
    """Parse a judge's JSON response into (rank, competitor_name) tuples."""
    json_str = extract_json(response_text)
    results_dict = json.loads(json_str)
    ranks = results_dict["results"]

    ranked: list[tuple[int, str]] = []
    for rank_index, competitor_number in enumerate(ranks):
        competitor = competitors[int(competitor_number) - 1]
        ranked.append((rank_index + 1, competitor))

    return ranked


def judge_answers(
    provider: Provider,
    question: str,
    competitors: list[str],
    answers: list[str],
) -> list[tuple[int, str]]:
    """Have a single provider judge all answers and return ranked results."""
    prompt = build_judge_prompt(question, competitors, answers)
    response_text = query_provider(provider, prompt)
    if response_text is None:
        raise RuntimeError(f"No API key for judge {provider.name}")
    return parse_ranking(response_text, competitors)


def average_rankings(
    all_rankings: list[list[tuple[int, str]]], competitors: list[str]
) -> list[tuple[float, str]]:
    """Average rank scores across all judges and return sorted (avg_rank, name) tuples."""
    totals: dict[str, float] = {name: 0.0 for name in competitors}
    counts: dict[str, int] = {name: 0 for name in competitors}

    for ranking in all_rankings:
        for rank, name in ranking:
            totals[name] += rank
            counts[name] += 1

    averaged = [
        (totals[name] / counts[name] if counts[name] else float("inf"), name)
        for name in competitors
    ]
    averaged.sort(key=lambda x: x[0])
    return averaged


async def judge_all(
    question: str,
    competitors: list[str],
    answers: list[str],
    judges: list[Provider],
) -> tuple[dict[str, list[tuple[int, str]]], list[tuple[float, str]]]:
    """Have every judge rank the answers concurrently, then average the results.

    Returns (per_judge_rankings, averaged_ranking) where:
      - per_judge_rankings maps judge name -> [(rank, competitor), ...]
      - averaged_ranking is [(avg_rank, competitor), ...] sorted best-first
    """

    async def _judge_one(provider: Provider) -> tuple[str, list[tuple[int, str]]]:
        try:
            ranking = await asyncio.to_thread(
                judge_answers, provider, question, competitors, answers
            )
            return provider.name, ranking
        except Exception as e:
            print(f"Warning: {provider.name} failed to judge: {e}")
            return provider.name, []

    results = await asyncio.gather(*[_judge_one(p) for p in judges])

    per_judge = {name: ranking for name, ranking in results}
    successful = [r for r in per_judge.values() if r]
    averaged = average_rankings(successful, competitors) if successful else []

    return per_judge, averaged
