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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# DLA Parameters
NUM_BLOCKS = 3200
BLOCK_SIZE = 5.0
STEP_SIZE = 14.0
STICK_DIST = 12.0
LIMIT = 1000.0

# Simulation data
positions = np.zeros((NUM_BLOCKS, 3))
scales = np.zeros(NUM_BLOCKS)
scales = np.random.uniform(0.5, 2.5, (NUM_BLOCKS, 3)) # W, H, D
hues = np.zeros(NUM_BLOCKS)
ages = np.zeros(NUM_BLOCKS)

# Starfield
NUM_STARS = 6000
star_pos = np.random.uniform(-1800, 1800, (NUM_STARS, 3))
star_brits = np.random.uniform(150, 255, NUM_STARS)

def generate_dla():
    global positions, scales, hues, ages
    
    # Seed at origin
    positions[0] = [0, 0, 0]
    scales[0] = [2.0, 5.0, 2.0]
    hues[0] = 190 # Cyan
    ages[0] = 0
    
    grid = {} # (ix, iy, iz) -> set of indices
    def add_to_grid(idx, pos):
        ix, iy, iz = np.floor(pos / STICK_DIST).astype(int)
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                for dz in [-1, 0, 1]:
                    key = (ix+dx, iy+dy, iz+dz)
                    if key not in grid: grid[key] = set()
                    grid[key].add(idx)

    add_to_grid(0, positions[0])
    
    count = 1
    max_radius = 20.0
    stick_dist_sq = STICK_DIST**2
    last_print = 0
    while count < NUM_BLOCKS:
        if count % 400 == 0 and count != last_print:
            print(f"Generating DLA: {count}/{NUM_BLOCKS} (R: {max_radius:.1f})")
            sys.stdout.flush()
            last_print = count
        
        # Spawn wanderer on a sphere just outside the cluster
        angle1 = np.random.uniform(0, 2 * np.pi)
        angle2 = np.random.uniform(0, np.pi)
        r = max_radius + STICK_DIST * 1.2
        p = np.array([
            r * np.sin(angle2) * np.cos(angle1),
            r * np.sin(angle2) * np.sin(angle1),
            r * np.cos(angle2)
        ])
        
        stuck = False
        for _ in range(1500): # Faster turnaround
            # Random walk
            p += np.random.uniform(-STEP_SIZE, STEP_SIZE, 3)
            
            # Distance from center
            d_sq = np.sum(p**2)
            
            # If too far, kill and respawn
            if d_sq > (max_radius * 1.8 + 80.0)**2:
                break
            
            # Proximity check using grid
            ix, iy, iz = np.floor(p / STICK_DIST).astype(int)
            key = (ix, iy, iz)
            if key in grid:
                for other_idx in grid[key]:
                    dist_sq = np.sum((p - positions[other_idx])**2)
                    if dist_sq < stick_dist_sq:
                        positions[count] = p
                        d = np.sqrt(d_sq)
                        # Tall skyscraper proportions
                        scales[count] = [
                            np.random.uniform(0.5, 1.5),
                            np.random.uniform(1.0, 4.0) * (1.0 + d * 0.001),
                            np.random.uniform(0.5, 1.5)
                        ]
                        hues[count] = (180 + np.random.uniform(-30, 90)) % 360
                        ages[count] = count
                        add_to_grid(count, p)
                        
                        if d > max_radius:
                            max_radius = d
                        
                        count += 1
                        stuck = True
                        break
            if stuck: break

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    if FRAMES_DIR.exists():
        import shutil
        shutil.rmtree(FRAMES_DIR)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)
    generate_dla()

def draw():
    py5.background(0)
    
    # Camera - more dramatic sweeping orbit
    t = py5.frame_count * 0.006
    cam_r = 1000 - 400 * np.cos(t * 0.3)
    py5.camera(cam_r * np.cos(t), -400 - 200 * np.sin(t * 0.5), cam_r * np.sin(t), 0, 0, 0, 0, 1, 0)
    
    # Starfield
    py5.stroke_weight(1.2)
    for i in range(NUM_STARS):
        # Subtle twinkle
        b = star_brits[i] * (0.6 + 0.4 * np.sin(t * 5 + i))
        py5.stroke(255, b * 0.5)
        py5.point(*star_pos[i])
        
    # Draw city (Aggregated blocks)
    # Number of visible blocks grows with time
    visible_count = int(np.interp(py5.frame_count, [0, TOTAL_FRAMES], [1, NUM_BLOCKS]))
    
    # 1. SOLID CORE PASS (BLEND)
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    
    # Pre-slice for performance
    v_pos = positions[:visible_count]
    v_scales = scales[:visible_count]
    v_hues = hues[:visible_count]
    
    # Group by hue to reduce state changes
    num_bins = 8
    for b in range(num_bins):
        h_min = 150 + b * (150 / num_bins)
        h_max = h_min + (150 / num_bins)
        mask = (v_hues >= h_min) & (v_hues < h_max)
        if np.any(mask):
            p_bin = v_pos[mask]
            s_bin = v_scales[mask]
            h_val = (h_min + (h_max - h_min) / 2) % 360
            
            # Obsidian core
            py5.fill(h_val, 30, 15, 100)
            for i in range(len(p_bin)):
                py5.push_matrix()
                py5.translate(*p_bin[i])
                py5.box(s_bin[i][0] * BLOCK_SIZE, s_bin[i][1] * BLOCK_SIZE, s_bin[i][2] * BLOCK_SIZE)
                py5.pop_matrix()

    # 2. NEON HIGHLIGHT & GLOW PASS (ADD)
    py5.blend_mode(py5.ADD)
    for b in range(num_bins):
        h_min = 150 + b * (150 / num_bins)
        h_max = h_min + (150 / num_bins)
        mask = (v_hues >= h_min) & (v_hues < h_max)
        if np.any(mask):
            p_bin = v_pos[mask]
            s_bin = v_scales[mask]
            h_val = (h_min + (h_max - h_min) / 2) % 360
            
            # Sub-glow
            py5.fill(h_val, 80, 50, 15)
            for i in range(len(p_bin)):
                py5.push_matrix()
                py5.translate(*p_bin[i])
                py5.box(s_bin[i][0] * BLOCK_SIZE * 1.4, s_bin[i][1] * BLOCK_SIZE * 1.1, s_bin[i][2] * BLOCK_SIZE * 1.4)
                py5.pop_matrix()
                
            # Sharp neon outline
            py5.no_fill()
            py5.stroke(h_val, 90, 100, 90)
            py5.stroke_weight(1.5)
            for i in range(len(p_bin)):
                py5.push_matrix()
                py5.translate(*p_bin[i])
                py5.box(s_bin[i][0] * BLOCK_SIZE * 1.05, s_bin[i][1] * BLOCK_SIZE * 1.02, s_bin[i][2] * BLOCK_SIZE * 1.05)
                py5.pop_matrix()
            py5.no_stroke()

    py5.blend_mode(py5.BLEND)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
