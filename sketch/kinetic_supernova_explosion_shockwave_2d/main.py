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

NUM_PARTICLES = 100000
positions = None
velocities = None
lifetimes = None

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global positions, velocities, lifetimes
    positions = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    positions[:, 0] = py5.width / 2.0
    positions[:, 1] = py5.height / 2.0
    
    # Initialize velocities with an outward burst
    angles = np.random.uniform(0, 2 * np.pi, NUM_PARTICLES)
    speeds = np.random.normal(15.0, 5.0, NUM_PARTICLES) # Fast burst
    velocities = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    velocities[:, 0] = np.cos(angles) * speeds
    velocities[:, 1] = np.sin(angles) * speeds
    
    lifetimes = np.random.uniform(0, 1, NUM_PARTICLES)

def draw():
    global positions, velocities, lifetimes
    
    # Subtle fade
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 10)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Update physics
    # Deceleration (drag)
    velocities *= 0.96
    
    # Add turbulence
    # We'll use a very fast simplified noise approach
    time_val = py5.frame_count * 0.01
    
    # Small random perturbation
    perturbation = np.random.normal(0, 0.5, (NUM_PARTICLES, 2))
    velocities += perturbation
    
    # Move
    positions += velocities
    lifetimes -= 0.005
    
    # Mask active
    active = lifetimes > 0
    pos_active = positions[active]
    vel_active = velocities[active]
    
    # Draw points
    # Color by speed and lifetime
    speeds = np.linalg.norm(vel_active, axis=1)
    
    # Map speeds to hue
    # Fast -> White/Gold (60), Medium -> Magenta (300), Slow -> Cyan (180)
    
    # Simple bucketing for performance
    fast_mask = speeds > 5.0
    med_mask = (speeds <= 5.0) & (speeds > 1.0)
    slow_mask = speeds <= 1.0
    
    py5.stroke_weight(2.0)
    
    # Fast
    if np.any(fast_mask):
        py5.stroke(60, 20, 100, 50)
        py5.points(pos_active[fast_mask])
        
    # Medium
    if np.any(med_mask):
        py5.stroke(300, 80, 100, 30)
        py5.points(pos_active[med_mask])
        
    # Slow
    if np.any(slow_mask):
        py5.stroke(180, 90, 80, 15)
        py5.points(pos_active[slow_mask])

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
