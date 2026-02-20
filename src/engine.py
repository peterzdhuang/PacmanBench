from typing import List, Tuple
from src.constants import Tile, Direction, GhostState, POINTS_PELLET, POINTS_POWER_PELLET, POINTS_GHOST_BASE, POWER_PELLET_DURATION
from src.entities import Pacman, Ghost, Blinky, Pinky, Inky, Clyde
from src.map import Map
import math

from src.constants import (
    Tile, Direction, GhostState, POINTS_PELLET, POINTS_POWER_PELLET, 
    POINTS_GHOST_BASE, POWER_PELLET_DURATION, SCATTER_CHASE_CYCLES,
    CHERRY_SPAWN_TIME, CHERRY_DURATION, POINTS_CHERRY
)
from src.entities import Pacman, Ghost, Blinky, Pinky, Inky, Clyde
from src.map import Map
import math
import random

class GameState:
    def __init__(self):
        self.map = Map()
        self.pacman = Pacman(*self.map.pacman_start)
        self.ghosts: List[Ghost] = [
            Blinky(14, 11),
            Pinky(14, 14),
            Inky(12, 14),
            Clyde(16, 14)
        ]
        self.score = 0
        self.game_over = False
        self.won = False
        self.ticks = 0
        self.ghost_eat_multiplier = 0
        self.cycle_index = 0
        self.cycle_timer = 0
        self.cherry_timer = 0
        self.cherry_active = False
        self.cherry_pos = (14, 17) # Below ghost house
        self.total_pellets = self.map.count_pellets()
        self.pellets_remaining = self.total_pellets

class GameEngine:
    def __init__(self):
        self.state = GameState()
        self.state.cycle_timer = SCATTER_CHASE_CYCLES[0][1]

    def step(self, pacman_direction: Direction):
        if self.state.game_over:
            return

        self.state.ticks += 1
        self._update_global_timers()
        self._move_pacman(pacman_direction)
        self._move_ghosts()
        self._check_collisions()
        self._handle_cherry()
        self._check_win()

    def _check_win(self):
        """Check if all pellets have been consumed."""
        if self.state.pellets_remaining <= 0:
            self.state.game_over = True
            self.state.won = True

    def _update_global_timers(self):
        # Handle power up timer
        if self.state.pacman.is_powered_up:
            self.state.pacman.power_up_timer -= 1
            if self.state.pacman.power_up_timer <= 0:
                self.state.pacman.is_powered_up = False
                self._sync_ghost_states()
        else:
            # Only advance cycle timer if not powered up (standard Pacman rule)
            self.state.cycle_timer -= 1
            if self.state.cycle_timer <= 0:
                self.state.cycle_index += 1
                if self.state.cycle_index < len(SCATTER_CHASE_CYCLES):
                    self.state.cycle_timer = SCATTER_CHASE_CYCLES[self.state.cycle_index][1]
                    self._sync_ghost_states()
                else:
                    # Permanent Chase
                    self.state.cycle_timer = float('inf')
                    for ghost in self.state.ghosts:
                        if ghost.state != GhostState.EATEN:
                            ghost.state = GhostState.CHASE

    def _sync_ghost_states(self):
        if self.state.pacman.is_powered_up:
            return
        
        current_mode = GhostState.CHASE
        if self.state.cycle_index < len(SCATTER_CHASE_CYCLES):
            current_mode = SCATTER_CHASE_CYCLES[self.state.cycle_index][0]
        
        for ghost in self.state.ghosts:
            if ghost.state not in [GhostState.EATEN, GhostState.FRIGHTENED]:
                ghost.state = current_mode

    def _move_pacman(self, direction: Direction):
        if direction == Direction.NONE:
            direction = self.state.pacman.direction

        next_x = self.state.pacman.x + direction.value[0]
        next_y = self.state.pacman.y + direction.value[1]

        # Handle tunnel wrapping
        if next_y == 14:
            if next_x < 0: next_x = self.state.map.width - 1
            elif next_x >= self.state.map.width: next_x = 0

        if not self.state.map.is_wall(next_x, next_y, entity_type='pacman'):
            self.state.pacman.x = next_x
            self.state.pacman.y = next_y
            self.state.pacman.direction = direction
            self._consume_tile(next_x, next_y)

    def _consume_tile(self, x, y):
        tile = self.state.map.get_tile(x, y)
        if tile == Tile.PELLET:
            self.state.score += POINTS_PELLET
            self.state.map.set_tile(x, y, Tile.EMPTY)
            self.state.pellets_remaining -= 1
        elif tile == Tile.POWER_PELLET:
            self.state.score += POINTS_POWER_PELLET
            self.state.map.set_tile(x, y, Tile.EMPTY)
            self.state.pellets_remaining -= 1
            self._trigger_power_up()
        elif tile == Tile.CHERRY:
            self.state.score += POINTS_CHERRY
            self.state.map.set_tile(x, y, Tile.EMPTY)
            self.state.cherry_active = False

    def _trigger_power_up(self):
        self.state.pacman.is_powered_up = True
        self.state.pacman.power_up_timer = POWER_PELLET_DURATION
        self.state.ghost_eat_multiplier = 0
        for ghost in self.state.ghosts:
            if ghost.state != GhostState.EATEN:
                ghost.state = GhostState.FRIGHTENED

    def _move_ghosts(self):
        # Direction priority for tie-breaking: UP, LEFT, DOWN, RIGHT
        direction_priority = [Direction.UP, Direction.LEFT, Direction.DOWN, Direction.RIGHT]

        for ghost in self.state.ghosts:
            # Determine entity type for wall checking
            entity_type = 'eaten_ghost' if ghost.state == GhostState.EATEN else 'ghost'

            # Dead ghosts return to spawn
            if ghost.state == GhostState.EATEN:
                if (ghost.x, ghost.y) == ghost.start_pos:
                    ghost.state = GhostState.CHASE # Will be synced next tick
                    self._sync_ghost_states()
                target = ghost.start_pos
            else:
                target = ghost.get_target(self.state)

            possible_directions = []
            for d in direction_priority:
                if d == ghost.direction.opposite():
                    continue
                
                nx, ny = ghost.x + d.value[0], ghost.y + d.value[1]
                
                # Handle tunnel
                if ny == 14:
                    if nx < 0: nx = self.state.map.width - 1
                    elif nx >= self.state.map.width: nx = 0

                if not self.state.map.is_wall(nx, ny, entity_type=entity_type, moving_direction=d):
                    possible_directions.append(d)
            
            if not possible_directions:
                # If stuck, allow turning back (shouldn't happen in standard map)
                d = ghost.direction.opposite()
                ghost.x += d.value[0]
                ghost.y += d.value[1]
                ghost.direction = d
                continue

            best_dir = possible_directions[0]
            if ghost.state == GhostState.FRIGHTENED:
                best_dir = random.choice(possible_directions)
            else:
                min_dist = float('inf')
                for d in possible_directions:
                    nx, ny = ghost.x + d.value[0], ghost.y + d.value[1]
                    # Handle tunnel for distance calculation
                    if ny == 14:
                        if nx < 0: nx = self.state.map.width - 1
                        elif nx >= self.state.map.width: nx = 0
                    dist = (nx - target[0])**2 + (ny - target[1])**2
                    if dist < min_dist:
                        min_dist = dist
                        best_dir = d
                    # Tie-breaking is handled by iteration order (UP, LEFT, DOWN, RIGHT)
                    # Since we iterate in priority order and use strict <, first direction wins
            
            ghost.x += best_dir.value[0]
            ghost.y += best_dir.value[1]
            
            # Handle tunnel wrapping for ghosts too
            if ghost.y == 14:
                if ghost.x < 0: ghost.x = self.state.map.width - 1
                elif ghost.x >= self.state.map.width: ghost.x = 0
                
            ghost.direction = best_dir

    def _check_collisions(self):
        px, py = self.state.pacman.x, self.state.pacman.y
        for ghost in self.state.ghosts:
            if ghost.x == px and ghost.y == py:
                if ghost.state == GhostState.FRIGHTENED:
                    self._eat_ghost(ghost)
                elif ghost.state != GhostState.EATEN:
                    self.state.game_over = True

    def _eat_ghost(self, ghost):
        self.state.ghost_eat_multiplier += 1
        # 200, 400, 800, 1600
        points = POINTS_GHOST_BASE * (2 ** min(self.state.ghost_eat_multiplier - 1, 3))
        self.state.score += points
        ghost.state = GhostState.EATEN

    def _handle_cherry(self):
        if not self.state.cherry_active:
            if self.state.ticks == CHERRY_SPAWN_TIME:
                self.state.cherry_active = True
                self.state.cherry_timer = CHERRY_DURATION
                self.state.map.set_tile(*self.state.cherry_pos, Tile.CHERRY)
        else:
            self.state.cherry_timer -= 1
            if self.state.cherry_timer <= 0:
                self.state.cherry_active = False
                if self.state.map.get_tile(*self.state.cherry_pos) == Tile.CHERRY:
                    self.state.map.set_tile(*self.state.cherry_pos, Tile.EMPTY)
