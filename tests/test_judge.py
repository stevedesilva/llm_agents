"""Tests for arena.judge — extract_json, parse_ranking, average_rankings, judge_answers, judge_all."""

from unittest.mock import patch

import pytest

from arena.judge import (
    average_rankings,
    build_judge_prompt,
    extract_json,
    judge_all,
    judge_answers,
    parse_ranking,
)
from arena.providers import Provider


# ---------------------------------------------------------------------------
# extract_json
# ---------------------------------------------------------------------------


class TestExtractJson:
    def test_raw_json(self):
        assert extract_json('{"results": [1, 2]}') == '{"results": [1, 2]}'

    def test_with_markdown_fences(self):
        text = '```json\n{"results": [2, 1]}\n```'
        assert extract_json(text) == '{"results": [2, 1]}'

    def test_with_code_fence_no_language(self):
        text = '```\n{"results": [1]}\n```'
        assert extract_json(text) == '{"results": [1]}'

    def test_with_surrounding_prose(self):
        text = 'Here is my ranking:\n{"results": [3, 1, 2]}\nHope that helps!'
        assert extract_json(text) == '{"results": [3, 1, 2]}'

    def test_whitespace_stripped(self):
        assert extract_json("  \n  {\"a\": 1}  \n  ") == '{"a": 1}'

    def test_no_json_returns_stripped(self):
        assert extract_json("  no json here  ") == "no json here"

    def test_nested_braces(self):
        text = '{"results": [1], "meta": {"k": "v"}}'
        result = extract_json(text)
        assert '"results"' in result
        assert '"meta"' in result


# ---------------------------------------------------------------------------
# build_judge_prompt
# ---------------------------------------------------------------------------


class TestBuildJudgePrompt:
    def test_includes_question(self):
        prompt = build_judge_prompt("What is 2+2?", ["A"], ["four"])
        assert "What is 2+2?" in prompt

    def test_includes_all_answers(self):
        prompt = build_judge_prompt("q?", ["A", "B"], ["ans1", "ans2"])
        assert "ans1" in prompt
        assert "ans2" in prompt
        assert 'competitor="1"' in prompt
        assert 'competitor="2"' in prompt

    def test_example_nums_match_count(self):
        prompt = build_judge_prompt("q?", ["A", "B", "C"], ["a", "b", "c"])
        assert "[1, 2, 3]" in prompt

    def test_uses_xml_delimiters(self):
        prompt = build_judge_prompt("q?", ["A"], ["a"])
        assert "<question>" in prompt
        assert "</question>" in prompt
        assert "<response" in prompt
        assert "</response>" in prompt


# ---------------------------------------------------------------------------
# parse_ranking
# ---------------------------------------------------------------------------


class TestParseRanking:
    def test_valid_ranking(self):
        response = '{"results": [2, 1, 3]}'
        competitors = ["Alice", "Bob", "Charlie"]
        result = parse_ranking(response, competitors)
        assert result == [(1, "Bob"), (2, "Alice"), (3, "Charlie")]

    def test_single_competitor(self):
        response = '{"results": [1]}'
        result = parse_ranking(response, ["Only"])
        assert result == [(1, "Only")]

    def test_invalid_json_raises_valueerror(self):
        with pytest.raises(ValueError, match="invalid JSON"):
            parse_ranking("not json at all {{{", ["A"])

    def test_missing_results_key_raises_valueerror(self):
        with pytest.raises(ValueError, match="missing 'results' key"):
            parse_ranking('{"rankings": [1, 2]}', ["A", "B"])

    def test_out_of_range_index_raises_valueerror(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_ranking('{"results": [1, 5]}', ["A", "B"])

    def test_zero_index_raises_valueerror(self):
        with pytest.raises(ValueError, match="out of range"):
            parse_ranking('{"results": [0, 1]}', ["A", "B"])

    def test_non_integer_rank_raises_valueerror(self):
        with pytest.raises(ValueError, match="Non-integer"):
            parse_ranking('{"results": ["first", 2]}', ["A", "B"])

    def test_duplicate_competitor_raises_valueerror(self):
        with pytest.raises(ValueError, match="Duplicate competitor"):
            parse_ranking('{"results": [1, 1]}', ["A", "B"])

    def test_float_values_accepted(self):
        """JSON-decoded floats like 1.0 are accepted via int() coercion."""
        result = parse_ranking('{"results": [1.0, 2.0]}', ["A", "B"])
        assert result == [(1, "A"), (2, "B")]


# ---------------------------------------------------------------------------
# average_rankings
# ---------------------------------------------------------------------------


class TestAverageRankings:
    def test_single_judge(self):
        rankings = [[(1, "Alice"), (2, "Bob")]]
        result = average_rankings(rankings, ["Alice", "Bob"])
        assert result == [(1.0, "Alice"), (2.0, "Bob")]

    def test_multiple_judges_averaged(self):
        rankings = [
            [(1, "Alice"), (2, "Bob")],
            [(2, "Alice"), (1, "Bob")],
        ]
        result = average_rankings(rankings, ["Alice", "Bob"])
        assert all(avg == 1.5 for avg, _ in result)

    def test_missing_competitor_gets_inf(self):
        rankings = [[(1, "Alice")]]
        result = average_rankings(rankings, ["Alice", "Bob"])
        assert result[0] == (1.0, "Alice")
        assert result[1][0] == float("inf")
        assert result[1][1] == "Bob"

    def test_empty_rankings(self):
        result = average_rankings([], ["Alice", "Bob"])
        assert all(avg == float("inf") for avg, _ in result)

    def test_three_judges_clear_winner(self):
        rankings = [
            [(1, "Alice"), (2, "Bob"), (3, "Charlie")],
            [(1, "Alice"), (3, "Bob"), (2, "Charlie")],
            [(1, "Alice"), (2, "Bob"), (3, "Charlie")],
        ]
        result = average_rankings(rankings, ["Alice", "Bob", "Charlie"])
        assert result[0] == (1.0, "Alice")

    def test_result_is_sorted_ascending(self):
        rankings = [
            [(2, "Alice"), (1, "Bob")],
            [(2, "Alice"), (1, "Bob")],
        ]
        result = average_rankings(rankings, ["Alice", "Bob"])
        assert result[0][1] == "Bob"
        assert result[1][1] == "Alice"


# ---------------------------------------------------------------------------
# judge_answers
# ---------------------------------------------------------------------------


class TestJudgeAnswers:
    @patch("arena.judge.query_provider", return_value='{"results": [2, 1]}')
    def test_returns_rankings_on_success(self, _mock_qp):
        p = Provider(name="judge", model="m", kind="openai", env_var="", api_key_value="k")
        result = judge_answers(p, "q?", ["A", "B"], ["ans1", "ans2"])
        assert result == [(1, "B"), (2, "A")]

    @patch("arena.judge.query_provider", return_value=None)
    def test_raises_runtime_error_when_no_key(self, _mock_qp):
        p = Provider(name="judge", model="m", kind="openai", env_var="", api_key_value="k")
        with pytest.raises(RuntimeError, match="No API key for judge"):
            judge_answers(p, "q?", ["A", "B"], ["a", "b"])


# ---------------------------------------------------------------------------
# judge_all (async)
# ---------------------------------------------------------------------------


class TestJudgeAll:
    @pytest.mark.asyncio
    async def test_all_judges_succeed(self):
        p1 = Provider(name="j1", model="m", kind="openai", env_var="", api_key_value="k")
        p2 = Provider(name="j2", model="m", kind="openai", env_var="", api_key_value="k")

        with patch("arena.judge.judge_answers") as mock_ja:
            mock_ja.return_value = [(1, "A"), (2, "B")]
            per_judge, averaged = await judge_all("q?", ["A", "B"], ["a", "b"], [p1, p2])

        assert len(per_judge) == 2
        assert per_judge["j1"] == [(1, "A"), (2, "B")]
        assert len(averaged) == 2

    @pytest.mark.asyncio
    async def test_judge_failure_returns_empty(self):
        p = Provider(name="bad", model="m", kind="openai", env_var="", api_key_value="k")

        with patch("arena.judge.judge_answers", side_effect=ValueError("bad json")):
            per_judge, averaged = await judge_all("q?", ["A", "B"], ["a", "b"], [p])

        assert per_judge["bad"] == []
        assert averaged == []

    @pytest.mark.asyncio
    async def test_mixed_success_failure(self):
        p1 = Provider(name="good", model="m", kind="openai", env_var="", api_key_value="k")
        p2 = Provider(name="bad", model="m", kind="openai", env_var="", api_key_value="k")

        def side_effect(provider, *args):
            if provider.name == "good":
                return [(1, "A"), (2, "B")]
            raise RuntimeError("fail")

        with patch("arena.judge.judge_answers", side_effect=side_effect):
            per_judge, averaged = await judge_all("q?", ["A", "B"], ["a", "b"], [p1, p2])

        assert per_judge["good"] == [(1, "A"), (2, "B")]
        assert per_judge["bad"] == []
        assert averaged[0] == (1.0, "A")
