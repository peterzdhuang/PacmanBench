"""PacmanBench CLI — run LLM benchmarks or demo games."""

import argparse
import os
import sys
import time

from src.engine import GameEngine
from src.constants import Direction
from src.render import state_to_ascii


def run_demo():
    """Run a demo game with hard-coded directions for testing."""
    engine = GameEngine()

    directions = [Direction.RIGHT] * 5 + [Direction.UP] * 5 + [Direction.LEFT] * 10

    for i in range(100):
        move = Direction.NONE
        if i < len(directions):
            move = directions[i]

        engine.step(move)
        os.system('clear' if os.name == 'posix' else 'cls')
        print(state_to_ascii(engine.state))

        if engine.state.game_over:
            if engine.state.won:
                print("YOU WIN!")
            else:
                print("GAME OVER")
            break
        time.sleep(0.1)


def run_benchmark(args):
    """Run the LLM benchmark."""
    from src.llm_provider import create_provider
    from src.benchmark import BenchmarkRunner, BenchmarkConfig

    provider = create_provider(args.provider, args.model)
    config = BenchmarkConfig(
        provider_name=args.provider,
        model=args.model,
        num_runs=args.runs,
        max_ticks=args.max_ticks,
        render=args.render,
        verbose=args.verbose,
    )

    runner = BenchmarkRunner(provider, config)
    report = runner.run()
    report.print_summary()

    if args.output:
        with open(args.output, 'w') as f:
            f.write(report.to_json())
        print(f"Results saved to {args.output}")


def main():
    parser = argparse.ArgumentParser(
        description="PacmanBench — Benchmark LLMs by playing Pac-Man"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Demo command
    subparsers.add_parser("demo", help="Run a demo game with pre-programmed directions")

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run the LLM benchmark")
    bench_parser.add_argument(
        "--provider", required=True, choices=["openai", "anthropic", "ollama"],
        help="LLM provider to use"
    )
    bench_parser.add_argument(
        "--model", required=True,
        help="Model name (e.g., gpt-4o, claude-sonnet-4-20250514, llama3)"
    )
    bench_parser.add_argument(
        "--runs", type=int, default=5,
        help="Number of games to run (default: 5)"
    )
    bench_parser.add_argument(
        "--max-ticks", type=int, default=1000,
        help="Maximum ticks per game (default: 1000)"
    )
    bench_parser.add_argument(
        "--output", type=str, default=None,
        help="Path to save results JSON"
    )
    bench_parser.add_argument(
        "--render", action="store_true",
        help="Show live ASCII rendering during games"
    )
    bench_parser.add_argument(
        "--verbose", action="store_true",
        help="Print LLM errors and invalid moves"
    )

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "benchmark":
        run_benchmark(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
