from src.constants import Tile

DEFAULT_MAP = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WPWWWW.WWWWW.WW.WWWWW.WWWWPW",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W..........................W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W.WWWW.WW.WWWWWWWW.WW.WWWW.W",
    "W......WW....WW....WW......W",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "WWWWWW.WWWWW WW WWWWW.WWWWWW",
    "WWWWWW.WW          WW.WWWWWW",
    "WWWWWW.WW WWW--WWW WW.WWWWWW",
    "WWWWWW.WW W      W WW.WWWWWW",
    "      .   W      W   .      ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "WWWWWW.WW          WW.WWWWWW",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "WWWWWW.WW WWWWWWWW WW.WWWWWW",
    "W............WW............W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "W.WWWW.WWWWW.WW.WWWWW.WWWW.W",
    "WP..WW................WW..PW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "WWW.WW.WW.WWWWWWWW.WW.WW.WWW",
    "W......WW....WW....WW......W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W.WWWWWWWWWW.WW.WWWWWWWWWW.W",
    "W..........................W",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

class Map:
    def __init__(self, layout=DEFAULT_MAP):
        self.height = len(layout)
        self.width = len(layout[0])
        self.grid = []
        self.pacman_start = (14, 23)
        self.ghost_spawn = (14, 14)
        
        for y, row in enumerate(layout):
            grid_row = []
            for x, char in enumerate(row):
                if char == 'W':
                    grid_row.append(Tile.WALL)
                elif char == '.':
                    grid_row.append(Tile.PELLET)
                elif char == 'P':
                    grid_row.append(Tile.POWER_PELLET)
                elif char == ' ':
                    grid_row.append(Tile.EMPTY)
                elif char == '-':
                    grid_row.append(Tile.ONE_WAY_WALL)
                else:
                    grid_row.append(Tile.EMPTY)
            self.grid.append(grid_row)

    def get_tile(self, x, y):
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.grid[y][x]
        return Tile.WALL

    def set_tile(self, x, y, tile):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[y][x] = tile

    def is_wall(self, x, y, entity_type='pacman', moving_direction=None):
        """Check if a tile is impassable.
        
        Args:
            x, y: Tile coordinates
            entity_type: 'pacman', 'ghost', or 'eaten_ghost'
            moving_direction: Direction the entity is moving (used for one-way door)
        """
        # Handle wrapping for the tunnel
        if y == 14 and (x < 0 or x >= self.width):
            return False
        tile = self.get_tile(x, y)
        if tile == Tile.WALL:
            return True
        if tile == Tile.ONE_WAY_WALL:
            # One-way door: only ghosts can pass through (exiting upward or eaten returning)
            if entity_type == 'pacman':
                return True
            if entity_type == 'eaten_ghost':
                return False  # Eaten ghosts can pass through to return to spawn
            # Normal ghosts can only exit (move up through the door), not re-enter
            if moving_direction is not None:
                from src.constants import Direction
                return moving_direction != Direction.UP
            return True
        return False

    def count_pellets(self):
        """Count remaining pellets and power pellets on the map."""
        count = 0
        for row in self.grid:
            for tile in row:
                if tile in (Tile.PELLET, Tile.POWER_PELLET):
                    count += 1
        return count
