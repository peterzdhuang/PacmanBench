# PacmanBench

PacmanBench is a reproducible benchmark that evaluates how well LLMs can play a Pac-Man-style environment under consistent game rules.

It combines a deterministic game engine, provider-agnostic LLM integration, and run-level metrics so model behavior can be compared across providers and prompts.

## Why this project

This project demonstrates practical AI engineering skills:
- Designing a benchmark harness around a constrained decision-making task
- Building a non-trivial simulation engine with deterministic rules
- Integrating multiple LLM providers behind a single interface
- Collecting and aggregating evaluation metrics across repeated runs
- Writing test coverage for gameplay, map logic, serialization, and benchmarking

## Core Features

- Turn-based Pac-Man simulation with:
  - Pellet, power pellet, ghost, and cherry scoring
  - Tunnel wrapping behavior
  - Ghost house one-way door rules
  - Scatter/chase global ghost mode cycles
  - Frightened/eaten ghost state transitions
- Ghost personalities:
  - Blinky: direct chase
  - Pinky: targets tiles ahead of Pac-Man
  - Inky: vector-based targeting using Blinky + Pac-Man
  - Clyde: chase/retreat behavior based on distance
- LLM benchmark runner:
  - OpenAI, Anthropic, and Ollama support
  - Configurable run count and tick budget
  - Optional live ASCII rendering
  - Invalid move and API error tracking
- Reporting:
  - Per-run metrics
  - Aggregate win rate, score, survival ticks, completion, and error stats
  - JSON export for analysis pipelines

## Tech Stack

- Python 3
- APIs: OpenAI, Anthropic, Ollama (HTTP)
- Testing: Pytest

## Project Structure

```text
src/
  main.py           # CLI entrypoint (demo + benchmark commands)
  benchmark.py      # Benchmark orchestration loop
  engine.py         # Game loop, scoring, collisions, timers
  entities.py       # Pac-Man and ghost targeting logic
  map.py            # Map layout, walls, tunnel, one-way door
  render.py         # ASCII + JSON state serialization
  prompt.py         # System prompt + per-turn prompt builder
  llm_provider.py   # Provider abstraction + API adapters
  metrics.py        # Run and aggregate benchmark metrics
  constants.py      # Enums + scoring/timing constants

tests/
  test_engine.py
  test_map.py
  test_ghosts.py
  test_serialization.py
  test_benchmark.py
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

Set API credentials only for providers you use:

```bash
# OpenAI
export OPENAI_API_KEY="..."

# Anthropic
export ANTHROPIC_API_KEY="..."
```

For Ollama, make sure the local server is running (default `http://localhost:11434`).

## Usage

### Run demo mode

```bash
python -m src.main demo
```

### Run benchmark mode

```bash
python -m src.main benchmark --provider openai --model gpt-4o --runs 5 --max-ticks 1000
```

Optional flags:
- `--render`: live ASCII board rendering
- `--verbose`: print provider errors and invalid responses
- `--output results.json`: save full report

Example with output file:

```bash
python -m src.main benchmark \
  --provider anthropic \
  --model claude-sonnet-4-20250514 \
  --runs 10 \
  --max-ticks 1200 \
  --output benchmark_results.json
```

## Metrics Captured

Each run records:
- Final score
- Ticks survived
- Pellets collected and completion percentage
- Win/loss
- Invalid move count (when model output cannot be parsed)
- Provider/API errors

Aggregated report includes:
- Win rate
- Mean/median/min/max for score, ticks survived, completion
- Total invalid moves and total API errors

## Prompting + Decision Interface

The benchmark sends each model:
- A strict system instruction to respond with one direction: `UP`, `DOWN`, `LEFT`, or `RIGHT`
- A per-turn prompt containing:
  - ASCII game board
  - Structured JSON state
  - Legal move list

Model responses are parsed robustly, with fallback to `NONE` on invalid output.

## Testing

Run tests with:

```bash
pytest -q
```

Test suite covers:
- Engine behavior (scoring, collisions, win condition, timers)
- Map rules (tunnel wrapping, one-way ghost door, pellet counting)
- Ghost targeting logic
- Serialization correctness (ASCII/JSON)
- Benchmark and metrics behavior with a mock provider

## Engineering Notes

- The environment is deterministic for fixed move sequences, which improves benchmark reproducibility.
- The provider abstraction (`LLMProvider`) makes it straightforward to add additional model backends.
- Metrics are intentionally simple and interpretable for quick model-to-model comparison.

## Resume Summary (Suggested)

Built a Python benchmark framework that evaluates LLM decision quality in a Pac-Man simulation, implementing game-engine mechanics, multi-provider model integration (OpenAI/Anthropic/Ollama), and metrics aggregation across repeated runs to compare win rate, score, survival, and action validity.
