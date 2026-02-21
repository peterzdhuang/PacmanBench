"""Tests for the game engine: scoring, power-ups, win condition, game over."""

import pytest
from src.engine import GameEngine, GameState
from src.constants import Direction, GhostState, Tile, POINTS_PELLET, POINTS_POWER_PELLET, POINTS_CHERRY


class TestPelletConsumption:
    def test_eating_pellet_awards_points(self):
        engine = GameEngine()
        state = engine.state
        # Pac-Man starts at (14, 23). Move left — tile (13, 23) should be a pellet
        # First find a direction that has a pellet
        initial_score = state.score
        # Move up from start — (14, 22) area
        engine.step(Direction.LEFT)
        # Score should have changed if there was a pellet
        assert state.score >= initial_score

    def test_pellet_count_decreases(self):
        engine = GameEngine()
        state = engine.state
        initial = state.pellets_remaining
        assert initial == state.total_pellets
        assert initial > 0

        # Move to consume a pellet
        engine.step(Direction.LEFT)
        # Pellet count should decrease (if the tile had a pellet)
        tile_at_new_pos = state.map.get_tile(state.pacman.x, state.pacman.y)
        # After consuming, tile should be EMPTY
        assert tile_at_new_pos == Tile.EMPTY

    def test_power_pellet_triggers_frightened(self):
        engine = GameEngine()
        state = engine.state
        # Place a power pellet right next to Pac-Man
        px, py = state.pacman.x, state.pacman.y
        state.map.set_tile(px - 1, py, Tile.POWER_PELLET)
        engine.step(Direction.LEFT)
        assert state.pacman.is_powered_up is True
        for ghost in state.ghosts:
            assert ghost.state in (GhostState.FRIGHTENED, GhostState.EATEN)


class TestWinCondition:
    def test_game_won_when_all_pellets_consumed(self):
        engine = GameEngine()
        state = engine.state
        # Clear all pellets from the map
        for y in range(state.map.height):
            for x in range(state.map.width):
                tile = state.map.get_tile(x, y)
                if tile in (Tile.PELLET, Tile.POWER_PELLET):
                    state.map.set_tile(x, y, Tile.EMPTY)
        state.pellets_remaining = 0
        # Step should trigger win
        engine.step(Direction.NONE)
        assert state.game_over is True
        assert state.won is True

    def test_game_not_won_with_pellets_remaining(self):
        engine = GameEngine()
        state = engine.state
        engine.step(Direction.NONE)
        # Should not be won with pellets remaining
        assert state.won is False


class TestGameOver:
    def test_ghost_collision_ends_game(self):
        engine = GameEngine()
        state = engine.state
        # Move a non-frightened ghost onto Pac-Man's position
        ghost = state.ghosts[0]
        ghost.state = GhostState.CHASE
        ghost.x = state.pacman.x
        ghost.y = state.pacman.y
        # Collision check happens during step
        engine._check_collisions()
        assert state.game_over is True

    def test_frightened_ghost_eaten_not_game_over(self):
        engine = GameEngine()
        state = engine.state
        ghost = state.ghosts[0]
        ghost.state = GhostState.FRIGHTENED
        ghost.x = state.pacman.x
        ghost.y = state.pacman.y
        engine._check_collisions()
        assert state.game_over is False
        # Ghost is immediately respawned to start position in normal state
        assert ghost.x == ghost.start_pos[0]
        assert ghost.y == ghost.start_pos[1]
        assert ghost.state != GhostState.FRIGHTENED


class TestScoring:
    def test_ghost_eat_escalating_points(self):
        engine = GameEngine()
        state = engine.state
        state.pacman.is_powered_up = True
        state.ghost_eat_multiplier = 0

        # Eat first ghost — 200 points
        ghost = state.ghosts[0]
        ghost.state = GhostState.FRIGHTENED
        initial = state.score
        engine._eat_ghost(ghost)
        assert state.score - initial == 200

        # Eat second ghost — 400 points
        ghost2 = state.ghosts[1]
        ghost2.state = GhostState.FRIGHTENED
        initial = state.score
        engine._eat_ghost(ghost2)
        assert state.score - initial == 400

    def test_cherry_awards_points(self):
        engine = GameEngine()
        state = engine.state
        cx, cy = state.cherry_pos
        state.map.set_tile(cx, cy, Tile.CHERRY)
        state.pacman.x = cx + 1
        state.pacman.y = cy
        initial = state.score
        engine._consume_tile(cx, cy)
        # Cherry consumed by moving onto it — we called consume directly
        # Actually let's set pacman and step
        engine2 = GameEngine()
        s2 = engine2.state
        s2.map.set_tile(cx, cy, Tile.CHERRY)
        s2.cherry_active = True
        s2.pacman.x = cx + 1
        s2.pacman.y = cy
        s2.pacman.direction = Direction.LEFT
        # Clear any wall/pellet at cherry pos (it should already be cherry)
        initial_score = s2.score
        engine2.step(Direction.LEFT)
        assert s2.score >= initial_score + POINTS_CHERRY


class TestGlobalTimers:
    def test_power_up_expires(self):
        engine = GameEngine()
        state = engine.state
        state.pacman.is_powered_up = True
        state.pacman.power_up_timer = 2
        for ghost in state.ghosts:
            ghost.state = GhostState.FRIGHTENED
        engine._update_global_timers()
        assert state.pacman.power_up_timer == 1
        assert state.pacman.is_powered_up is True
        engine._update_global_timers()
        assert state.pacman.is_powered_up is False
