"""Tests for game state serialization: ASCII rendering and JSON export."""

import json
import pytest
from src.engine import GameEngine
from src.render import state_to_ascii, state_to_json, get_legal_moves
from src.constants import Direction, GhostState


class TestAsciiRendering:
    def test_ascii_contains_pacman(self):
        engine = GameEngine()
        ascii_str = state_to_ascii(engine.state)
        assert 'P' in ascii_str

    def test_ascii_contains_ghosts(self):
        engine = GameEngine()
        ascii_str = state_to_ascii(engine.state)
        # Blinky starts outside ghost house
        assert 'B' in ascii_str

    def test_ascii_contains_walls(self):
        engine = GameEngine()
        ascii_str = state_to_ascii(engine.state)
        assert '#' in ascii_str

    def test_ascii_contains_pellets(self):
        engine = GameEngine()
        ascii_str = state_to_ascii(engine.state)
        assert '.' in ascii_str

    def test_ascii_contains_score_header(self):
        engine = GameEngine()
        ascii_str = state_to_ascii(engine.state)
        assert 'Score:' in ascii_str
        assert 'Ticks:' in ascii_str
        assert 'Pellets:' in ascii_str

    def test_frightened_ghost_shows_f(self):
        engine = GameEngine()
        state = engine.state
        ghost = state.ghosts[0]
        ghost.state = GhostState.FRIGHTENED
        ascii_str = state_to_ascii(state)
        assert 'f' in ascii_str

    def test_eaten_ghost_shows_e(self):
        engine = GameEngine()
        state = engine.state
        ghost = state.ghosts[0]
        ghost.state = GhostState.EATEN
        ascii_str = state_to_ascii(state)
        assert 'e' in ascii_str


class TestJsonSerialization:
    def test_json_has_required_keys(self):
        engine = GameEngine()
        data = state_to_json(engine.state)
        assert 'pacman' in data
        assert 'ghosts' in data
        assert 'score' in data
        assert 'ticks' in data
        assert 'pellets_remaining' in data
        assert 'total_pellets' in data
        assert 'legal_moves' in data
        assert 'cherry' in data
        assert 'game_over' in data
        assert 'won' in data

    def test_pacman_data(self):
        engine = GameEngine()
        data = state_to_json(engine.state)
        pac = data['pacman']
        assert 'x' in pac
        assert 'y' in pac
        assert 'direction' in pac
        assert 'is_powered_up' in pac

    def test_ghosts_data(self):
        engine = GameEngine()
        data = state_to_json(engine.state)
        assert len(data['ghosts']) == 4
        ghost = data['ghosts'][0]
        assert 'name' in ghost
        assert 'x' in ghost
        assert 'y' in ghost
        assert 'state' in ghost

    def test_legal_moves_are_valid(self):
        engine = GameEngine()
        data = state_to_json(engine.state)
        valid_dirs = {'UP', 'DOWN', 'LEFT', 'RIGHT'}
        for move in data['legal_moves']:
            assert move in valid_dirs

    def test_json_is_serializable(self):
        engine = GameEngine()
        data = state_to_json(engine.state)
        # Should not raise
        json_str = json.dumps(data)
        assert isinstance(json_str, str)

    def test_cherry_null_when_inactive(self):
        engine = GameEngine()
        data = state_to_json(engine.state)
        assert data['cherry'] is None


class TestLegalMoves:
    def test_legal_moves_exist_at_start(self):
        engine = GameEngine()
        moves = get_legal_moves(engine.state)
        assert len(moves) > 0

    def test_legal_moves_are_directions(self):
        engine = GameEngine()
        moves = get_legal_moves(engine.state)
        for m in moves:
            assert isinstance(m, Direction)
