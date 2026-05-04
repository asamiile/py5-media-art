from pathlib import Path
import subprocess
import sys
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.preview import maybe_save_exit_on_frame, preview_filename
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Particle System Constants
NUM_PARTICLES = 8000
MAX_AGE = 150
NOISE_SCALE = 0.005
SPEED = 2.0

# State
pos = np.random.rand(NUM_PARTICLES, 2) * np.array(SIZE)
old_pos = pos.copy()
age = np.random.randint(0, MAX_AGE, NUM_PARTICLES)

def setup():
    py5.size(*SIZE)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(250, 80, 5) # Deep indigo
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    global pos, old_pos, age
    
    t = py5.frame_count / TOTAL_FRAMES
    
    # Atmospheric accumulation (don't clear background completely)
    py5.fill(250, 80, 5, 5)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    # Vector Field Advection
    # Compute angles using noise
    noise_vec = np.frompyfunc(py5.noise, 3, 1)
    angles = noise_vec(pos[:, 0] * NOISE_SCALE, pos[:, 1] * NOISE_SCALE, t * 0.5).astype(float) * np.pi * 4
    vel = np.stack([np.cos(angles), np.sin(angles)], axis=-1) * SPEED
    
    old_pos[:] = pos
    pos += vel
    age += 1
    
    # Boundaries and Reset
    mask_offscreen = (pos[:, 0] < 0) | (pos[:, 0] > py5.width) | (pos[:, 1] < 0) | (pos[:, 1] > py5.height)
    mask_old = age > MAX_AGE
    mask_reset = mask_offscreen | mask_old
    
    if np.any(mask_reset):
        pos[mask_reset] = np.random.rand(np.sum(mask_reset), 2) * np.array(SIZE)
        old_pos[mask_reset] = pos[mask_reset]
        age[mask_reset] = 0
        
    # Rendering
    # Group by color to optimize draw calls
    hue_base = (t * 360) % 360
    for i in range(0, NUM_PARTICLES, 100):
        # Sample few particles for color
        p_hue = (hue_base + (i / NUM_PARTICLES) * 120) % 360
        py5.stroke(p_hue, 70, 90, 40)
        py5.stroke_weight(1.0)
        
        # Batch draw lines
        p_slice = slice(i, i + 100)
        for j in range(i, min(i + 100, NUM_PARTICLES)):
            py5.line(old_pos[j, 0], old_pos[j, 1], pos[j, 0], pos[j, 1])

    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Preview
    if py5.frame_count == 1:
        py5.save_frame(str(SKETCH_DIR / PREVIEW_FILENAME))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Update preview to a middle frame
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
