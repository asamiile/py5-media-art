from pathlib import Path
import shutil
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
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_NODES = 400
MAX_DIST = 250

positions = None
velocities = None

def setup():
    global positions, velocities
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.random.rand(NUM_NODES, 2) * np.array([py5.width, py5.height])
    velocities = (np.random.rand(NUM_NODES, 2) - 0.5) * 4.0

def draw():
    global positions, velocities
    
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)

    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.05
    
    # Update positions
    positions += velocities
    
    # Bounce off walls
    for i in range(NUM_NODES):
        if positions[i][0] < 0 or positions[i][0] > py5.width:
            velocities[i][0] *= -1
        if positions[i][1] < 0 or positions[i][1] > py5.height:
            velocities[i][1] *= -1
            
    # Add slight perlin noise drift
    for i in range(NUM_NODES):
        noise_x = py5.os_noise(positions[i][0] * 0.005, positions[i][1] * 0.005, time)
        noise_y = py5.os_noise(positions[i][0] * 0.005 + 1000, positions[i][1] * 0.005 + 1000, time)
        
        velocities[i][0] += (noise_x - 0.5) * 0.5
        velocities[i][1] += (noise_y - 0.5) * 0.5
        
        # clamp velocity
        speed = np.linalg.norm(velocities[i])
        if speed > 5.0:
            velocities[i] = (velocities[i] / speed) * 5.0
    
    # Draw connections
    for i in range(NUM_NODES):
        p1 = positions[i]
        
        # Calculate distances to all other points
        diffs = positions[i+1:] - p1
        dists = np.linalg.norm(diffs, axis=1)
        
        close_indices = np.where(dists < MAX_DIST)[0]
        
        for idx in close_indices:
            j = i + 1 + idx
            p2 = positions[j]
            d = dists[idx]
            
            # alpha is inversely proportional to distance
            alpha = py5.remap(d, 0, MAX_DIST, 100, 0)
            
            # hue pulses based on distance and time
            hue = (200 + d * 0.5 + time * 10) % 360
            
            # Hot pink and cyan
            if hue > 280: hue = 320 # pink
            elif hue > 180: hue = 190 # cyan
            
            py5.stroke(hue, 90, 100, alpha)
            py5.stroke_weight(py5.remap(d, 0, MAX_DIST, 3, 0.5))
            
            py5.line(p1[0], p1[1], p2[0], p2[1])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

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
