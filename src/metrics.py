"""Benchmark metrics collection and reporting."""

import json
import statistics
from dataclasses import dataclass, field, asdict
from typing import List, Optional


@dataclass
class RunMetrics:
    """Metrics for a single benchmark run (one game)."""
    run_id: int = 0
    final_score: int = 0
    ticks_survived: int = 0
    pellets_collected: int = 0
    total_pellets: int = 0
    completion_pct: float = 0.0
    won: bool = False
    invalid_move_count: int = 0
    errors: List[str] = field(default_factory=list)

    def compute_completion(self):
        if self.total_pellets > 0:
            self.pellets_collected = self.total_pellets - getattr(self, '_pellets_remaining', self.total_pellets)
            self.completion_pct = round(self.pellets_collected / self.total_pellets * 100, 2)

    @classmethod
    def from_game_state(cls, state, run_id: int, invalid_moves: int, errors: List[str]) -> 'RunMetrics':
        total = state.total_pellets
        remaining = state.pellets_remaining
        collected = total - remaining
        pct = round(collected / total * 100, 2) if total > 0 else 0.0
        return cls(
            run_id=run_id,
            final_score=state.score,
            ticks_survived=state.ticks,
            pellets_collected=collected,
            total_pellets=total,
            completion_pct=pct,
            won=state.won,
            invalid_move_count=invalid_moves,
            errors=errors,
        )


@dataclass
class AggregateMetrics:
    """Aggregate metrics across multiple runs."""
    num_runs: int = 0
    wins: int = 0
    win_rate: float = 0.0

    score_mean: float = 0.0
    score_median: float = 0.0
    score_min: int = 0
    score_max: int = 0

    ticks_mean: float = 0.0
    ticks_median: float = 0.0
    ticks_min: int = 0
    ticks_max: int = 0

    completion_mean: float = 0.0
    completion_median: float = 0.0
    completion_min: float = 0.0
    completion_max: float = 0.0

    total_invalid_moves: int = 0
    total_errors: int = 0

    @classmethod
    def from_runs(cls, runs: List[RunMetrics]) -> 'AggregateMetrics':
        if not runs:
            return cls()

        scores = [r.final_score for r in runs]
        ticks = [r.ticks_survived for r in runs]
        completions = [r.completion_pct for r in runs]
        wins = sum(1 for r in runs if r.won)

        return cls(
            num_runs=len(runs),
            wins=wins,
            win_rate=round(wins / len(runs) * 100, 2),
            score_mean=round(statistics.mean(scores), 2),
            score_median=round(statistics.median(scores), 2),
            score_min=min(scores),
            score_max=max(scores),
            ticks_mean=round(statistics.mean(ticks), 2),
            ticks_median=round(statistics.median(ticks), 2),
            ticks_min=min(ticks),
            ticks_max=max(ticks),
            completion_mean=round(statistics.mean(completions), 2),
            completion_median=round(statistics.median(completions), 2),
            completion_min=min(completions),
            completion_max=max(completions),
            total_invalid_moves=sum(r.invalid_move_count for r in runs),
            total_errors=sum(len(r.errors) for r in runs),
        )


class BenchmarkReport:
    """Full benchmark report with per-run and aggregate metrics."""

    def __init__(self, provider: str, model: str, max_ticks: int):
        self.provider = provider
        self.model = model
        self.max_ticks = max_ticks
        self.runs: List[RunMetrics] = []
        self.aggregate: Optional[AggregateMetrics] = None

    def add_run(self, run: RunMetrics):
        self.runs.append(run)

    def finalize(self):
        self.aggregate = AggregateMetrics.from_runs(self.runs)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider,
            "model": self.model,
            "max_ticks": self.max_ticks,
            "aggregate": asdict(self.aggregate) if self.aggregate else None,
            "runs": [asdict(r) for r in self.runs],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def print_summary(self):
        if not self.aggregate:
            self.finalize()
        a = self.aggregate
        print(f"\n{'='*60}")
        print(f"  PacmanBench Results: {self.provider}/{self.model}")
        print(f"{'='*60}")
        print(f"  Runs:           {a.num_runs}")
        print(f"  Max Ticks:      {self.max_ticks}")
        print(f"  Win Rate:       {a.wins}/{a.num_runs} ({a.win_rate}%)")
        print(f"  ---")
        print(f"  Score:          mean={a.score_mean}, median={a.score_median}, min={a.score_min}, max={a.score_max}")
        print(f"  Ticks Survived: mean={a.ticks_mean}, median={a.ticks_median}, min={a.ticks_min}, max={a.ticks_max}")
        print(f"  Completion %:   mean={a.completion_mean}, median={a.completion_median}, min={a.completion_min}, max={a.completion_max}")
        print(f"  Invalid Moves:  {a.total_invalid_moves}")
        print(f"  API Errors:     {a.total_errors}")
        print(f"{'='*60}\n")
