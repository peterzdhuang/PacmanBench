"""Tests for benchmark runner with a mock LLM provider."""

import pytest
from src.engine import GameEngine
from src.constants import Direction
from src.llm_provider import LLMProvider, parse_direction
from src.benchmark import BenchmarkRunner, BenchmarkConfig
from src.metrics import RunMetrics, AggregateMetrics, BenchmarkReport


class MockProvider(LLMProvider):
    """Mock LLM provider that returns a fixed sequence of directions."""

    def __init__(self, directions=None):
        super().__init__(model="mock", temperature=0.0, max_tokens=10)
        self.directions = directions or [Direction.RIGHT] * 100
        self.call_count = 0

    def _call_api(self, system_prompt: str, user_prompt: str) -> str:
        if self.call_count < len(self.directions):
            d = self.directions[self.call_count]
            self.call_count += 1
            return d.name
        return "RIGHT"


class TestParseDirection:
    def test_exact_match(self):
        assert parse_direction("UP") == Direction.UP
        assert parse_direction("DOWN") == Direction.DOWN
        assert parse_direction("LEFT") == Direction.LEFT
        assert parse_direction("RIGHT") == Direction.RIGHT

    def test_case_insensitive(self):
        assert parse_direction("up") == Direction.UP
        assert parse_direction("Down") == Direction.DOWN

    def test_with_whitespace(self):
        assert parse_direction("  UP  ") == Direction.UP

    def test_in_sentence(self):
        assert parse_direction("I think I should go UP") == Direction.UP

    def test_last_direction_wins(self):
        assert parse_direction("I considered LEFT but decided RIGHT") == Direction.RIGHT

    def test_invalid_returns_none(self):
        assert parse_direction("FORWARD") == Direction.NONE
        assert parse_direction("") == Direction.NONE


class TestRunMetrics:
    def test_from_game_state(self):
        engine = GameEngine()
        state = engine.state
        metrics = RunMetrics.from_game_state(state, run_id=1, invalid_moves=0, errors=[])
        assert metrics.run_id == 1
        assert metrics.total_pellets > 0
        assert metrics.pellets_collected == 0
        assert metrics.completion_pct == 0.0
        assert metrics.won is False


class TestAggregateMetrics:
    def test_aggregate_from_runs(self):
        runs = [
            RunMetrics(run_id=1, final_score=100, ticks_survived=50, pellets_collected=10,
                       total_pellets=240, completion_pct=4.17, won=False, invalid_move_count=2),
            RunMetrics(run_id=2, final_score=200, ticks_survived=100, pellets_collected=20,
                       total_pellets=240, completion_pct=8.33, won=False, invalid_move_count=1),
        ]
        agg = AggregateMetrics.from_runs(runs)
        assert agg.num_runs == 2
        assert agg.score_mean == 150.0
        assert agg.score_min == 100
        assert agg.score_max == 200
        assert agg.total_invalid_moves == 3

    def test_empty_runs(self):
        agg = AggregateMetrics.from_runs([])
        assert agg.num_runs == 0


class TestBenchmarkRunner:
    def test_mock_benchmark_runs(self):
        provider = MockProvider()
        config = BenchmarkConfig(
            provider_name="mock",
            model="mock",
            num_runs=1,
            max_ticks=10,  # Very short game
            render=False,
            verbose=False,
        )
        runner = BenchmarkRunner(provider, config)
        report = runner.run()
        assert len(report.runs) == 1
        assert report.runs[0].ticks_survived <= 10

    def test_report_serialization(self):
        report = BenchmarkReport(provider="mock", model="mock", max_ticks=10)
        report.add_run(RunMetrics(run_id=1, final_score=50, ticks_survived=10,
                                   total_pellets=240, completion_pct=0.0))
        report.finalize()
        data = report.to_dict()
        assert data['provider'] == 'mock'
        assert len(data['runs']) == 1
        json_str = report.to_json()
        assert '"mock"' in json_str
