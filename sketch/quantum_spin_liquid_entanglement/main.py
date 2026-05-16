from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
LATTICE_DIM = 24
NUM_SITES = LATTICE_DIM * LATTICE_DIM
NUM_TRACERS = 100000

# Site coordinates (Triangular Lattice)
i = np.arange(LATTICE_DIM)
j = np.arange(LATTICE_DIM)
ii, jj = np.meshgrid(i, j)
site_x = (ii + 0.5 * (jj % 2)) * 60 - (LATTICE_DIM * 30)
site_y = jj * 52 - (LATTICE_DIM * 26)
site_pos = np.stack([site_x.flatten(), site_y.flatten()], axis=-1)

# Dimers: Initially 1-2, 3-4, ...
# site_indices[k] is paired with site_indices[k+1] for even k
dimer_pairs = np.arange(NUM_SITES)
np.random.shuffle(dimer_pairs)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.background(10, 5, 20)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global dimer_pairs
    t = py5.frame_count
    
    py5.background(8, 4, 15)
    
    # RVB Dynamics: Stochastic Dimer Swapping
    # Pick a random "plaquette" (4 sites) and swap if they are currently paired as (1,2), (3,4)
    for _ in range(50):
        idx = np.random.randint(0, NUM_SITES, 4)
        # Simplified: just swap random pairs occasionally
        p1, p2 = np.random.randint(0, NUM_SITES // 2, 2)
        if np.random.random() < 0.1:
            # Swap partner of 2*p1 and 2*p2
            dimer_pairs[2*p1+1], dimer_pairs[2*p2+1] = dimer_pairs[2*p2+1], dimer_pairs[2*p1+1]

    # Rendering: Entanglement Threads
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2)
    py5.rotate(t * 0.002)
    
    py5.blend_mode(py5.ADD)
    
    # Draw dimers
    p1_indices = dimer_pairs[0::2]
    p2_indices = dimer_pairs[1::2]
    
    pos1 = site_pos[p1_indices]
    pos2 = site_pos[p2_indices]
    
    # HSB mapping for color
    # Deep Amethyst (280), Electric Lime (80), Stark White (0,0,100)
    # Use distance or index to modulate color
    dist = np.sqrt(np.sum((pos1 - pos2)**2, axis=-1))
    
    # Drawing threads
    # For performance, we'll draw a subset of lines or use a vectorized approach
    # py5.lines(x1, y1, x2, y2) doesn't exist, but we can use points or lines in a loop
    # or just use tracers
    
    # Vectorized point cloud around threads
    # Each dimer has a few tracers
    num_per_dimer = NUM_TRACERS // (NUM_SITES // 2)
    
    # Linear interpolation + noise
    lerp_t = np.random.random((NUM_SITES // 2, num_per_dimer, 1))
    tracer_pos = pos1[:, np.newaxis, :] * (1 - lerp_t) + pos2[:, np.newaxis, :] * lerp_t
    tracer_pos += np.random.normal(0, 2.0, tracer_pos.shape)
    
    # Flatten for rendering
    flat_pos = tracer_pos.reshape(-1, 2)
    
    # Color bands
    # Amethyst band
    py5.stroke_weight(1.5)
    py5.stroke(150, 50, 250, 40)
    py5.points(flat_pos[::3])
    
    # Lime band
    py5.stroke(180, 255, 50, 30)
    py5.points(flat_pos[1::3])
    
    # White sparks
    py5.stroke(255, 255, 255, 60)
    py5.stroke_weight(2.0)
    py5.points(flat_pos[2::6])
    
    py5.pop_matrix()
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-crf", "18",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
