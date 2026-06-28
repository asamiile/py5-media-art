from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 30
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
NUM_FILINGS = 40000
FILING_LENGTH = 15.0

# 3 North poles (+1), 3 South poles (-1)
NUM_POLES = 6
pole_charges = np.array([1.0, 1.0, 1.0, -1.0, -1.0, -1.0])

def setup():
    py5.size(*SIZE)
    py5.no_smooth()
    py5.pixel_density(1)
    py5.background(10, 15, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global filing_pos, pole_phases
    # Distribute iron filings uniformly across the canvas
    filing_pos = np.random.rand(NUM_FILINGS, 2)
    filing_pos[:, 0] *= py5.width
    filing_pos[:, 1] *= py5.height
    
    # Each pole gets a random phase for its orbital movement
    pole_phases = np.random.rand(NUM_POLES) * py5.PI * 2
    
def draw():
    # Motion blur fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15, 20, 80)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    py5.stroke(200, 220, 255, 150) # Glowing silver
    
    progress = py5.frame_count / TOTAL_FRAMES
    time_val = progress * py5.PI * 2.0
    
    # Calculate pole positions
    # They orbit in complex Lissajous patterns to create dynamic, smooth loops
    pole_pos = np.zeros((NUM_POLES, 2))
    for i in range(NUM_POLES):
        px = py5.width / 2 + np.cos(time_val + pole_phases[i]) * py5.width * 0.35
        py = py5.height / 2 + np.sin(time_val * 2.0 + pole_phases[i]) * py5.height * 0.35
        
        # Add some Perlin noise to make the orbits more chaotic but still looping
        # noise(cos(t), sin(t)) gives a looping noise path
        nx = np.cos(time_val) * 0.5 + i * 10
        ny = np.sin(time_val) * 0.5 + i * 10
        px += (py5.noise(nx, ny) - 0.5) * py5.width * 0.2
        py += (py5.noise(nx + 100, ny + 100) - 0.5) * py5.height * 0.2
        
        pole_pos[i] = [px, py]
        
    # Calculate magnetic field vector at each filing location
    # B = sum( Q_i / r_i^2 * r_hat_i )
    field_vectors = np.zeros((NUM_FILINGS, 2))
    
    # Vectorized computation for all 40,000 filings against the 6 poles
    for i in range(NUM_POLES):
        # vector from pole to filing
        dx = filing_pos[:, 0] - pole_pos[i, 0]
        dy = filing_pos[:, 1] - pole_pos[i, 1]
        
        # distance squared
        r2 = dx*dx + dy*dy
        r2 = np.maximum(r2, 1000.0) # prevent division by zero / extreme values
        
        # distance
        r = np.sqrt(r2)
        
        # normalized direction vector
        ux = dx / r
        uy = dy / r
        
        # force magnitude (1/r^2)
        # multiply by charge: positive repels (points away), negative attracts (points towards)
        magnitude = pole_charges[i] * 500000.0 / r2
        
        field_vectors[:, 0] += ux * magnitude
        field_vectors[:, 1] += uy * magnitude
        
    # Normalize the final field vectors to set the length of the iron filing lines
    lengths = np.sqrt(field_vectors[:, 0]**2 + field_vectors[:, 1]**2)
    # Avoid division by zero
    lengths[lengths < 1e-5] = 1e-5
    
    dir_x = field_vectors[:, 0] / lengths
    dir_y = field_vectors[:, 1] / lengths
    
    # Generate line coordinates: [x - L*dx, y - L*dy] to [x + L*dx, y + L*dy]
    lines = np.empty((NUM_FILINGS, 2, 2))
    half_L = FILING_LENGTH / 2.0
    
    lines[:, 0, 0] = filing_pos[:, 0] - dir_x * half_L
    lines[:, 0, 1] = filing_pos[:, 1] - dir_y * half_L
    lines[:, 1, 0] = filing_pos[:, 0] + dir_x * half_L
    lines[:, 1, 1] = filing_pos[:, 1] + dir_y * half_L
    
    line_coords = lines.reshape(-1, 4)
    py5.lines(line_coords)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 30 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
