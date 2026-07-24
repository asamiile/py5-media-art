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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Physics parameters
NUM_PENDULUMS = 5000
G = 0.05
FRICTION = 0.005
MAGNET_STRENGTH = 25.0
H_DIST = 100.0 # Height of pendulum above magnets (prevents singularity)
DT = 0.5

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global pos, old_pos, vel, magnets, colors
    
    W, H = SIZE
    
    # 5 Magnets arranged in a pentagon
    magnets = []
    r_mag = H * 0.35
    for i in range(5):
        angle = i * py5.TWO_PI / 5 - py5.HALF_PI
        magnets.append([W/2 + r_mag * np.cos(angle), H/2 + r_mag * np.sin(angle)])
    magnets = np.array(magnets)
    
    # Initialize pendulums tightly clustered around center
    pos = np.zeros((NUM_PENDULUMS, 2))
    theta = np.random.uniform(0, py5.TWO_PI, NUM_PENDULUMS)
    r = np.random.uniform(0, H * 0.2, NUM_PENDULUMS)
    pos[:, 0] = W/2 + r * np.cos(theta)
    pos[:, 1] = H/2 + r * np.sin(theta)
    
    old_pos = pos.copy()
    vel = np.zeros((NUM_PENDULUMS, 2))
    
    # Colors based on initial angles
    colors = np.zeros((NUM_PENDULUMS, 4))
    colors[:, 0] = (theta / py5.TWO_PI * 360) % 360 # Hue
    colors[:, 1] = 80 # Sat
    colors[:, 2] = 100 # Bri
    colors[:, 3] = 40 # Alpha

def draw():
    global pos, old_pos, vel
    
    # Motion fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    W, H = SIZE
    center = np.array([W/2, H/2])
    
    # Physics step (sub-stepping for stability)
    for _ in range(4):
        acc = np.zeros_like(pos)
        
        # Central gravity pulling to center
        diff_c = center - pos
        acc += diff_c * G
        
        # Magnetic forces
        for m in magnets:
            diff_m = m - pos
            dist_sq = np.sum(diff_m**2, axis=-1, keepdims=True)
            # Force = strength * r / (r^2 + h^2)^(3/2)
            denom = (dist_sq + H_DIST**2)**1.5
            acc += diff_m * (MAGNET_STRENGTH / denom)
            
        # Friction
        acc -= vel * FRICTION
        
        # Update
        vel += acc * DT
        pos += vel * DT
        
    # Draw trajectories
    py5.stroke_weight(1)
    
    # In Python loops, drawing 5,000 points is very fast.
    py5.begin_shape(py5.POINTS)
    for i in range(NUM_PENDULUMS):
        py5.stroke(colors[i, 0], colors[i, 1], colors[i, 2], colors[i, 3])
        py5.vertex(pos[i, 0], pos[i, 1])
    py5.end_shape()

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
