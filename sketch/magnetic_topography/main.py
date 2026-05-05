from pathlib import Path
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
GRID_RES = 10
CONTOUR_LEVELS = 22
DIPOLE_COUNT = 7

dipoles = []
field_grid = None

def setup():
    global dipoles, field_grid
    py5.size(*SIZE)
    py5.background(10, 5, 5)
    py5.no_loop()
    
    # Randomly place dipoles
    for _ in range(DIPOLE_COUNT):
        pos = np.array([np.random.uniform(0, py5.width), np.random.uniform(0, py5.height)])
        strength = np.random.uniform(500, 2000)
        dipoles.append({'pos': pos, 'strength': strength})

    # Calculate field grid
    cols = py5.width // GRID_RES + 1
    rows = py5.height // GRID_RES + 1
    field_grid = np.zeros((rows, cols))
    
    for r in range(rows):
        for c in range(cols):
            x, y = c * GRID_RES, r * GRID_RES
            total_field = 0
            for d in dipoles:
                dist = np.linalg.norm(np.array([x, y]) - d['pos'])
                total_field += d['strength'] / (dist + 80)**1.5
            field_grid[r, c] = total_field

def get_state(a, b, c, d, threshold):
    res = 0
    if a >= threshold: res += 8
    if b >= threshold: res += 4
    if c >= threshold: res += 2
    if d >= threshold: res += 1
    return res

def draw():
    py5.background(12, 8, 8)
    
    # Draw starfield
    py5.stroke(255, 120)
    for _ in range(1500):
        py5.stroke_weight(np.random.uniform(0.5, 1.5))
        py5.point(np.random.uniform(0, py5.width), np.random.uniform(0, py5.height))
        
    # Marching Squares
    max_f = np.max(field_grid)
    min_f = np.min(field_grid)
    levels = np.linspace(min_f + 0.02, max_f - 0.05, CONTOUR_LEVELS)
    
    rows, cols = field_grid.shape
    
    for lvl_idx, threshold in enumerate(levels):
        t = lvl_idx / len(levels)
        py5.color_mode(py5.HSB, 255)
        # Deep Teal to Electric Copper
        hue = py5.lerp(140, 25, t)
        sat = 180 + t * 75
        brt = 150 + t * 105
        py5.stroke(hue, sat, brt, 220)
        py5.stroke_weight(1.0 + t * 1.5)
        
        for r in range(rows - 1):
            for c in range(cols - 1):
                x = c * GRID_RES
                y = r * GRID_RES
                
                f_tl = field_grid[r, c]
                f_tr = field_grid[r, c+1]
                f_br = field_grid[r+1, c+1]
                f_bl = field_grid[r+1, c]
                
                state = get_state(f_tl, f_tr, f_br, f_bl, threshold)
                
                # Draw lines for each state
                half = GRID_RES / 2
                if state == 1 or state == 14:
                    py5.line(x, y + half, x + half, y + GRID_RES)
                elif state == 2 or state == 13:
                    py5.line(x + half, y + GRID_RES, x + GRID_RES, y + half)
                elif state == 3 or state == 12:
                    py5.line(x, y + half, x + GRID_RES, y + half)
                elif state == 4 or state == 11:
                    py5.line(x + half, y, x + GRID_RES, y + half)
                elif state == 5:
                    py5.line(x, y + half, x + half, y)
                    py5.line(x + half, y + GRID_RES, x + GRID_RES, y + half)
                elif state == 6 or state == 9:
                    py5.line(x + half, y, x + half, y + GRID_RES)
                elif state == 7 or state == 8:
                    py5.line(x, y + half, x + half, y)
                elif state == 10:
                    py5.line(x, y + half, x + half, y + GRID_RES)
                    py5.line(x + half, y, x + GRID_RES, y + half)

    py5.color_mode(py5.RGB, 255)
    
    # Draw Dipole Cores with glow
    for d in dipoles:
        for r_offset in range(4):
            py5.no_stroke()
            py5.fill(255, 250, 180, 50 // (r_offset + 1))
            py5.circle(d['pos'][0], d['pos'][1], 10 + r_offset * 12)

    py5.save(str(SKETCH_DIR / PREVIEW_FILENAME))
    py5.exit_sketch()

if __name__ == "__main__":
    py5.run_sketch()
