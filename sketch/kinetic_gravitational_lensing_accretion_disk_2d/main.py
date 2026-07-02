import os
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
FINAL_VIDEO = SKETCH_DIR / f"{WORK_NAME}.mp4"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Setup particles for accretion disk
N_PARTICLES = 150000
G_MASS = 8000.0   # Gravitational parameter
SOFTENING = 20.0  # Prevent infinite gravity at singularity

positions = np.zeros((N_PARTICLES, 2))
velocities = np.zeros((N_PARTICLES, 2))
masses = np.random.uniform(0.5, 2.0, N_PARTICLES)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.background(0)
    
    # Initialize particles in a disk around the center
    # Density should be higher near the center, lower outwards
    r = np.random.normal(SIZE[1]*0.3, SIZE[1]*0.1, N_PARTICLES)
    r = np.abs(r) + 50 # Avoid absolute center
    theta = np.random.uniform(0, 2 * np.pi, N_PARTICLES)
    
    positions[:, 0] = SIZE[0]/2 + r * np.cos(theta)
    positions[:, 1] = SIZE[1]/2 + r * np.sin(theta)
    
    # Orbital velocity v = sqrt(G*M / r) for circular orbit
    v_mag = np.sqrt(G_MASS / r) * 15.0 # Scaled for visual effect
    
    # Add some turbulence
    v_mag += np.random.normal(0, v_mag * 0.1)
    
    # Tangent vector is (-sin, cos)
    velocities[:, 0] = -np.sin(theta) * v_mag
    velocities[:, 1] = np.cos(theta) * v_mag
    
    # We want an elliptical/tilted look, so we scale Y to fake 3D perspective
    positions[:, 1] = SIZE[1]/2 + (positions[:, 1] - SIZE[1]/2) * 0.3
    velocities[:, 1] *= 0.3

def draw():
    # Subtle background fade for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 5, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global positions, velocities
    
    center = np.array([py5.width/2, py5.height/2])
    
    # Calculate gravity vector towards center
    d = center - positions
    
    # Fake 3D distance by un-scaling Y for physics calculations
    d_phys = d.copy()
    d_phys[:, 1] /= 0.3
    
    dist_sq = np.sum(d_phys**2, axis=1, keepdims=True)
    dist = np.sqrt(dist_sq)
    
    # F = G * M / (r^2 + softening^2)
    force_mag = G_MASS / (dist_sq + SOFTENING**2)
    
    # Direction vector
    direction = d_phys / (dist + 0.001)
    
    # Acceleration
    accel = direction * force_mag
    
    # Re-scale acceleration back to our fake 3D projection
    accel[:, 1] *= 0.3
    
    velocities += accel
    
    # Add a tiny bit of drag so they spiral in very slowly
    velocities *= 0.998
    
    old_positions = positions.copy()
    positions += velocities
    
    # Draw particles
    # Calculate color based on speed and distance
    speed = np.linalg.norm(velocities, axis=1)
    
    # Blue shifted (fast, inner) to Red shifted (slow, outer)
    # Using py5.lines for trails
    py5.stroke_weight(1.5)
    
    # To draw efficiently with varying colors in py5, we can't vectorize different stroke colors in a single py5.lines call
    # Instead we'll split into 3 speed buckets (Hot Blue, Orange, Red)
    speed_percentile = np.percentile(speed, [33, 66])
    
    mask_slow = speed < speed_percentile[0]
    mask_med = (speed >= speed_percentile[0]) & (speed < speed_percentile[1])
    mask_fast = speed >= speed_percentile[1]
    
    # Slow - Deep Red
    if np.any(mask_slow):
        p1 = old_positions[mask_slow]
        p2 = positions[mask_slow]
        lines_array = np.column_stack((p1[:, 0], p1[:, 1], p2[:, 0], p2[:, 1]))
        py5.stroke(200, 30, 30, 80)
        py5.lines(lines_array)
        
    # Medium - Gold/Orange
    if np.any(mask_med):
        p1 = old_positions[mask_med]
        p2 = positions[mask_med]
        lines_array = np.column_stack((p1[:, 0], p1[:, 1], p2[:, 0], p2[:, 1]))
        py5.stroke(255, 150, 50, 120)
        py5.lines(lines_array)
        
    # Fast - Bright Cyan/White (Inner disk)
    if np.any(mask_fast):
        p1 = old_positions[mask_fast]
        p2 = positions[mask_fast]
        lines_array = np.column_stack((p1[:, 0], p1[:, 1], p2[:, 0], p2[:, 1]))
        py5.stroke(150, 230, 255, 180)
        py5.lines(lines_array)

    # Draw the central black hole (pure black to occlude)
    py5.blend_mode(py5.BLEND)
    py5.fill(0)
    py5.no_stroke()
    py5.ellipse(center[0], center[1], 80, 80 * 0.3)
    
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
        
        import os
        os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
