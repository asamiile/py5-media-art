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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 50000
SPHERE_RADIUS = OUTPUT_SIZE[0] * 0.25

positions = None
velocities = None
flash_life = None

def setup():
    global positions, velocities, flash_life
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.random.uniform(-SIZE[0], SIZE[0], (NUM_PARTICLES, 3))
    positions[:, 1] = np.random.uniform(-SIZE[1]*2, SIZE[1]*2, NUM_PARTICLES)
    
    velocities = np.zeros((NUM_PARTICLES, 3))
    velocities[:, 1] = np.random.uniform(15, 40, NUM_PARTICLES)
    
    flash_life = np.zeros(NUM_PARTICLES)

def draw():
    global positions, velocities, flash_life
    
    py5.background(5, 5, 12)
    
    # Update physics
    positions += velocities
    velocities[:, 1] += 0.3 # gravity
    
    # Check collision with sphere at center
    dists = np.linalg.norm(positions, axis=1)
    hit_mask = dists < SPHERE_RADIUS
    
    if np.any(hit_mask):
        normals = positions[hit_mask] / dists[hit_mask, None]
        dots = np.sum(velocities[hit_mask] * normals, axis=1)
        # Bounce only if moving towards the center
        bounce_mask = dots < 0
        
        if np.any(bounce_mask):
            # We need to map the bounce_mask back to the hit_mask subset
            hit_indices = np.where(hit_mask)[0]
            bounce_indices = hit_indices[bounce_mask]
            
            n = normals[bounce_mask]
            v = velocities[bounce_indices]
            d = dots[bounce_mask]
            
            velocities[bounce_indices] = (v - 2 * d[:, None] * n) * 0.7
            positions[bounce_indices] = n * (SPHERE_RADIUS + 1)
            flash_life[bounce_indices] = 1.0
            
            # add a bit of random scatter
            velocities[bounce_indices] += np.random.uniform(-5, 5, (len(bounce_indices), 3))
        
    # Reset particles
    reset_mask = positions[:, 1] > SIZE[1] * 1.5
    if np.any(reset_mask):
        positions[reset_mask, 0] = np.random.uniform(-SIZE[0], SIZE[0], np.sum(reset_mask))
        positions[reset_mask, 1] = np.random.uniform(-SIZE[1]*1.5, -SIZE[1], np.sum(reset_mask))
        positions[reset_mask, 2] = np.random.uniform(-SIZE[0], SIZE[0], np.sum(reset_mask))
        velocities[reset_mask, 0] = 0
        velocities[reset_mask, 1] = np.random.uniform(15, 40, np.sum(reset_mask))
        velocities[reset_mask, 2] = 0
        flash_life[reset_mask] = 0.0
        
    flash_life = np.clip(flash_life - 0.03, 0, 1)
    
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2, -SIZE[0]/2)
    
    # Slowly rotate camera
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.sin(py5.frame_count * 0.01) * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    # Draw points in groups by flash life to assign colors efficiently
    for i in range(5):
        thresh_low = i / 5.0
        thresh_high = (i+1) / 5.0
        mask = (flash_life >= thresh_low) & (flash_life <= thresh_high)
        if i == 4:
            mask = (flash_life >= thresh_low) # include exactly 1.0
            
        if np.any(mask):
            pts = positions[mask]
            vels = velocities[mask]
            
            r = py5.lerp(0, 255, thresh_low)
            g = py5.lerp(200, 50, thresh_low)
            b = py5.lerp(255, 255, thresh_low)
            a = 80 + 175 * thresh_low
            
            # Motion blur effect
            for step in range(3):
                pos_step = pts - vels * (step * 0.5)
                py5.stroke(r, g, b, a / (step + 1))
                py5.stroke_weight(3 if step == 0 else 1)
                py5.points(pos_step)
                
    # Draw central sphere faintly
    py5.blend_mode(py5.BLEND)
    py5.no_fill()
    py5.stroke(0, 200, 255, 20)
    py5.stroke_weight(2)
    py5.sphere_detail(40)
    py5.sphere(SPHERE_RADIUS * 0.98)
    
    py5.pop_matrix()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 10 == 0:
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
