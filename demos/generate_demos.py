"""Generate demo benchmark runs for PacmanBench showcase.

Simulates three LLM players (Claude, ChatGPT, Grok) with different
skill levels, recording every frame for GIF generation.

Usage:
    python demos/generate_demos.py

Output:
    demos/demo_runs.json — Frame-by-frame game recordings
"""

import json
import random
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.engine import GameEngine
from src.constants import Direction, Tile, GhostState
from src.render import state_to_ascii, state_to_json


def _ghost_info(state):
    """Return list of dicts with each ghost's name, position index, and state."""
    return [
        {"name": g.name, "x": g.x, "y": g.y, "state": g.state.name}
        for g in state.ghosts
    ]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def get_valid_moves(state):
    """Return list of non-wall directions for Pac-Man."""
    moves = []
    for d in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
        nx = state.pacman.x + d.value[0]
        ny = state.pacman.y + d.value[1]
        if ny == 14:
            if nx < 0: nx = state.map.width - 1
            elif nx >= state.map.width: nx = 0
        if not state.map.is_wall(nx, ny, entity_type='pacman'):
            moves.append(d)
    return moves


def nearest_ghost_dist(state, x, y):
    """Manhattan distance to nearest active (non-eaten, non-frightened) ghost."""
    min_d = float('inf')
    for g in state.ghosts:
        if g.state not in (GhostState.EATEN, GhostState.FRIGHTENED):
            min_d = min(min_d, abs(g.x - x) + abs(g.y - y))
    return min_d


def nearest_frightened_dist(state, x, y):
    """Manhattan distance to nearest frightened ghost."""
    min_d = float('inf')
    for g in state.ghosts:
        if g.state == GhostState.FRIGHTENED:
            min_d = min(min_d, abs(g.x - x) + abs(g.y - y))
    return min_d


def tile_after_move(state, d):
    """Return (nx, ny, tile) after moving Pac-Man in direction d."""
    nx = state.pacman.x + d.value[0]
    ny = state.pacman.y + d.value[1]
    if ny == 14:
        if nx < 0: nx = state.map.width - 1
        elif nx >= state.map.width: nx = 0
    return nx, ny, state.map.get_tile(nx, ny)


# ---------------------------------------------------------------------------
# AI strategies (simulated LLM "personalities")
# ---------------------------------------------------------------------------

def claude_ai(state, rng):
    """Smart AI: 2-step lookahead, strong ghost avoidance, ghost hunting when powered."""
    moves = get_valid_moves(state)
    if not moves:
        return Direction.NONE

    px, py = state.pacman.x, state.pacman.y
    powered = state.pacman.is_powered_up
    scored = []

    for d in moves:
        nx, ny, tile = tile_after_move(state, d)
        score = 0.0

        # Pellet scoring
        if tile == Tile.PELLET:
            score += 10
        elif tile == Tile.POWER_PELLET:
            score += 20
        elif tile == Tile.CHERRY:
            score += 25

        # 2-step lookahead: check what's reachable from (nx, ny)
        for d2 in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
            nx2 = nx + d2.value[0]
            ny2 = ny + d2.value[1]
            if ny2 == 14:
                if nx2 < 0: nx2 = state.map.width - 1
                elif nx2 >= state.map.width: nx2 = 0
            if not state.map.is_wall(nx2, ny2, entity_type='pacman'):
                t2 = state.map.get_tile(nx2, ny2)
                if t2 == Tile.PELLET:
                    score += 3
                elif t2 == Tile.POWER_PELLET:
                    score += 5

        if powered:
            # Chase frightened ghosts for bonus points
            fright_dist = nearest_frightened_dist(state, nx, ny)
            if fright_dist < 6:
                score += max(0, 30 - fright_dist * 5)
        else:
            # Avoid active ghosts aggressively
            gdist = nearest_ghost_dist(state, nx, ny)
            if gdist <= 1:
                score -= 100
            elif gdist <= 2:
                score -= 40
            elif gdist <= 3:
                score -= 15
            elif gdist <= 5:
                score -= 5

        # Slight preference for continuing current direction (less zigzag)
        if d == state.pacman.direction:
            score += 1.5

        # Tiny randomness for variety
        score += rng.random() * 0.5

        scored.append((score, d))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def chatgpt_ai(state, rng):
    """Decent AI: 1-step pellet awareness, moderate ghost avoidance, tendency to stay on path."""
    moves = get_valid_moves(state)
    if not moves:
        return Direction.NONE

    px, py = state.pacman.x, state.pacman.y
    scored = []

    for d in moves:
        nx, ny, tile = tile_after_move(state, d)
        score = 0.0

        # Pellet scoring
        if tile == Tile.PELLET:
            score += 8
        elif tile == Tile.POWER_PELLET:
            score += 12
        elif tile == Tile.CHERRY:
            score += 10

        # Moderate ghost avoidance (misses ghosts at distance 3+)
        gdist = nearest_ghost_dist(state, nx, ny)
        if gdist <= 1:
            score -= 50
        elif gdist <= 2:
            score -= 15

        # Stronger continuation bias — sometimes gets stuck in corridors
        if d == state.pacman.direction:
            score += 4

        # More randomness than Claude
        score += rng.random() * 3

        scored.append((score, d))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


def grok_ai(state, rng):
    """Weak AI: mostly random, slight pellet preference, minimal ghost avoidance."""
    moves = get_valid_moves(state)
    if not moves:
        return Direction.NONE

    # 35% chance of pure random move
    if rng.random() < 0.35:
        return rng.choice(moves)

    scored = []
    for d in moves:
        nx, ny, tile = tile_after_move(state, d)
        score = 0.0

        if tile == Tile.PELLET:
            score += 5

        # Barely aware of ghosts
        gdist = nearest_ghost_dist(state, nx, ny)
        if gdist <= 1:
            score -= 20

        # Heavy randomness dominates
        score += rng.random() * 12

        scored.append((score, d))

    scored.sort(key=lambda x: -x[0])
    return scored[0][1]


# ---------------------------------------------------------------------------
# Game runner with frame recording
# ---------------------------------------------------------------------------

def run_game(ai_func, max_ticks, seed):
    """Run a game with the given AI, recording every frame.

    Returns (frames_list, final_game_state).
    """
    rng = random.Random(seed)
    random.seed(seed)  # Seed global random for engine's frightened-ghost logic

    engine = GameEngine()
    state = engine.state
    frames = []

    # Record initial frame (tick 0)
    frames.append({
        "tick": 0,
        "move": "NONE",
        "score": state.score,
        "pacman": {"x": state.pacman.x, "y": state.pacman.y},
        "ghosts": _ghost_info(state),
        "ascii_map": state_to_ascii(state),
    })

    for _ in range(max_ticks):
        if state.game_over:
            break

        direction = ai_func(state, rng)
        engine.step(direction)

        frames.append({
            "tick": state.ticks,
            "move": direction.name,
            "score": state.score,
            "pacman": {"x": state.pacman.x, "y": state.pacman.y},
            "ghosts": _ghost_info(state),
            "ascii_map": state_to_ascii(state),
        })

    return frames, state


# ---------------------------------------------------------------------------
# Main: generate all demo runs
# ---------------------------------------------------------------------------

def main():
    configs = [
        {
            "provider": "Anthropic",
            "model": "claude-sonnet-4-20250514",
            "ai": claude_ai,
            "max_ticks": 350,
            "seed": 42,
        },
        {
            "provider": "OpenAI",
            "model": "gpt-4o",
            "ai": chatgpt_ai,
            "max_ticks": 250,
            "seed": 99,
        },
        {
            "provider": "xAI",
            "model": "grok-2",
            "ai": grok_ai,
            "max_ticks": 180,
            "seed": 777,
        },
    ]

    all_runs = []

    for cfg in configs:
        label = f"{cfg['provider']}/{cfg['model']}"
        print(f"Running {label} (max {cfg['max_ticks']} ticks, seed={cfg['seed']})...")

        frames, final = run_game(cfg["ai"], cfg["max_ticks"], cfg["seed"])

        total = final.total_pellets
        remaining = final.pellets_remaining
        collected = total - remaining
        pct = round(collected / total * 100, 2) if total > 0 else 0.0

        run = {
            "provider": cfg["provider"],
            "model": cfg["model"],
            "seed": cfg["seed"],
            "summary": {
                "total_ticks": final.ticks,
                "final_score": final.score,
                "pellets_collected": collected,
                "total_pellets": total,
                "completion_pct": pct,
                "won": final.won,
                "died": final.game_over and not final.won,
            },
            "frames": frames,
        }

        s = run["summary"]
        status = "WON!" if s["won"] else ("DIED" if s["died"] else "SURVIVED")
        print(f"  {status} | Ticks: {s['total_ticks']} | Score: {s['final_score']} | "
              f"Pellets: {collected}/{total} ({pct}%)")

        all_runs.append(run)

    # Sort by score descending for the report
    all_runs_sorted = sorted(all_runs, key=lambda r: r["summary"]["final_score"], reverse=True)
    print(f"\n{'='*60}")
    print("  LEADERBOARD")
    print(f"{'='*60}")
    for i, r in enumerate(all_runs_sorted, 1):
        s = r["summary"]
        print(f"  #{i} {r['provider']}/{r['model']}: "
              f"Score={s['final_score']}, Pellets={s['completion_pct']}%, "
              f"Ticks={s['total_ticks']}")
    print(f"{'='*60}")

    output = {"runs": all_runs}
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_runs.json")
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    size_kb = os.path.getsize(output_path) / 1024
    print(f"\nSaved to {output_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
