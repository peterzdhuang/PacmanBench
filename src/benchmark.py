"""Benchmark runner: orchestrates LLM-driven Pacman games and collects metrics."""

import os
import time
import sys
from dataclasses import dataclass
from typing import Optional

from src.engine import GameEngine
from src.constants import Direction
from src.llm_provider import LLMProvider
from src.prompt import SYSTEM_PROMPT, build_turn_prompt
from src.render import state_to_ascii
from src.metrics import RunMetrics, BenchmarkReport


@dataclass
class BenchmarkConfig:
    """Configuration for a benchmark run."""
    provider_name: str
    model: str
    num_runs: int = 5
    max_ticks: int = 1000
    render: bool = False
    verbose: bool = False


class BenchmarkRunner:
    """Runs multiple Pacman games with an LLM provider and collects metrics."""

    def __init__(self, provider: LLMProvider, config: BenchmarkConfig):
        self.provider = provider
        self.config = config

    def run(self) -> BenchmarkReport:
        """Execute all benchmark runs and return the report."""
        report = BenchmarkReport(
            provider=self.config.provider_name,
            model=self.config.model,
            max_ticks=self.config.max_ticks,
        )

        for run_id in range(1, self.config.num_runs + 1):
            print(f"\n--- Run {run_id}/{self.config.num_runs} ---")
            run_metrics = self._run_single_game(run_id)
            report.add_run(run_metrics)
            print(f"  Score: {run_metrics.final_score} | "
                  f"Ticks: {run_metrics.ticks_survived} | "
                  f"Completion: {run_metrics.completion_pct}% | "
                  f"Won: {run_metrics.won} | "
                  f"Invalid: {run_metrics.invalid_move_count}")

        report.finalize()
        return report

    def _run_single_game(self, run_id: int) -> RunMetrics:
        """Run a single game and return its metrics."""
        engine = GameEngine()
        state = engine.state
        invalid_moves = 0
        errors = []

        while not state.game_over and state.ticks < self.config.max_ticks:
            # Build prompt
            turn_prompt = build_turn_prompt(state)

            # Get LLM move
            direction, raw_response, latency, error = self.provider.get_move(
                SYSTEM_PROMPT, turn_prompt
            )

            if error:
                errors.append(f"Tick {state.ticks}: {error}")
                if self.config.verbose:
                    print(f"  [ERROR] Tick {state.ticks}: {error}")

            if direction == Direction.NONE:
                invalid_moves += 1
                if self.config.verbose:
                    print(f"  [INVALID] Tick {state.ticks}: '{raw_response.strip()[:50]}'")

            # Step the game
            engine.step(direction)

            # Render if requested
            if self.config.render:
                os.system('clear' if os.name == 'posix' else 'cls')
                print(state_to_ascii(state))
                print(f"\nLLM chose: {direction.name} (latency: {latency:.2f}s)")
                sys.stdout.flush()
                time.sleep(0.05)

        return RunMetrics.from_game_state(
            state=state,
            run_id=run_id,
            invalid_moves=invalid_moves,
            errors=errors,
        )
