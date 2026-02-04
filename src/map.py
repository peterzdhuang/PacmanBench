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
    "     W.WWWWW WW WWWWW.W     ",
    "     W.WW          WW.W     ",
    "     W.WW WWW--WWW WW.W     ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "      .   W      W   .      ",
    "WWWWWW.WW W      W WW.WWWWWW",
    "     W.WW WWWWWWWW WW.W     ",
    "     W.WW          WW.W     ",
    "     W.WW WWWWWWWW WW.W     ",
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

    def is_wall(self, x, y):
        # Handle wrapping for the tunnel
        if y == 14 and (x < 0 or x >= self.width):
            return False
        return self.get_tile(x, y) == Tile.WALL
