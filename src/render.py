"""Game state serialization: ASCII grid rendering and JSON state export."""

from src.constants import Tile, Direction, GhostState


def state_to_ascii(state) -> str:
    """Render game state as an ASCII grid string (no terminal clearing).
    
    Legend:
        # = Wall, . = Pellet, O = Power Pellet, C = Cherry
        P = Pac-Man, f = Frightened ghost, e = Eaten ghost
        B/P/I/C = Blinky/Pinky/Inky/Clyde (first letter of name)
    """
    header = (
        f"Score: {state.score} | Ticks: {state.ticks} | "
        f"Pellets: {state.pellets_remaining}/{state.total_pellets} | "
        f"PowerUp: {state.pacman.power_up_timer if state.pacman.is_powered_up else 0}"
    )

    rows = []
    for y in range(state.map.height):
        row = []
        for x in range(state.map.width):
            tile = state.map.get_tile(x, y)
            if tile == Tile.WALL:
                char = '#'
            elif tile == Tile.PELLET:
                char = '.'
            elif tile == Tile.POWER_PELLET:
                char = 'O'
            elif tile == Tile.CHERRY:
                char = 'C'
            elif tile == Tile.ONE_WAY_WALL:
                char = '-'
            else:
                char = ' '

            # Overlay entities
            if (x, y) == (state.pacman.x, state.pacman.y):
                char = 'P'
            else:
                for ghost in state.ghosts:
                    if (x, y) == (ghost.x, ghost.y):
                        if ghost.state == GhostState.FRIGHTENED:
                            char = 'f'
                        elif ghost.state == GhostState.EATEN:
                            char = 'e'
                        else:
                            char = ghost.name[0]
                        break

            row.append(char)
        rows.append("".join(row))

    return header + "\n" + "\n".join(rows)


def get_legal_moves(state) -> list:
    """Return list of legal Direction values Pac-Man can move to (non-wall tiles)."""
    legal = []
    for d in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
        nx = state.pacman.x + d.value[0]
        ny = state.pacman.y + d.value[1]
        # Handle tunnel wrapping
        if ny == 14:
            if nx < 0:
                nx = state.map.width - 1
            elif nx >= state.map.width:
                nx = 0
        if not state.map.is_wall(nx, ny, entity_type='pacman'):
            legal.append(d)
    return legal


def state_to_json(state) -> dict:
    """Serialize game state to a structured dictionary."""
    legal_moves = get_legal_moves(state)

    ghosts_data = []
    for ghost in state.ghosts:
        ghosts_data.append({
            "name": ghost.name,
            "x": ghost.x,
            "y": ghost.y,
            "state": ghost.state.name,
            "direction": ghost.direction.name,
        })

    cherry = None
    if state.cherry_active:
        cherry = {"x": state.cherry_pos[0], "y": state.cherry_pos[1]}

    return {
        "pacman": {
            "x": state.pacman.x,
            "y": state.pacman.y,
            "direction": state.pacman.direction.name,
            "is_powered_up": state.pacman.is_powered_up,
            "power_up_timer": state.pacman.power_up_timer,
        },
        "ghosts": ghosts_data,
        "score": state.score,
        "ticks": state.ticks,
        "pellets_remaining": state.pellets_remaining,
        "total_pellets": state.total_pellets,
        "legal_moves": [d.name for d in legal_moves],
        "cherry": cherry,
        "game_over": state.game_over,
        "won": state.won,
    }
