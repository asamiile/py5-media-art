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
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 15000
positions = None
velocities = None

def setup():
    global positions, velocities
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize particles outside the center
    positions = np.random.rand(NUM_PARTICLES, 2) * [SIZE[0], SIZE[1]]
    velocities = (np.random.rand(NUM_PARTICLES, 2) - 0.5) * 4.0
    
    py5.background(2, 0, 5)

def draw():
    global positions, velocities
    
    # Subtractive trail effect
    py5.fill(2, 0, 5, 30)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    # Black hole singularity gravity
    diff = np.array([cx, cy]) - positions
    dist_sq = np.sum(diff**2, axis=1, keepdims=True)
    dist = np.sqrt(dist_sq)
    
    # Inverse square gravity, very strong
    force = diff / np.clip(dist_sq, 1000.0, None) * 1000.0
    
    # Add a tangential rotational force (accretion disk)
    tangent = np.stack([-diff[:, 1], diff[:, 0]], axis=-1)
    tangent_force = tangent / np.clip(dist_sq, 1000.0, None) * 2000.0
    
    velocities += force + tangent_force
    
    # Friction
    velocities *= 0.98
    
    # Update positions
    prev_positions = positions.copy()
    positions += velocities
    
    # Re-spawn particles that fall into the event horizon or go too far off screen
    event_horizon = dist < 50.0
    off_screen = (positions[:, 0] < -1000) | (positions[:, 0] > SIZE[0] + 1000) | \
                 (positions[:, 1] < -1000) | (positions[:, 1] > SIZE[1] + 1000)
    reset_mask = event_horizon.flatten() | off_screen
    
    if np.any(reset_mask):
        num_reset = np.sum(reset_mask)
        # spawn far away
        angle = np.random.rand(num_reset) * 2 * np.pi
        rad = np.random.rand(num_reset) * 500 + 1000
        positions[reset_mask, 0] = cx + rad * np.cos(angle)
        positions[reset_mask, 1] = cy + rad * np.sin(angle)
        
        v_angle = angle + np.pi/2 # tangent
        velocities[reset_mask, 0] = np.cos(v_angle) * 5.0
        velocities[reset_mask, 1] = np.sin(v_angle) * 5.0
        prev_positions[reset_mask] = positions[reset_mask]

    # Draw lines
    py5.blend_mode(py5.ADD)
    
    # Color mapping based on speed (relativistic blue shift)
    speeds = np.linalg.norm(velocities, axis=1)
    
    verts = np.empty((NUM_PARTICLES * 2, 2))
    verts[0::2] = prev_positions
    verts[1::2] = positions
    
    # Fast drawing with buckets based on speed
    slow_mask = speeds < 10.0
    med_mask = (speeds >= 10.0) & (speeds < 30.0)
    fast_mask = speeds >= 30.0
    
    def draw_bucket(mask, color, weight):
        if not np.any(mask): return
        v_sub = np.empty((np.sum(mask) * 2, 2))
        v_sub[0::2] = prev_positions[mask]
        v_sub[1::2] = positions[mask]
        py5.stroke(*color)
        py5.stroke_weight(weight)
        py5.begin_shape(py5.LINES)
        py5.vertices(v_sub)
        py5.end_shape()

    # Violet/Blue for slow
    draw_bucket(slow_mask, (170, 68, 255, 100), 1.5)
    # Cyan for medium
    draw_bucket(med_mask, (136, 204, 255, 150), 2.0)
    # White for fast
    draw_bucket(fast_mask, (255, 255, 255, 200), 2.5)
    
    py5.blend_mode(py5.BLEND)

    # Draw event horizon (black circle)
    py5.fill(0)
    py5.no_stroke()
    py5.circle(cx, cy, 100)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...", flush=True)
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
            
        import os
        os._exit(0)

py5.run_sketch()
