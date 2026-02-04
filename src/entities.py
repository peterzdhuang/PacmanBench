from dataclasses import dataclass
from typing import Tuple, List
from src.constants import Direction, GhostState, Tile
import math

@dataclass
class Entity:
    x: int
    y: int
    direction: Direction = Direction.NONE

    @property
    def pos(self) -> Tuple[int, int]:
        return (self.x, self.y)

class Pacman(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.lives = 3
        self.score = 0
        self.is_powered_up = False
        self.power_up_timer = 0

class Ghost(Entity):
    def __init__(self, x, y, name, color, scatter_target):
        super().__init__(x, y)
        self.name = name
        self.color = color
        self.state = GhostState.SCATTER
        self.scatter_target = scatter_target
        self.start_pos = (x, y)

    def get_target(self, game_state) -> Tuple[int, int]:
        if self.state == GhostState.FRIGHTENED:
            # Random or specific logic for frightened
            return (self.x, self.y) # Placeholder
        if self.state == GhostState.SCATTER:
            return self.scatter_target
        
        return self._get_chase_target(game_state)

    def _get_chase_target(self, game_state) -> Tuple[int, int]:
        raise NotImplementedError

class Blinky(Ghost):
    def __init__(self, x, y):
        super().__init__(x, y, "Blinky", "Red", (25, -2))

    def _get_chase_target(self, game_state) -> Tuple[int, int]:
        # Targets Pac-Man's current tile directly
        return (game_state.pacman.x, game_state.pacman.y)

class Pinky(Ghost):
    def __init__(self, x, y):
        super().__init__(x, y, "Pinky", "Pink", (2, -2))

    def _get_chase_target(self, game_state) -> Tuple[int, int]:
        # Targets 4 tiles in front of Pac-Man
        px, py = game_state.pacman.x, game_state.pacman.y
        dx, dy = game_state.pacman.direction.value
        return (px + dx * 4, py + dy * 4)

class Inky(Ghost):
    def __init__(self, x, y):
        super().__init__(x, y, "Inky", "Cyan", (27, 32))

    def _get_chase_target(self, game_state) -> Tuple[int, int]:
        # Vector based on Blinky's position and Pac-Man's position
        px, py = game_state.pacman.x, game_state.pacman.y
        dx, dy = game_state.pacman.direction.value
        # Target tile: 2 tiles in front of Pac-Man
        tx, ty = px + dx * 2, py + dy * 2
        
        blinky = next(g for g in game_state.ghosts if isinstance(g, Blinky))
        bx, by = blinky.x, blinky.y
        
        # Double the vector from Blinky to the target tile
        return (tx + (tx - bx), ty + (ty - by))

class Clyde(Ghost):
    def __init__(self, x, y):
        super().__init__(x, y, "Clyde", "Orange", (0, 32))

    def _get_chase_target(self, game_state) -> Tuple[int, int]:
        # Chases if distance > 8, else runs to corner
        dist = math.sqrt((self.x - game_state.pacman.x)**2 + (self.y - game_state.pacman.y)**2)
        if dist > 8:
            return (game_state.pacman.x, game_state.pacman.y)
        return self.scatter_target
