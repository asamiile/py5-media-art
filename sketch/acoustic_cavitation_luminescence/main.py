import numpy as np
import py5
from pathlib import Path
import subprocess
import sys

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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_BUBBLES = 50000

# [x, y, z, vx, vy, vz, phase, active, flash_intensity]
bubbles = np.zeros((NUM_BUBBLES, 9), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    global bubbles
    bubbles[:, 0] = np.random.uniform(-SIZE[0]/1.5, SIZE[0]/1.5, NUM_BUBBLES)
    bubbles[:, 1] = np.random.uniform(-SIZE[1]/1.5, SIZE[1]/1.5, NUM_BUBBLES)
    bubbles[:, 2] = np.random.uniform(-800, 800, NUM_BUBBLES)
    
    # Random phases for collapse timing
    bubbles[:, 6] = np.random.uniform(0, 2*np.pi, NUM_BUBBLES)
    bubbles[:, 7] = 1.0

def draw():
    global bubbles
    
    py5.background(230, 100, 10)
    py5.blend_mode(py5.ADD)
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    py5.rotate_y(py5.frame_count * 0.002)
    py5.rotate_x(py5.frame_count * 0.001)
    
    # Acoustic standing wave pushes bubbles towards antinodes
    k = 0.015
    force_x = -np.sin(bubbles[:, 0] * k)
    force_y = -np.sin(bubbles[:, 1] * k)
    force_z = -np.sin(bubbles[:, 2] * k)
    
    bubbles[:, 3] += force_x * 0.6
    bubbles[:, 4] += force_y * 0.6
    bubbles[:, 5] += force_z * 0.6
    
    # Apply drag
    bubbles[:, 3:6] *= 0.82
    
    # Update position
    bubbles[:, 0:3] += bubbles[:, 3:6]
    
    # Update phase based on acoustic frequency
    bubbles[:, 6] += 0.08
    
    # Determine flash (when phase crosses 2*pi)
    flash_mask = bubbles[:, 6] > 2 * np.pi
    bubbles[flash_mask, 6] -= 2 * np.pi
    
    # The pressure must be high. High pressure = near nodes: sin(x*k) ~ 0.
    pressure = np.abs(np.cos(bubbles[:, 0] * k) * np.cos(bubbles[:, 1] * k) * np.cos(bubbles[:, 2] * k))
    
    # Update flash intensities
    bubbles[:, 8] *= 0.7  # Decay
    
    flashers = flash_mask & (pressure > 0.7) & (np.random.rand(NUM_BUBBLES) > 0.95)
    bubbles[flashers, 8] = 100.0  # Max intensity
    
    # Draw normal bubbles (dim cyan)
    normal_mask = bubbles[:, 8] < 10
    if np.any(normal_mask):
        py5.stroke(180, 100, 60, 40)
        py5.stroke_weight(1.5)
        py5.points(bubbles[normal_mask, 0:3])
        
    # Draw flashing bubbles
    bright_mask = bubbles[:, 8] >= 10
    if np.any(bright_mask):
        bright_bubbles = bubbles[bright_mask]
        
        for b in bright_bubbles:
            intensity = b[8]
            # When very bright -> white, otherwise violet
            if intensity > 60:
                py5.stroke(0, 0, 100, intensity)
                py5.stroke_weight(intensity * 0.12)
                py5.point(b[0], b[1], b[2])
            else:
                py5.stroke(270, 100, 90, intensity * 1.5)
                py5.stroke_weight(4)
                py5.point(b[0], b[1], b[2])
                
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
