from enum import Enum

class Tile(Enum):
    EMPTY = 0
    WALL = 1
    PELLET = 2
    POWER_PELLET = 3
    CHERRY = 4
    ONE_WAY_WALL = 5

class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)
    NONE = (0, 0)

    def opposite(self):
        if self == Direction.UP: return Direction.DOWN
        if self == Direction.DOWN: return Direction.UP
        if self == Direction.LEFT: return Direction.RIGHT
        if self == Direction.RIGHT: return Direction.LEFT
        return Direction.NONE

class GhostState(Enum):
    CHASE = 1
    SCATTER = 2
    FRIGHTENED = 3
    EATEN = 4

# Scoring
POINTS_PELLET = 10
POINTS_POWER_PELLET = 50
POINTS_GHOST_BASE = 200
POINTS_CHERRY = 100

# Timing (in ticks)
POWER_PELLET_DURATION = 40
CHERRY_SPAWN_TIME = 200
CHERRY_DURATION = 50

# Global Mode Timers (Scatter, Chase)
# Scatter 7, Chase 20, Scatter 7, Chase 20, Scatter 5, Chase 20, Scatter 5, Chase ...
SCATTER_CHASE_CYCLES = [
    (GhostState.SCATTER, 30),
    (GhostState.CHASE, 100),
    (GhostState.SCATTER, 30),
    (GhostState.CHASE, 100),
    (GhostState.SCATTER, 20),
    (GhostState.CHASE, 100),
    (GhostState.SCATTER, 20),
]
