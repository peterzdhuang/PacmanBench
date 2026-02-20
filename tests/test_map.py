"""Tests for map: wall detection, tunnel wrapping, one-way door, pellet counting."""

import pytest
from src.map import Map
from src.constants import Tile, Direction


class TestMapBasics:
    def test_map_dimensions(self):
        m = Map()
        assert m.width == 28
        assert m.height == 31

    def test_corners_are_walls(self):
        m = Map()
        assert m.get_tile(0, 0) == Tile.WALL
        assert m.get_tile(27, 0) == Tile.WALL
        assert m.get_tile(0, 30) == Tile.WALL
        assert m.get_tile(27, 30) == Tile.WALL

    def test_out_of_bounds_returns_wall(self):
        m = Map()
        assert m.get_tile(-1, 0) == Tile.WALL
        assert m.get_tile(28, 0) == Tile.WALL
        assert m.get_tile(0, -1) == Tile.WALL
        assert m.get_tile(0, 31) == Tile.WALL


class TestTunnel:
    def test_tunnel_row_wrapping(self):
        m = Map()
        # Row 14 is the tunnel row, x < 0 and x >= width should not be walls
        assert m.is_wall(-1, 14) is False
        assert m.is_wall(28, 14) is False

    def test_non_tunnel_row_no_wrapping(self):
        m = Map()
        assert m.is_wall(-1, 10) is True


class TestOneWayDoor:
    def test_pacman_blocked_by_door(self):
        m = Map()
        # Find the one-way wall tiles (row 12, the ghost house door)
        # From map: "WWWWWW.WW WWW--WWW WW.WWWWWW" — row 12
        # The '-' chars are at positions 13 and 14 on row 12
        assert m.get_tile(13, 12) == Tile.ONE_WAY_WALL
        assert m.is_wall(13, 12, entity_type='pacman') is True

    def test_ghost_can_exit_up_through_door(self):
        m = Map()
        assert m.is_wall(13, 12, entity_type='ghost', moving_direction=Direction.UP) is False

    def test_ghost_cannot_enter_down_through_door(self):
        m = Map()
        assert m.is_wall(13, 12, entity_type='ghost', moving_direction=Direction.DOWN) is True

    def test_eaten_ghost_can_pass_through_door(self):
        m = Map()
        assert m.is_wall(13, 12, entity_type='eaten_ghost') is False


class TestPelletCounting:
    def test_initial_pellet_count(self):
        m = Map()
        count = m.count_pellets()
        # The classic map should have > 200 pellets
        assert count > 200

    def test_pellet_count_decreases(self):
        m = Map()
        initial = m.count_pellets()
        # Find and remove a pellet
        for y in range(m.height):
            for x in range(m.width):
                if m.get_tile(x, y) == Tile.PELLET:
                    m.set_tile(x, y, Tile.EMPTY)
                    assert m.count_pellets() == initial - 1
                    return
