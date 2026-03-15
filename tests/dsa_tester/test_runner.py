"""Unit tests for runner.py"""
from desilvaware.dsa_tester.runner import run_python, run_code


def test_run_python_pass():
    code = "def solution(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i]+nums[j]==target: return [i,j]"
    test_cases = [
        {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
        {"input": {"nums": [3, 2, 4], "target": 6}, "expected": [1, 2]},
    ]
    results = run_python(code, test_cases)
    assert len(results) == 2
    assert all(r.passed for r in results)


def test_run_python_fail():
    code = "def solution(nums, target):\n    return []"
    test_cases = [
        {"input": {"nums": [2, 7, 11, 15], "target": 9}, "expected": [0, 1]},
    ]
    results = run_python(code, test_cases)
    assert len(results) == 1
    assert not results[0].passed
    assert results[0].error is not None


def test_run_python_exception():
    code = "def solution(nums, target):\n    raise ValueError('oops')"
    test_cases = [{"input": {"nums": [1, 2], "target": 3}, "expected": [0, 1]}]
    results = run_python(code, test_cases)
    assert not results[0].passed
    assert "oops" in (results[0].error or "")


def test_run_python_timeout():
    code = "def solution(nums, target):\n    while True: pass"
    test_cases = [{"input": {"nums": [1], "target": 1}, "expected": [0]}]
    results = run_python(code, test_cases, time_limit=1)
    assert not results[0].passed
    assert "Time limit" in (results[0].error or "")


def test_run_code_unsupported_language():
    results = run_code("java", "public int[] solution() {}", [{"input": {}, "expected": []}])
    assert len(results) == 1
    assert not results[0].passed
    assert "not yet supported" in (results[0].error or "")
