"""Unit tests for elo.py"""
import pytest
from desilvaware.dsa_tester.elo import (
    composite_score,
    compute_elo_delta,
    question_elo_for_difficulty,
    select_difficulty,
    update_elo,
    DIFFICULTY_BANDS,
)


def test_select_difficulty_easy():
    assert select_difficulty(800) == "easy"
    assert select_difficulty(999) == "easy"


def test_select_difficulty_medium_or_easy():
    results = {select_difficulty(1200) for _ in range(50)}
    assert "medium" in results


def test_select_difficulty_hard_or_medium():
    results = {select_difficulty(1600) for _ in range(50)}
    assert "hard" in results


def test_select_difficulty_expert_or_hard():
    results = {select_difficulty(2000) for _ in range(50)}
    assert "expert" in results


def test_question_elo_in_range():
    for difficulty in ["easy", "medium", "hard", "expert"]:
        lo, hi = DIFFICULTY_BANDS[difficulty]["elo_range"]
        for _ in range(10):
            elo = question_elo_for_difficulty(difficulty)
            assert lo <= elo <= hi


def test_composite_score():
    assert composite_score(1.0, 1.0, 1.0) == pytest.approx(1.0)
    assert composite_score(0.0, 0.0, 0.0) == pytest.approx(0.0)
    # 0.6*0.5 + 0.3*0.5 + 0.1*0.5 = 0.5
    assert composite_score(0.5, 0.5, 0.5) == pytest.approx(0.5)
    # Weights: pass=0.6, explanation=0.3, speed=0.1
    assert composite_score(1.0, 0.0, 0.0) == pytest.approx(0.6)
    assert composite_score(0.0, 1.0, 0.0) == pytest.approx(0.3)
    assert composite_score(0.0, 0.0, 1.0) == pytest.approx(0.1)


def test_elo_delta_win():
    # If user performs better than expected, delta should be positive
    # Equal elos: expected = 0.5, score = 1.0 → positive delta
    delta = compute_elo_delta(1200.0, 1200.0, 1.0, "medium")
    assert delta > 0


def test_elo_delta_loss():
    # If user performs worse than expected, delta should be negative
    delta = compute_elo_delta(1200.0, 1200.0, 0.0, "medium")
    assert delta < 0


def test_update_elo_returns_tuple():
    new_elo, delta = update_elo(1000.0, 1000.0, 0.8, "easy")
    assert isinstance(new_elo, float)
    assert isinstance(delta, float)
    assert new_elo >= 100.0  # floor check


def test_update_elo_floor():
    # Even with score=0, elo should not go below 100
    new_elo, _ = update_elo(100.0, 2000.0, 0.0, "easy")
    assert new_elo >= 100.0
