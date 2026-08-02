from pathlib import Path
import random
import subprocess
import sys
import shutil
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS

PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
_, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE  # 3840 x 2160

# Grid layout
CELL_SIZE = 160
COLS = 24
ROWS = 13
X_OFFSET = 0
Y_OFFSET = (SIZE[1] - ROWS * CELL_SIZE) // 2  # 40

# Tile definitions: [up, right, down, left]
TILES = {
    "empty": [0, 0, 0, 0],
    "line_h": [0, 1, 0, 1],
    "line_v": [1, 0, 1, 0],
    "corner_ur": [1, 1, 0, 0],
    "corner_rd": [0, 1, 1, 0],
    "corner_dl": [0, 0, 1, 1],
    "corner_lu": [1, 0, 0, 1],
    "t_up": [1, 1, 0, 1],
    "t_right": [1, 1, 1, 0],
    "t_down": [0, 1, 1, 1],
    "t_left": [1, 0, 1, 1],
    "cross": [1, 1, 1, 1],
}

# Opposite directions for adjacency checks
OPPOSITE = {
    0: 2,  # Up -> Down
    1: 3,  # Right -> Left
    2: 0,  # Down -> Up
    3: 1,  # Left -> Right
}

# Neighbors relative offsets
NEIGHBORS = [
    (0, -1, 0),  # Up (direction index 0)
    (1, 0, 1),   # Right (direction index 1)
    (0, 1, 2),   # Down (direction index 2)
    (-1, 0, 3),  # Left (direction index 3)
]

# Wave Function Collapse Solver Class
class WFCSolver:
    def __init__(self, cols, rows):
        self.cols = cols
        self.rows = rows
        self.grid = {}  # (x, y) -> set of tile names
        self.collapsed = {}  # (x, y) -> tile name
        self.reset()

    def reset(self):
        self.grid = {(x, y): set(TILES.keys()) for x in range(self.cols) for y in range(self.rows)}
        self.collapsed = {}
        # Apply boundary constraints
        for x in range(self.cols):
            for y in range(self.rows):
                impossible = set()
                for tile_name in self.grid[(x, y)]:
                    ports = TILES[tile_name]
                    # If on boundary, pointing out must be 0
                    if y == 0 and ports[0] != 0:
                        impossible.add(tile_name)
                    if x == self.cols - 1 and ports[1] != 0:
                        impossible.add(tile_name)
                    if y == self.rows - 1 and ports[2] != 0:
                        impossible.add(tile_name)
                    if x == 0 and ports[3] != 0:
                        impossible.add(tile_name)
                self.grid[(x, y)] -= impossible

    def get_neighbors(self, x, y):
        result = []
        for dx, dy, d_idx in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.cols and 0 <= ny < self.rows:
                result.append((nx, ny, d_idx))
        return result

    def constrain(self):
        # Propagate constraints
        queue = [(x, y) for x in range(self.cols) for y in range(self.rows)]
        while queue:
            cx, cy = queue.pop(0)
            current_possibilities = self.grid[(cx, cy)]
            if not current_possibilities:
                return False

            for nx, ny, d_idx in self.get_neighbors(cx, cy):
                neighbor_possibilities = self.grid[(nx, ny)]
                if not neighbor_possibilities:
                    continue

                # Find valid neighbor ports
                valid_ports = set()
                for t in current_possibilities:
                    valid_ports.add(TILES[t][d_idx])

                # Check if neighbor has tiles that don't match
                opp_dir = OPPOSITE[d_idx]
                invalid = set()
                for nt in neighbor_possibilities:
                    if TILES[nt][opp_dir] not in valid_ports:
                        invalid.add(nt)

                if invalid:
                    self.grid[(nx, ny)] -= invalid
                    if not self.grid[(nx, ny)]:
                        return False
                    if (nx, ny) not in queue:
                        queue.append((nx, ny))
        return True

    def run_to_completion(self):
        history = []  # list of grid states
        collapse_order = []  # list of collapsed cell coordinates
        
        # Save initial state
        history.append({k: set(v) for k, v in self.grid.items()})

        while len(self.collapsed) < self.cols * self.rows:
            # Find cell with minimum entropy
            min_entropy = 9999
            candidates = []
            for (x, y), poss in self.grid.items():
                if (x, y) not in self.collapsed:
                    e = len(poss)
                    if e == 0:
                        return None, None, None  # Contradiction
                    if e < min_entropy:
                        min_entropy = e
                        candidates = [(x, y)]
                    elif e == min_entropy:
                        candidates.append((x, y))

            if not candidates:
                break

            # Choose one and collapse
            cx, cy = random.choice(candidates)
            choices = list(self.grid[(cx, cy)])
            if not choices:
                return None, None, None  # Contradiction

            chosen = random.choice(choices)
            self.grid[(cx, cy)] = {chosen}
            self.collapsed[(cx, cy)] = chosen
            collapse_order.append((cx, cy))

            # Propagate constraints
            success = self.constrain()
            if not success:
                return None, None, None  # Contradiction

            # Save state
            history.append({k: set(v) for k, v in self.grid.items()})

        return history, collapse_order, self.collapsed

# Global simulation state
wfc_history = []
wfc_collapse_order = []
wfc_final_grid = {}
distances = {}
source_cell = (0, 0)

def precompute_wfc():
    global wfc_history, wfc_collapse_order, wfc_final_grid, distances, source_cell
    print("[WFC Precompute] Solving WFC constraint grid...")
    attempts = 0
    while True:
        attempts += 1
        solver = WFCSolver(COLS, ROWS)
        history, order, final = solver.run_to_completion()
        if history is not None:
            wfc_history = history
            wfc_collapse_order = order
            wfc_final_grid = final
            print(f"[WFC Precompute] Solved successfully on attempt {attempts}!")
            break
        if attempts > 200:
            print("[Error] Failed to solve WFC after 200 attempts. Check adjacency constraints.")
            import os
            os._exit(1)

    # Pick the first collapsed cell as the source for the light pulse
    source_cell = wfc_collapse_order[0]
    
    # Run BFS on final grid to compute geodesic distance from source cell
    print("[WFC Precompute] Computing circuit path distances...")
    distances = {source_cell: 0}
    queue = [source_cell]
    while queue:
        cx, cy = queue.pop(0)
        dist = distances[(cx, cy)]
        
        current_tile = wfc_final_grid[(cx, cy)]
        current_ports = TILES[current_tile]
        
        for dx, dy, d_idx in NEIGHBORS:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < COLS and 0 <= ny < ROWS:
                # Must be connected in the current tile port and the neighbor's opposite port
                neighbor_tile = wfc_final_grid[(nx, ny)]
                opp_dir = OPPOSITE[d_idx]
                if current_ports[d_idx] == 1 and TILES[neighbor_tile][opp_dir] == 1:
                    if (nx, ny) not in distances:
                        distances[(nx, ny)] = dist + 1
                        queue.append((nx, ny))

    # Fill unreached cells with a high default distance
    for x in range(COLS):
        for y in range(ROWS):
            if (x, y) not in distances:
                distances[(x, y)] = 999

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.frame_rate(FPS)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Run the WFC algorithm once to get the exact sequence of shapes
    precompute_wfc()

def draw():
    # Base background (pitch black void)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    # Establish schedule
    # 0 - 120 (2s): Pure superposition
    # 120 - 600 (8s): Collapse
    # 600 - 780 (3s): Active pulse
    # 780 - 900 (2s): Dissolve / Decay back to black
    fc = py5.frame_count
    
    # Determine the step index in the WFC collapse history
    if fc < 120:
        step_idx = 0
    elif fc < 600:
        step_idx = int(py5.remap(fc, 120, 600, 0, len(wfc_collapse_order)))
    else:
        step_idx = len(wfc_collapse_order)

    # Get the current grid state from pre-computed history
    current_grid_state = wfc_history[min(step_idx, len(wfc_history) - 1)]

    # Draw the grid cells
    for x in range(COLS):
        for y in range(ROWS):
            possibilities = current_grid_state.get((x, y), set())
            is_determined = (len(possibilities) == 1)
            chosen_tile = list(possibilities)[0] if is_determined else None
            
            # Cell center screen coordinate
            cx = X_OFFSET + x * CELL_SIZE + CELL_SIZE // 2
            cy = Y_OFFSET + y * CELL_SIZE + CELL_SIZE // 2
            
            # Animation factors
            pulse = py5.sin(fc * 0.08 + (x + y) * 0.3) * 0.5 + 0.5
            
            # Draw cell background/hologram if not fully resolved
            if not is_determined:
                # Faint grid box
                py5.no_fill()
                py5.stroke(60, 40, 100, 15)  # Soft violet
                py5.stroke_weight(1)
                py5.rect(cx - CELL_SIZE // 2, cy - CELL_SIZE // 2, CELL_SIZE, CELL_SIZE)
                
                # Render possible tiles at low opacity with a shimmering rotation
                py5.push_matrix()
                py5.translate(cx, cy)
                # Shimmer rotation proportional to entropy
                entropy_factor = len(possibilities) / len(TILES)
                py5.rotate(fc * 0.015 * entropy_factor + (x * 0.1 - y * 0.15))
                
                # Render outlines of possible shapes
                for tile_name in possibilities:
                    draw_tile_shape(0, 0, CELL_SIZE, tile_name, opacity=12, stroke_color=py5.color(0, 200, 255))
                py5.pop_matrix()
                
            else:
                # Fully determined cell. Render high-fidelity neon pathway.
                # Compute base color based on geodesic distance
                d = distances.get((x, y), 999)
                
                # Fade out during the final dissolve phase (780 - 900)
                fade_alpha = 255
                if fc > 780:
                    fade_alpha = int(py5.remap(fc, 780, 900, 255, 0))
                
                # Dynamic current pulse wavefront
                # Propagation speed of 0.35 hops per frame
                pulse_intensity = 0.0
                if 600 <= fc <= 780:
                    pulse_center = (fc - 600) * 0.35
                    pulse_intensity = py5.exp(-((d - pulse_center) ** 2) / 12.0)
                
                # Draw the glowing back-glow line (thick violet/amethyst)
                glow_color = py5.color(180, 30, 255)
                # If pulse is passing, boost brightness and shift color towards gold
                if pulse_intensity > 0.01:
                    glow_color = py5.lerp_color(glow_color, py5.color(255, 200, 0), pulse_intensity)
                
                draw_tile_shape(cx, cy, CELL_SIZE, chosen_tile, opacity=int(60 * (fade_alpha / 255.0)), stroke_color=glow_color, weight=14)
                
                # Draw the sharp foreground line (cyan/white core)
                core_color = py5.color(0, 240, 255)
                if pulse_intensity > 0.01:
                    core_color = py5.lerp_color(core_color, py5.color(255, 255, 255), pulse_intensity)
                
                draw_tile_shape(cx, cy, CELL_SIZE, chosen_tile, opacity=int(230 * (fade_alpha / 255.0)), stroke_color=core_color, weight=3.5)

                # Draw terminal connection joints (small circle at ports)
                draw_ports_markers(cx, cy, CELL_SIZE, chosen_tile, core_color, fade_alpha)

    # Progress feedback: prevents silent timeouts and makes it clear the render is healthy
    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES} ({fc/TOTAL_FRAMES*100:.1f}%)")

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot (midpoint frame is at frame 450)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory to save storage
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)  # Force exit to prevent macOS JVM hangs

def draw_tile_shape(cx, cy, size, tile_name, opacity, stroke_color, weight=2):
    """Draw a tile design centered at (cx, cy) with given size, color and weight."""
    py5.no_fill()
    py5.stroke(py5.red(stroke_color), py5.green(stroke_color), py5.blue(stroke_color), opacity)
    py5.stroke_weight(weight)
    
    ports = TILES.get(tile_name, [0, 0, 0, 0])
    r = size // 2
    
    # 0 = Up, 1 = Right, 2 = Down, 3 = Left
    if tile_name == "empty":
        # Draw a small decorative micro-chip dot in empty cells to suggest structural details
        py5.fill(py5.red(stroke_color), py5.green(stroke_color), py5.blue(stroke_color), opacity * 0.4)
        py5.no_stroke()
        py5.circle(cx, cy, weight * 1.5)
        py5.no_fill()
        return

    # Draw connections
    if tile_name == "line_h":
        py5.line(cx - r, cy, cx + r, cy)
    elif tile_name == "line_v":
        py5.line(cx, cy - r, cx, cy + r)
    elif tile_name == "corner_ur":
        # Draw curved arc corner centered at (cx + r, cy - r)
        py5.arc(cx + r, cy - r, size, size, py5.HALF_PI, py5.PI)
    elif tile_name == "corner_rd":
        # Draw curved arc corner centered at (cx + r, cy + r)
        py5.arc(cx + r, cy + r, size, size, py5.PI, py5.PI + py5.HALF_PI)
    elif tile_name == "corner_dl":
        # Draw curved arc corner centered at (cx - r, cy + r)
        py5.arc(cx - r, cy + r, size, size, py5.PI + py5.HALF_PI, py5.TWO_PI)
    elif tile_name == "corner_lu":
        # Draw curved arc corner centered at (cx - r, cy - r)
        py5.arc(cx - r, cy - r, size, size, 0, py5.HALF_PI)
    elif tile_name == "t_up":
        py5.line(cx - r, cy, cx + r, cy)
        py5.line(cx, cy, cx, cy - r)
    elif tile_name == "t_right":
        py5.line(cx, cy - r, cx, cy + r)
        py5.line(cx, cy, cx + r, cy)
    elif tile_name == "t_down":
        py5.line(cx - r, cy, cx + r, cy)
        py5.line(cx, cy, cx, cy + r)
    elif tile_name == "t_left":
        py5.line(cx, cy - r, cx, cy + r)
        py5.line(cx, cy, cx - r, cy)
    elif tile_name == "cross":
        py5.line(cx - r, cy, cx + r, cy)
        py5.line(cx, cy - r, cx, cy + r)

def draw_ports_markers(cx, cy, size, tile_name, stroke_color, fade_alpha):
    """Draw small techy circles at the junction ports to make it look like a circuit."""
    ports = TILES.get(tile_name, [0, 0, 0, 0])
    r = size // 2
    py5.no_stroke()
    py5.fill(py5.red(stroke_color), py5.green(stroke_color), py5.blue(stroke_color), int(180 * (fade_alpha / 255.0)))
    
    # Center junction dot
    if tile_name != "empty" and tile_name != "line_h" and tile_name != "line_v":
        py5.circle(cx, cy, 6)
        
    # Boundary ports dots
    if ports[0]: py5.circle(cx, cy - r, 4)
    if ports[1]: py5.circle(cx + r, cy, 4)
    if ports[2]: py5.circle(cx, cy + r, 4)
    if ports[3]: py5.circle(cx - r, cy, 4)

py5.run_sketch()
