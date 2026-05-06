from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
PARTICLE_COUNT = 120000
THROAT_RADIUS = 150
TUNNEL_LENGTH = 2000
STAR_COUNT = 5000

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, vel, colors, stars
    # Particles: [u, v, phase]
    # u: angle (0 to 2PI), v: longitudinal position (-3 to 3), phase: rotation offset
    u = np.random.uniform(0, 2 * np.pi, PARTICLE_COUNT)
    v = np.random.uniform(-4, 4, PARTICLE_COUNT)
    phase = np.random.uniform(0, 2 * np.pi, PARTICLE_COUNT)
    pos = np.stack([u, v, phase], axis=1)
    
    # Speed in v and u
    v_speed = np.random.uniform(0.01, 0.03, PARTICLE_COUNT)
    u_speed = np.random.uniform(0.02, 0.05, PARTICLE_COUNT)
    vel = np.stack([u_speed, v_speed], axis=1)
    
    # Static starfield in the background (far away)
    stars = np.random.uniform(-4000, 4000, (STAR_COUNT, 3))

def draw():
    py5.background(0, 0, 15)
    
    time_val = py5.frame_count / 60.0
    
    # Update particles
    pos[:, 0] += vel[:, 0] # Rotate
    pos[:, 1] += vel[:, 1] # Move forward
    
    # Wrap particles in v
    pos[pos[:, 1] > 4, 1] = -4
    
    # Hyperboloid mapping
    u_vals = pos[:, 0]
    v_vals = pos[:, 1]
    
    # Radius expands as we move away from the throat (v=0)
    # Using cosh(v) for hyperboloid of one sheet
    r = THROAT_RADIUS * np.cosh(v_vals)
    x = r * np.cos(u_vals)
    y = r * np.sin(u_vals)
    z = THROAT_RADIUS * np.sinh(v_vals)
    
    # Camera
    cam_z = (py5.frame_count * 5) % 2000 - 1000
    py5.camera(0, 0, cam_z, 0, 0, cam_z + 100, 0, 1, 0)
    
    # Render Starfield (only if far enough)
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        # Simple parallax stars
        py5.point(s[0], s[1], s[2] + cam_z)
        
    # Render Particles
    # Color by v (distance from throat)
    # Amethyst (#9966CC) at v=4, Cyan (#00FFFF) at v=0
    dist_from_throat = np.abs(v_vals)
    
    # HSB mapping
    # Cyan is ~180, Amethyst is ~270
    hues = 180 + (dist_from_throat / 4.0) * 90
    
    # Multi-pass rendering via points with varying alpha
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.begin_shape(py5.POINTS)
    for i in range(0, PARTICLE_COUNT, 2): # Render every 2nd for speed in preview
        v_abs = dist_from_throat[i]
        alpha = py5.lerp(255, 50, v_abs / 4.0)
        
        # Glow effect
        py5.stroke(hues[i], 80, 100, alpha * 0.5)
        py5.stroke_weight(2)
        py5.vertex(x[i], y[i], z[i])
        
        py5.stroke(hues[i], 40, 100, alpha)
        py5.stroke_weight(1)
        py5.vertex(x[i], y[i], z[i])
    py5.end_shape()
    
    # Additive core light at the center of the throat
    py5.push_matrix()
    py5.translate(0, 0, 0)
    py5.no_stroke()
    for i in range(4):
        r_glow = THROAT_RADIUS * (0.8 - i * 0.2)
        py5.fill(255, 255, 255, 40)
        py5.sphere(r_glow)
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "8M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
