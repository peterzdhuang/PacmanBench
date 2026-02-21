#!/usr/bin/env python3
"""Generate animated GIFs from PacmanBench demo runs.

Renders demo game recordings as retro Pac-Man style animated GIFs
with pixel-art sprites, classic colors, and score display.

Usage:
    python demos/generate_gif.py              # Generate GIFs for all runs
    python demos/generate_gif.py --run 0      # Generate GIF for first run only
    python demos/generate_gif.py --fps 8      # Custom frame rate
    python demos/generate_gif.py --cell 16    # Cell size (default: 16)

Output:
    demos/gifs/<provider>_<model>.gif
"""

import json
import os
import sys
import argparse

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Pillow is required: pip install Pillow")
    sys.exit(1)

# ──────────────────────────────────────────────────────────────────────────────
# Color Palette  (classic Pac-Man colours, RGB)
# ──────────────────────────────────────────────────────────────────────────────
BLACK          = (0, 0, 0)
WALL_FILL      = (33, 33, 222)
WALL_BORDER    = (66, 66, 255)
PELLET_COL     = (255, 183, 174)
POWER_COL      = (255, 255, 255)
PACMAN_COL     = (255, 255, 0)
BLINKY_COL     = (255, 0, 0)
PINKY_COL      = (255, 184, 255)
INKY_COL       = (0, 255, 255)
CLYDE_COL      = (255, 184, 82)
FRIGHT_COL     = (33, 33, 255)
FRIGHT_WHITE   = (255, 255, 255)
EYE_WHITE      = (255, 255, 255)
EYE_PUPIL      = (33, 33, 200)
CHERRY_BODY    = (255, 0, 0)
CHERRY_STEM    = (0, 180, 0)
CHERRY_LEAF    = (0, 220, 0)
DOOR_COL       = (255, 183, 255)
SCORE_COL      = (255, 255, 0)
TEXT_COL       = (255, 255, 255)
HEADER_BG      = (0, 0, 0)

# ──────────────────────────────────────────────────────────────────────────────
# Game constants (mirror src/engine.py & src/map.py)
# ──────────────────────────────────────────────────────────────────────────────
MAP_W, MAP_H   = 28, 31
PACMAN_START   = (14, 23)

# Direction deltas used for Pac-Man position tracking
DIR_DELTA = {
    "UP": (0, -1), "DOWN": (0, 1),
    "LEFT": (-1, 0), "RIGHT": (1, 0),
    "NONE": (0, 0),
}


# ──────────────────────────────────────────────────────────────────────────────
# ASCII frame parsing
# ──────────────────────────────────────────────────────────────────────────────
def parse_frame(ascii_map: str):
    """Return (header_dict, grid) from an ascii_map string.

    header_dict keys: Score, Ticks, Pellets, PowerUp (all str values).
    grid is a list of lists of single characters, padded to MAP_W.
    """
    lines = ascii_map.split("\n")
    header_line = lines[0]
    grid = [list(line.ljust(MAP_W)[:MAP_W]) for line in lines[1:]]
    # Pad rows if fewer than MAP_H
    while len(grid) < MAP_H:
        grid.append(list(" " * MAP_W))

    header = {}
    for part in header_line.split("|"):
        if ":" in part:
            k, v = part.split(":", 1)
            header[k.strip()] = v.strip()
    return header, grid


def find_all(grid, char):
    """Return list of (x, y) positions of *char* in *grid*."""
    return [
        (x, y)
        for y, row in enumerate(grid)
        for x, c in enumerate(row)
        if c == char
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Pac-Man position tracking  (disambiguates 'P' = Pac-Man vs Pinky)
# ──────────────────────────────────────────────────────────────────────────────
def track_pacman(frames):
    """Return a list of (x, y) for Pac-Man in each frame."""
    positions = []
    prev = PACMAN_START

    for frame in frames:
        _, grid = parse_frame(frame["ascii_map"])
        move = frame.get("move", "NONE")
        p_list = find_all(grid, "P")

        if not p_list:
            # Pac-Man not visible (dead / overlap) — keep previous pos
            positions.append(prev)
            continue

        if len(p_list) == 1:
            positions.append(p_list[0])
            prev = p_list[0]
            continue

        # Multiple 'P' — predict expected pos from previous + move
        dx, dy = DIR_DELTA.get(move, (0, 0))
        ex, ey = prev[0] + dx, prev[1] + dy
        # Tunnel wrapping
        if ey == 14:
            if ex < 0:
                ex = MAP_W - 1
            elif ex >= MAP_W:
                ex = 0

        best = min(p_list, key=lambda p: abs(p[0] - ex) + abs(p[1] - ey))
        positions.append(best)
        prev = best

    return positions


# ──────────────────────────────────────────────────────────────────────────────
# Entity classification
# ──────────────────────────────────────────────────────────────────────────────
def classify(grid, pacman_pos, tick):
    """Return dict  (x, y) → entity_type_str  for all entity cells."""
    entities = {}
    ghost_count = 0

    for y, row in enumerate(grid):
        for x, c in enumerate(row):
            if c == "B":
                entities[(x, y)] = "blinky"
                ghost_count += 1
            elif c == "I":
                entities[(x, y)] = "inky"
                ghost_count += 1
            elif c == "f":
                entities[(x, y)] = "frightened"
                ghost_count += 1
            elif c == "e":
                entities[(x, y)] = "eaten"
                ghost_count += 1
            elif c == "P":
                if (x, y) == pacman_pos:
                    entities[(x, y)] = "pacman"
                else:
                    entities[(x, y)] = "pinky"
                    ghost_count += 1
            # Defer 'C' — handled below

    # Classify 'C' characters (Clyde ghost vs Cherry tile)
    for x, y in find_all(grid, "C"):
        if ghost_count < 4:
            entities[(x, y)] = "clyde"
            ghost_count += 1
        else:
            entities[(x, y)] = "cherry"

    return entities


# ──────────────────────────────────────────────────────────────────────────────
# Sprite Renderer
# ──────────────────────────────────────────────────────────────────────────────
class Renderer:
    """Draws retro Pac-Man sprites onto PIL images."""

    def __init__(self, cell: int = 16, header_h: int = 48):
        self.c = cell
        self.hh = header_h
        self.w = MAP_W * cell
        self.h = MAP_H * cell + header_h

    # ── helpers ───────────────────────────────────────────────────────────
    def _rect(self, x, y):
        x0 = x * self.c
        y0 = y * self.c + self.hh
        return (x0, y0, x0 + self.c - 1, y0 + self.c - 1)

    def _center(self, x, y):
        return (x * self.c + self.c // 2,
                y * self.c + self.hh + self.c // 2)

    @staticmethod
    def _is_wall(grid, x, y):
        if 0 <= y < len(grid) and 0 <= x < len(grid[0]):
            return grid[y][x] == "#"
        return True  # out-of-bounds ≈ wall for border purposes

    # ── frame renderer ────────────────────────────────────────────────────
    def render(self, frame, pac_pos, tick, move, provider="", model=""):
        header, grid = parse_frame(frame["ascii_map"])
        power = int(header.get("PowerUp", "0"))

        img = Image.new("RGB", (self.w, self.h), BLACK)
        draw = ImageDraw.Draw(img)

        # Header bar
        self._header(draw, header, provider, model)

        # Maze tiles (from ASCII — skip entity chars)
        entity_chars = set("BIPCfeO")
        for y, row in enumerate(grid):
            for x, c in enumerate(row):
                if c == "#":
                    self._wall(draw, x, y, grid)
                elif c == "-":
                    self._door(draw, x, y)
                elif c == ".":
                    self._pellet(draw, x, y)
                elif c == "O":
                    self._power(draw, x, y, tick)

        # ── Use structured entity data if available ──
        ghost_data = frame.get("ghosts")
        if ghost_data is not None:
            # Draw ghosts from structured data
            ghost_color_map = {
                "Blinky": BLINKY_COL,
                "Pinky": PINKY_COL,
                "Inky": INKY_COL,
                "Clyde": CLYDE_COL,
            }
            for g in ghost_data:
                gx, gy = g["x"], g["y"]
                gstate = g.get("state", "CHASE")
                gname = g.get("name", "")
                if gstate == "FRIGHTENED":
                    self._frightened(draw, gx, gy, tick, power)
                elif gstate == "EATEN":
                    self._eyes(draw, *self._center(gx, gy))
                else:
                    col = ghost_color_map.get(gname, BLINKY_COL)
                    self._ghost(draw, gx, gy, col, tick)

            # Draw Pac-Man
            self._pacman(draw, pac_pos[0], pac_pos[1], move, tick)

            # Draw cherry from ASCII (if tile 'C' exists and isn't a ghost position)
            ghost_positions = {(g["x"], g["y"]) for g in ghost_data}
            for cx, cy in find_all(grid, "C"):
                if (cx, cy) not in ghost_positions:
                    self._cherry(draw, cx, cy)
        else:
            # Fallback: parse entities from ASCII (legacy format)
            ents = classify(grid, pac_pos, tick)
            ghost_map = {
                "blinky": BLINKY_COL,
                "pinky": PINKY_COL,
                "inky": INKY_COL,
                "clyde": CLYDE_COL,
            }
            for (ex, ey), etype in ents.items():
                if etype == "pacman":
                    self._pacman(draw, ex, ey, move, tick)
                elif etype in ghost_map:
                    self._ghost(draw, ex, ey, ghost_map[etype], tick)
                elif etype == "frightened":
                    self._frightened(draw, ex, ey, tick, power)
                elif etype == "eaten":
                    self._eyes(draw, *self._center(ex, ey))
                elif etype == "cherry":
                    self._cherry(draw, ex, ey)

        return img

    # ── header ────────────────────────────────────────────────────────────
    def _header(self, draw, hdr, provider, model):
        try:
            sz = max(11, self.hh // 3)
            font = ImageFont.truetype("arial.ttf", sz)
            sm = ImageFont.truetype("arial.ttf", max(10, sz - 3))
        except (OSError, IOError):
            font = ImageFont.load_default()
            sm = font

        draw.rectangle((0, 0, self.w, self.hh - 1), fill=HEADER_BG)

        # Row 1 — model label
        if provider or model:
            label = f"{provider}/{model}" if provider and model else (provider or model)
            draw.text((4, 2), label, fill=TEXT_COL, font=sm)

        # Row 2 — score / pellets / tick
        score = hdr.get("Score", "0")
        pellets = hdr.get("Pellets", "?")
        ticks = hdr.get("Ticks", "0")
        power = hdr.get("PowerUp", "0")
        line = f"SCORE {score}    PELLETS {pellets}    TICK {ticks}"
        if power != "0":
            line += f"    PWR {power}"
        draw.text((4, self.hh // 2 + 1), line, fill=SCORE_COL, font=sm)

    # ── wall ──────────────────────────────────────────────────────────────
    def _wall(self, draw, x, y, grid):
        c = self.c
        x0, y0, x1, y1 = self._rect(x, y)

        # Fill the cell with wall colour
        draw.rectangle((x0, y0, x1, y1), fill=WALL_FILL)

        # Bright border on edges facing corridors
        bw = max(1, c // 6)
        iw = self._is_wall
        if not iw(grid, x, y - 1):
            draw.rectangle((x0, y0, x1, y0 + bw - 1), fill=WALL_BORDER)
        if not iw(grid, x, y + 1):
            draw.rectangle((x0, y1 - bw + 1, x1, y1), fill=WALL_BORDER)
        if not iw(grid, x - 1, y):
            draw.rectangle((x0, y0, x0 + bw - 1, y1), fill=WALL_BORDER)
        if not iw(grid, x + 1, y):
            draw.rectangle((x1 - bw + 1, y0, x1, y1), fill=WALL_BORDER)

    # ── door (one-way ghost gate) ─────────────────────────────────────────
    def _door(self, draw, x, y):
        cx, cy = self._center(x, y)
        hw = self.c // 2 - 1
        hh = max(2, self.c // 5)
        draw.rectangle((cx - hw, cy - hh, cx + hw, cy + hh), fill=DOOR_COL)

    # ── pellet ────────────────────────────────────────────────────────────
    def _pellet(self, draw, x, y):
        cx, cy = self._center(x, y)
        r = max(1, self.c // 8)
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=PELLET_COL)

    # ── power pellet (pulsing) ────────────────────────────────────────────
    def _power(self, draw, x, y, tick):
        cx, cy = self._center(x, y)
        r = max(3, self.c * 3 // 8)
        col = POWER_COL if (tick // 3) % 2 == 0 else PELLET_COL
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col)

    # ── Pac-Man ───────────────────────────────────────────────────────────
    def _pacman(self, draw, x, y, direction, tick):
        cx, cy = self._center(x, y)
        r = self.c // 2 - 1

        # Mouth animation — 3-phase cycle
        phase = tick % 6
        mouth = 45 if phase < 2 else (25 if phase < 4 else 8)

        # PIL angles: 0°=east, clockwise.  pieslice draws from start→end CW.
        base = {"RIGHT": 0, "DOWN": 90, "LEFT": 180, "UP": 270, "NONE": 0}
        b = base.get(direction, 0)
        start = b + mouth
        end = b + 360 - mouth

        draw.pieslice((cx - r, cy - r, cx + r, cy + r),
                      start=start, end=end, fill=PACMAN_COL)

    # ── ghost body ────────────────────────────────────────────────────────
    def _ghost(self, draw, x, y, color, tick):
        c = self.c
        x0, y0, x1, y1 = self._rect(x, y)
        cx, cy = self._center(x, y)
        r = c // 2 - 1

        # Rounded top  (semicircle)
        draw.pieslice((cx - r, y0 + 1, cx + r, y0 + 2 * r + 1),
                      start=180, end=360, fill=color)

        # Rectangular body
        body_top = y0 + r + 1
        body_bot = y1 - max(2, c // 5)
        if body_top <= body_bot:
            draw.rectangle((cx - r, body_top, cx + r, body_bot), fill=color)

        # Wavy / scalloped bottom  (3 bumps, alternating)
        wave = max(2, c // 5)
        sw = max(1, (2 * r + 1) // 3)
        alt = (tick // 3) % 2
        for i in range(3):
            bx = cx - r + i * sw
            if (i % 2) == alt:
                draw.rectangle((bx, body_bot, bx + sw - 1, body_bot + wave),
                               fill=color)

        # Eyes
        self._eyes(draw, cx, cy - max(1, c // 7))

    # ── ghost eyes ────────────────────────────────────────────────────────
    def _eyes(self, draw, cx, ey):
        c = self.c
        er = max(2, c // 5)
        pr = max(1, er // 2)
        sp = max(3, c // 4)
        for dx in (-sp, sp):
            ex = cx + dx
            draw.ellipse((ex - er, ey - er, ex + er, ey + er), fill=EYE_WHITE)
            draw.ellipse((ex - pr, ey - pr, ex + pr, ey + pr), fill=EYE_PUPIL)

    # ── frightened ghost ──────────────────────────────────────────────────
    def _frightened(self, draw, x, y, tick, power_timer):
        # Flash blue/white when power-up nearly expired
        if power_timer > 0 and power_timer < 15:
            col = FRIGHT_COL if (tick // 2) % 2 == 0 else FRIGHT_WHITE
        else:
            col = FRIGHT_COL
        self._ghost(draw, x, y, col, tick)

    # ── cherry ────────────────────────────────────────────────────────────
    def _cherry(self, draw, x, y):
        cx, cy = self._center(x, y)
        c = self.c
        r = max(2, c // 4)

        # Two berries
        draw.ellipse((cx - r - 2, cy + 1, cx, cy + r + 2), fill=CHERRY_BODY)
        draw.ellipse((cx + 1, cy, cx + r + 2, cy + r + 1), fill=CHERRY_BODY)

        # Stems
        sw = max(1, c // 10)
        draw.line([(cx - r // 2, cy + 1), (cx, cy - r)],
                  fill=CHERRY_STEM, width=sw)
        draw.line([(cx + r // 2 + 1, cy), (cx, cy - r)],
                  fill=CHERRY_STEM, width=sw)

        # Small leaf
        lx, ly = cx + 2, cy - r - 1
        lr = max(1, c // 8)
        draw.ellipse((lx, ly, lx + lr * 2, ly + lr), fill=CHERRY_LEAF)


# ──────────────────────────────────────────────────────────────────────────────
# GIF generation
# ──────────────────────────────────────────────────────────────────────────────
def generate_gif(run, output_path, cell=16, fps=10, header_h=48):
    """Render all frames of a run and save as an animated GIF."""
    frames = run["frames"]
    provider = run.get("provider", "")
    model = run.get("model", "")

    # Determine Pac-Man positions: use structured data if available, else heuristic
    has_pacman_data = "pacman" in frames[0] if frames else False
    if has_pacman_data:
        print(f"  Using structured position data ({len(frames)} frames) …")
        pac_positions = [(f["pacman"]["x"], f["pacman"]["y"]) for f in frames]
    else:
        print(f"  Tracking Pac-Man across {len(frames)} frames (ASCII fallback) …")
        pac_positions = track_pacman(frames)

    renderer = Renderer(cell=cell, header_h=header_h)
    images = []

    print("  Rendering …")
    for i, frame in enumerate(frames):
        tick = frame.get("tick", i)
        move = frame.get("move", "NONE")
        img = renderer.render(frame, pac_positions[i], tick, move, provider, model)

        # Quantise to 64-colour palette for efficient GIF
        images.append(img.quantize(colors=64, method=Image.Quantize.MEDIANCUT))

        if (i + 1) % 100 == 0:
            print(f"    {i + 1}/{len(frames)}")

    print(f"  Writing {output_path} …")
    ms = 1000 // fps

    # Hold last frame for 3 seconds
    durations = [ms] * len(images)
    if durations:
        durations[-1] = 3000

    images[0].save(
        output_path,
        save_all=True,
        append_images=images[1:],
        duration=durations,
        loop=0,
        optimize=True,
    )

    size_kb = os.path.getsize(output_path) / 1024
    print(f"  ✓ {size_kb:.0f} KB  ({len(images)} frames @ {fps} FPS)\n")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Generate Pac-Man GIFs from demo runs")
    ap.add_argument("--run", type=int, default=None,
                    help="Index of a single run to render (default: all)")
    ap.add_argument("--fps", type=int, default=10,
                    help="Frames per second (default: 10)")
    ap.add_argument("--cell", type=int, default=16,
                    help="Pixel size of each grid cell (default: 16)")
    ap.add_argument("--input", type=str, default=None,
                    help="Path to demo_runs.json")
    ap.add_argument("--output-dir", type=str, default=None,
                    help="Output directory (default: demos/gifs)")
    args = ap.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    inp = args.input or os.path.join(here, "demo_runs.json")
    out = args.output_dir or os.path.join(here, "gifs")

    if not os.path.exists(inp):
        print(f"Error: {inp} not found.  Run generate_demos.py first.")
        sys.exit(1)

    with open(inp) as f:
        data = json.load(f)
    runs = data["runs"]
    print(f"Loaded {len(runs)} run(s) from {inp}\n")

    os.makedirs(out, exist_ok=True)

    indices = [args.run] if args.run is not None else list(range(len(runs)))

    for idx in indices:
        if idx < 0 or idx >= len(runs):
            print(f"Run {idx} out of range (0–{len(runs) - 1})")
            continue

        r = runs[idx]
        prov = r.get("provider", "unknown")
        mdl = r.get("model", "unknown")
        summary = r.get("summary", {})
        safe = f"{prov}_{mdl}".replace("/", "_").replace(" ", "_")
        path = os.path.join(out, f"{safe}.gif")

        print(f"{'=' * 60}")
        print(f"Run {idx}: {prov}/{mdl}")
        print(f"  Score {summary.get('final_score', '?')}  |  "
              f"Pellets {summary.get('completion_pct', '?')}%  |  "
              f"Ticks {summary.get('total_ticks', '?')}")
        print(f"{'=' * 60}")

        generate_gif(r, path, cell=args.cell, fps=args.fps)

    print(f"All GIFs saved to {out}/")


if __name__ == "__main__":
    main()
