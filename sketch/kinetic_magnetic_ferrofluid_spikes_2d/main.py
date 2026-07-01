from pathlib import Path
import shutil
import subprocess
import sys
import random
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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 8000
positions = None
velocities = None
masses = None

def setup():
    global positions, velocities, masses
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles
    # Center them mostly around the middle
    theta = np.random.rand(NUM_PARTICLES) * 2 * np.pi
    r = np.sqrt(np.random.rand(NUM_PARTICLES)) * SIZE[0] * 0.4
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    positions = np.zeros((NUM_PARTICLES, 2))
    positions[:, 0] = cx + r * np.cos(theta)
    positions[:, 1] = cy + r * np.sin(theta)
    
    velocities = np.zeros((NUM_PARTICLES, 2))
    masses = np.random.rand(NUM_PARTICLES) * 0.5 + 0.5

def draw():
    global positions, velocities
    
    t = py5.frame_count / 60.0
    
    # Subtractive trail effect
    py5.fill(240, 240, 240, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    # Trigonometric flow field for organic fluid motion
    x_norm = (positions[:, 0] - cx) / SIZE[0] * 6.0
    y_norm = (positions[:, 1] - cy) / SIZE[1] * 6.0
    flow_x = np.sin(y_norm * 1.5 + t * 0.8) * np.cos(x_norm * 0.5 - t * 0.5)
    flow_y = np.cos(x_norm * 1.2 + t * 0.7) * np.sin(y_norm * 0.8 - t * 0.6)
    total_force = np.stack([flow_x, flow_y], axis=-1) * 12.0
    
    # Weakened magnetic poles for structural attractors
    poles = [
        np.array([cx + np.sin(t * 0.5) * 600, cy + np.cos(t * 0.4) * 400]),
        np.array([cx + np.cos(t * 0.6) * 700, cy + np.sin(t * 0.7) * 500]),
    ]
    strengths = [15.0, -10.0] 
    
    for pole, strength in zip(poles, strengths):
        diff = pole - positions
        dist_sq = np.sum(diff**2, axis=1, keepdims=True)
        # Avoid division by zero and limit max force
        dist_sq = np.clip(dist_sq, 2000.0, None)
        force = (strength * diff) / np.sqrt(dist_sq) * 2.0  # inverse linear instead of inverse square
        total_force += force
        
    # Weak global pull to keep them on screen
    center_diff = np.array([cx, cy]) - positions
    center_dist = np.sqrt(np.sum(center_diff**2, axis=1, keepdims=True))
    total_force += (center_diff / np.clip(center_dist, 1.0, None)) * (center_dist / 1000.0)**2 * 5.0
    
    velocities += (total_force / masses[:, None]) * 0.5
    
    # Friction
    velocities *= 0.92
    
    # Update positions
    prev_positions = positions.copy()
    positions += velocities
    
    # Interleave for py5.vertices (drawing lines)
    # Each line segment goes from prev_positions to positions
    verts = np.empty((NUM_PARTICLES * 2, 2))
    verts[0::2] = prev_positions
    verts[1::2] = prev_positions - velocities * 4.0 # Draw a spike in the direction of velocity
    
    py5.stroke(10, 10, 10, 200) # Glossy black
    py5.stroke_weight(3.0)
    py5.begin_shape(py5.LINES)
    py5.vertices(verts)
    py5.end_shape()

    # Sometimes draw accent blue spikes
    if py5.frame_count % 3 == 0:
        py5.stroke(16, 32, 64, 150) # Magnetic Blue
        py5.stroke_weight(2.0)
        py5.begin_shape(py5.LINES)
        py5.vertices(verts[::4]) # subset
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

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
