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

# Particle setup
N_PARTICLES = 30000
MAX_SPEED = 6.0
NOISE_SCALE = 0.003
TIME_SCALE = 0.005

positions = np.zeros((N_PARTICLES, 2))
colors = np.zeros((N_PARTICLES, 3))

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    py5.background(10, 15, 20)
    
    positions[:, 0] = np.random.uniform(0, SIZE[0], N_PARTICLES)
    positions[:, 1] = np.random.uniform(0, SIZE[1], N_PARTICLES)
    
    # Assign gradient colors (Gold to Crimson to Magenta)
    t_colors = np.random.uniform(0, 1, N_PARTICLES)
    
    # Gold (255, 215, 0), Crimson (220, 20, 60), Magenta (255, 0, 255)
    # Color interpolation based on t_colors
    for i in range(N_PARTICLES):
        tc = t_colors[i]
        if tc < 0.5:
            # Gold to Crimson
            ratio = tc * 2
            r = 255 * (1 - ratio) + 220 * ratio
            g = 215 * (1 - ratio) + 20 * ratio
            b = 0 * (1 - ratio) + 60 * ratio
        else:
            # Crimson to Magenta
            ratio = (tc - 0.5) * 2
            r = 220 * (1 - ratio) + 255 * ratio
            g = 20 * (1 - ratio) + 0 * ratio
            b = 60 * (1 - ratio) + 255 * ratio
        
        colors[i] = [r, g, b]

def get_curl_velocities(px, py, pz):
    e = 1.0
    
    # Calculate gradients of the noise field using vectorized py5.os_noise
    # Make sure inputs to py5.os_noise are float arrays
    n1 = py5.os_noise((px + e) * NOISE_SCALE, py * NOISE_SCALE, np.full_like(px, pz))
    n2 = py5.os_noise((px - e) * NOISE_SCALE, py * NOISE_SCALE, np.full_like(px, pz))
    n3 = py5.os_noise(px * NOISE_SCALE, (py + e) * NOISE_SCALE, np.full_like(px, pz))
    n4 = py5.os_noise(px * NOISE_SCALE, (py - e) * NOISE_SCALE, np.full_like(px, pz))
    
    dx = (n1 - n2) / (2 * e)
    dy = (n3 - n4) / (2 * e)
    
    # The curl of a 2D scalar field (0, 0, N) is (dy, -dx, 0)
    vx = dy * 20000.0  # Scale up the velocity
    vy = -dx * 20000.0
    
    return vx, vy

def draw():
    # Fading background for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(10, 15, 20, 12)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    global positions
    
    t = py5.frame_count * TIME_SCALE
    
    old_positions = positions.copy()
    
    # Get curl noise velocities
    vx, vy = get_curl_velocities(positions[:, 0], positions[:, 1], t)
    
    # Limit speed
    speeds = np.sqrt(vx**2 + vy**2)
    mask = speeds > MAX_SPEED
    vx[mask] = (vx[mask] / speeds[mask]) * MAX_SPEED
    vy[mask] = (vy[mask] / speeds[mask]) * MAX_SPEED
    
    positions[:, 0] += vx
    positions[:, 1] += vy
    
    # Wrap around boundaries
    positions[:, 0] = positions[:, 0] % py5.width
    positions[:, 1] = positions[:, 1] % py5.height
    
    # Draw trails
    dist = np.sqrt((positions[:, 0] - old_positions[:, 0])**2 + (positions[:, 1] - old_positions[:, 1])**2)
    valid = dist < MAX_SPEED * 2
    
    if np.any(valid):
        p1 = old_positions[valid]
        p2 = positions[valid]
        c = colors[valid]
        
        lines_array = np.column_stack((p1[:, 0], p1[:, 1], p2[:, 0], p2[:, 1]))
        
        py5.stroke_weight(2)
        # We can't batch draw lines with individual colors easily, so we use a generic blend color
        # that mimics the spectrum 
        py5.stroke(255, 100, 50, 40)
        py5.lines(lines_array)

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
