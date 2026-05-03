from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 5  # Reduced for faster iteration
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_PARTICLES = 40000
GRID_DEPTH = 6
STREET_WIDTH = 2
MIN_BLOCK_SIZE = 30

particles_pos = None
particles_vel = None
particles_col = None
blocks = []
streets_mask = None
window_grids = []


def recursive_subdivide(x, y, w, h, depth):
    if depth == 0 or w < MIN_BLOCK_SIZE * 2 or h < MIN_BLOCK_SIZE * 2:
        # Add block with padding for streets
        bx, by, bw, bh = x + STREET_WIDTH, y + STREET_WIDTH, w - STREET_WIDTH * 2, h - STREET_WIDTH * 2
        blocks.append((bx, by, bw, bh))
        
        # Pre-calculate window grid for this block
        if bw > 15 and bh > 15:
            rows = int(bh / 10)
            cols = int(bw / 10)
            if rows > 1 and cols > 1:
                grid = []
                for r in range(rows):
                    for c in range(cols):
                        if np.random.rand() > 0.4:  # 60% chance of a light being on
                            grid.append((bx + 2 + c * 10, by + 2 + r * 10, 4, 4))
                window_grids.append(grid)
            else:
                window_grids.append([])
        else:
            window_grids.append([])
        return

    # Random split
    if np.random.rand() > 0.5:
        # Vertical split
        split = np.random.uniform(0.3, 0.7) * w
        recursive_subdivide(x, y, split, h, depth - 1)
        recursive_subdivide(x + split, y, w - split, h, depth - 1)
    else:
        # Horizontal split
        split = np.random.uniform(0.3, 0.7) * h
        recursive_subdivide(x, y, w, split, depth - 1)
        recursive_subdivide(x, y + split, w, h - split, depth - 1)


def setup():
    global particles_pos, particles_vel, particles_col, streets_mask
    py5.size(*SIZE)
    py5.background(5, 5, 8)  # Near black
    FRAMES_DIR.mkdir(exist_ok=True)

    # Generate City Grid
    recursive_subdivide(0, 0, SIZE[0], SIZE[1], GRID_DEPTH)

    # Create Streets Mask (for particle navigation)
    streets_mask = np.ones((SIZE[1], SIZE[0]), dtype=np.uint8)
    for bx, by, bw, bh in blocks:
        x1, y1 = max(0, int(bx)), max(0, int(by))
        x2, y2 = min(SIZE[0], int(bx + bw)), min(SIZE[1], int(by + bh))
        streets_mask[y1:y2, x1:x2] = 0

    # Initialize Particles
    street_indices = np.argwhere(streets_mask == 1)
    if len(street_indices) == 0:
        particles_pos = np.random.uniform(0, SIZE[0], (NUM_PARTICLES, 2))
    else:
        chosen_indices = street_indices[np.random.choice(len(street_indices), NUM_PARTICLES)]
        particles_pos = chosen_indices[:, [1, 0]].astype(np.float32)
    
    dirs = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]], dtype=np.float32)
    particles_vel = dirs[np.random.choice(4, NUM_PARTICLES)] * np.random.uniform(2, 6, (NUM_PARTICLES, 1))

    colors = [
        (0, 242, 255),  # Cyan
        (255, 0, 255),  # Magenta
        (255, 220, 100)  # Golden Amber
    ]
    color_indices = np.random.choice(len(colors), NUM_PARTICLES, p=[0.5, 0.4, 0.1])
    particles_col = np.array([colors[i] for i in color_indices], dtype=np.float32)


def draw():
    global particles_pos, particles_vel
    
    # Dark fade for trails
    py5.no_stroke()
    py5.fill(5, 5, 8, 25)
    py5.rect(0, 0, py5.width, py5.height)

    # Pulse effect
    pulse = np.sin(py5.frame_count * 0.08) * 0.5 + 0.5

    # Draw Background blocks and windows
    for i, (bx, by, bw, bh) in enumerate(blocks):
        py5.no_stroke()
        py5.fill(20, 20, 35, 40)
        py5.rect(bx, by, bw, bh)
        
        # Windows
        if window_grids[i]:
            for wx, wy, ww, wh in window_grids[i]:
                # Flicker windows
                if np.random.rand() > 0.01:
                    py5.fill(60, 60, 100, 30 + pulse * 40)
                    py5.rect(wx, wy, ww, wh)

    # Update Particles
    particles_pos += particles_vel
    particles_pos[:, 0] %= SIZE[0]
    particles_pos[:, 1] %= SIZE[1]
    
    idx_y = particles_pos[:, 1].astype(int) % SIZE[1]
    idx_x = particles_pos[:, 0].astype(int) % SIZE[0]
    in_block = streets_mask[idx_y, idx_x] == 0
    
    if np.any(in_block):
        particles_pos[in_block] -= particles_vel[in_block]
        dirs = np.array([[1, 0], [-1, 0], [0, 1], [0, -1]], dtype=np.float32)
        new_dirs = dirs[np.random.choice(4, np.sum(in_block))]
        particles_vel[in_block] = new_dirs * np.random.uniform(2, 6, (np.sum(in_block), 1))

    # Draw Particles
    py5.blend_mode(py5.ADD)
    
    cyan_mask = (particles_col[:, 0] == 0)
    mag_mask = (particles_col[:, 0] == 255) & (particles_col[:, 1] == 0)
    gold_mask = (particles_col[:, 0] == 255) & (particles_col[:, 1] == 220)
    
    # Cyan
    py5.stroke(0, 242, 255, 120 + pulse * 80)
    py5.stroke_weight(1.5)
    py5.points(particles_pos[cyan_mask])
    
    # Magenta
    py5.stroke(255, 0, 255, 100 + pulse * 60)
    py5.stroke_weight(1.5)
    py5.points(particles_pos[mag_mask])
    
    # Gold
    py5.stroke(255, 220, 100, 180 + pulse * 75)
    py5.stroke_weight(2.5)
    py5.points(particles_pos[gold_mask])

    py5.blend_mode(py5.BLEND)

    # Video recording
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # Ensure FFmpeg is available and run it
        try:
            subprocess.run([
                "ffmpeg", "-y", "-r", str(FPS),
                "-i", str(FRAMES_DIR / "frame-%04d.png"),
                "-vcodec", "libx264", "-pix_fmt", "yuv420p",
                str(SKETCH_DIR / "output.mp4"),
            ], check=True)
            # Copy middle frame for preview
            mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
            subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        except Exception as e:
            print(f"Error encoding video: {e}")


if __name__ == "__main__":
    py5.run_sketch()
