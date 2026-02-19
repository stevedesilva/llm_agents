"""Tests for arena.judge — extract_json, parse_ranking, average_rankings."""

import pytest

from arena.judge import average_rankings, extract_json, parse_ranking


# ---------------------------------------------------------------------------
# extract_json
# ---------------------------------------------------------------------------


class TestExtractJson:
    def test_raw_json(self):
        assert extract_json('{"results": [1, 2]}') == '{"results": [1, 2]}'

    def test_with_markdown_fences(self):
        text = '```json\n{"results": [2, 1]}\n```'
        assert extract_json(text) == '{"results": [2, 1]}'

    def test_with_surrounding_prose(self):
        text = 'Here is my ranking:\n{"results": [3, 1, 2]}\nHope that helps!'
        result = extract_json(text)
        assert result == '{"results": [3, 1, 2]}'

    def test_whitespace_stripped(self):
        assert extract_json("  \n  {\"a\": 1}  \n  ") == '{"a": 1}'

    def test_no_json_returns_stripped(self):
        assert extract_json("  no json here  ") == "no json here"


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
        # Both average to 1.5
        assert all(avg == 1.5 for avg, _ in result)

    def test_missing_competitor_gets_inf(self):
        rankings = [[(1, "Alice")]]  # Bob not ranked
        result = average_rankings(rankings, ["Alice", "Bob"])
        assert result[0] == (1.0, "Alice")
        assert result[1][0] == float("inf")
        assert result[1][1] == "Bob"

    def test_empty_rankings(self):
        result = average_rankings([], ["Alice", "Bob"])
        assert all(avg == float("inf") for avg, _ in result)
