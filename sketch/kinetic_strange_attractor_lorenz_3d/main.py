from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Lorenz attractor constants
SIGMA = 10.0
RHO = 28.0
BETA = 8.0 / 3.0
DT = 0.005
NUM_PARTICLES = 30000

# Particles state (N, 3)
# Randomly distributed around the center
particles = np.random.uniform(-1.0, 1.0, (NUM_PARTICLES, 3)).astype(np.float32)
# Ensure they start somewhat close to the chaotic region
particles[:, 2] += 20.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    # Use additive blending for the glowing effect
    py5.blend_mode(py5.ADD)

def draw():
    global particles
    
    # We clear the background with a faint rect to leave trails
    # But for a clear additive effect without washing out, we might need a black background
    # Actually, blend_mode(ADD) accumulates to white fast. 
    # Let's switch back to blend_mode(BLEND) to draw a semi-transparent black rect, 
    # then switch back to ADD for particles.
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    # Lorenz equations using numpy
    x = particles[:, 0]
    y = particles[:, 1]
    z = particles[:, 2]
    
    dx = SIGMA * (y - x)
    dy = x * (RHO - z) - y
    dz = x * y - BETA * z
    
    new_x = x + dx * DT
    new_y = y + dy * DT
    new_z = z + dz * DT
    
    new_particles = np.column_stack((new_x, new_y, new_z))
    
    # Calculate velocity for color
    vel = np.linalg.norm(new_particles - particles, axis=1)
    vel_normalized = np.clip(vel / 2.0, 0, 1) # ~ max velocity
    
    # Hue: interpolate from cyan (180) to hot pink (320)
    hues = 180 + vel_normalized * 140
    
    # 2D Projection
    cam_angle = py5.frame_count * 0.005
    cos_a = np.cos(cam_angle)
    sin_a = np.sin(cam_angle)
    
    # Rotate around Y axis
    rot_x = particles[:, 0] * cos_a - particles[:, 2] * sin_a
    rot_z = particles[:, 0] * sin_a + particles[:, 2] * cos_a
    
    new_rot_x = new_particles[:, 0] * cos_a - new_particles[:, 2] * sin_a
    # We don't really need to compute new_rot_z if we just use orthogonal projection
    
    # Scale and center
    scale_fac = 25.0
    cx = py5.width / 2
    cy = py5.height / 2 + 300 # shifted down slightly because lorenz goes up
    
    proj_x = cx + rot_x * scale_fac
    proj_y = cy - particles[:, 1] * scale_fac # invert Y so it goes up
    
    new_proj_x = cx + new_rot_x * scale_fac
    new_proj_y = cy - new_particles[:, 1] * scale_fac
    
    # Draw particles as lines from old to new position for motion blur effect
    py5.stroke_weight(2)
    py5.begin_shape(py5.LINES)
    for i in range(NUM_PARTICLES):
        py5.stroke(hues[i], 90, 100, 40)
        py5.vertex(proj_x[i], proj_y[i])
        py5.vertex(new_proj_x[i], new_proj_y[i])
    py5.end_shape()
    
    particles = new_particles

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
        import os
        os._exit(0)

py5.run_sketch()
