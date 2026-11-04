"""Test benchmark runner execution."""

from benchmarks.run_all import get_git_commit, run_benchmark


def test_benchmark_runner():
    commit = get_git_commit()
    assert isinstance(commit, str)
    # Execute benchmark runner function
    run_benchmark()
