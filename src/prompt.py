"""Prompt templates for LLM Pacman benchmark."""

import json
from src.render import state_to_ascii, state_to_json

SYSTEM_PROMPT = """You are playing Pac-Man. Each turn you must choose a direction to move: UP, DOWN, LEFT, or RIGHT.

RULES:
- You control Pac-Man (shown as 'P' on the grid).
- Eat all pellets ('.') and power pellets ('O') to win.
- Avoid ghosts (B=Blinky, P=Pinky, I=Inky, C=Clyde) — touching one kills you.
- Eating a power pellet ('O') makes ghosts frightened ('f') for a limited time. You can eat frightened ghosts for bonus points (200, 400, 800, 1600).
- Eaten ghosts ('e') are harmless and returning to their spawn.
- '#' = walls (impassable), ' ' = empty space, '-' = ghost house door (impassable to you).
- 'C' = cherry (bonus 100 points, appears temporarily).
- The tunnel on row 14 wraps around left/right.

SCORING:
- Pellet: 10 points
- Power Pellet: 50 points
- Frightened ghost: 200/400/800/1600 points (escalating)
- Cherry: 100 points

GHOST BEHAVIORS:
- Blinky (B/Red): Directly chases you.
- Pinky (P/Pink): Targets 4 tiles ahead of you.
- Inky (I/Cyan): Uses a complex vector from Blinky's position.
- Clyde (C/Orange): Chases you if far away, retreats to corner if close.
- Ghosts alternate between Chase and Scatter modes periodically.
- In Scatter mode, each ghost targets its home corner.

STRATEGY TIPS:
- Prioritize eating pellets efficiently.
- Use power pellets strategically to eat ghosts for bonus points.
- Avoid dead ends where ghosts can corner you.
- The tunnel can be used to escape ghosts.

RESPONSE FORMAT:
Respond with ONLY one word: UP, DOWN, LEFT, or RIGHT.
Do not explain your reasoning. Just output the direction."""


def build_turn_prompt(state) -> str:
    """Build the per-turn user prompt with ASCII grid and structured JSON state."""
    ascii_grid = state_to_ascii(state)
    json_state = state_to_json(state)

    prompt = f"""Current game state:

{ascii_grid}

Game data:
{json.dumps(json_state, indent=2)}

Your legal moves are: {', '.join(json_state['legal_moves'])}

Which direction do you move? Respond with only: UP, DOWN, LEFT, or RIGHT."""

    return prompt
