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

# Physics Parameters
NUM_PENDULUMS = 200000
G = 1.0 # Gravity
DT = 0.01
SUB_STEPS = 10 # 10 * 0.01 = 0.1 sim seconds per frame (90 sim seconds total)

# State vectors
# Initial state: almost horizontal, all identical except for microscopic noise
theta1 = np.full(NUM_PENDULUMS, np.pi * 0.5, dtype=np.float32)
theta2 = np.full(NUM_PENDULUMS, np.pi * 0.5, dtype=np.float32)

# Inject a tiny amount of uniform noise (1e-6) to seed the chaos
theta1 += np.random.uniform(-1e-6, 1e-6, NUM_PENDULUMS).astype(np.float32)
theta2 += np.random.uniform(-1e-6, 1e-6, NUM_PENDULUMS).astype(np.float32)

omega1 = np.zeros(NUM_PENDULUMS, dtype=np.float32)
omega2 = np.zeros(NUM_PENDULUMS, dtype=np.float32)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(5, 5, 10)

def draw():
    global theta1, theta2, omega1, omega2
    
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 10, 15) # Dark blue-grey fade
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    # Physics integration
    for _ in range(SUB_STEPS):
        delta = theta2 - theta1
        cos_delta = np.cos(delta)
        sin_delta = np.sin(delta)
        
        den = 2.0 - cos_delta * cos_delta
        
        # Calculate angular accelerations
        alpha1 = (omega1**2 * sin_delta * cos_delta +
                  G * np.sin(theta2) * cos_delta +
                  omega2**2 * sin_delta -
                  2.0 * G * np.sin(theta1)) / den
                  
        alpha2 = (-omega2**2 * sin_delta * cos_delta +
                  2.0 * (G * np.sin(theta1) * cos_delta -
                         omega1**2 * sin_delta -
                         G * np.sin(theta2))) / den
                         
        # Semi-implicit Euler
        omega1 += alpha1 * DT
        omega2 += alpha2 * DT
        theta1 += omega1 * DT
        theta2 += omega2 * DT

    # Render
    # Calculate positions
    # Scale length so the pendulums take up a good portion of the 4K screen
    L = SIZE[1] * 0.22 
    
    # Origin at the center of the screen
    cx, cy = SIZE[0] / 2, SIZE[1] / 2
    
    x1 = cx + L * np.sin(theta1)
    y1 = cy + L * np.cos(theta1)
    
    x2 = x1 + L * np.sin(theta2)
    y2 = y1 + L * np.cos(theta2)
    
    # Draw only the tip of the second pendulum
    # Color mapping based on momentum / velocity
    vel = np.sqrt(omega1**2 + omega2**2)
    
    # Fast = Cyan, Slow = Magenta
    # Vectorized drawing using Points
    pts = np.column_stack((x2, y2))
    
    py5.stroke_weight(2.0)
    
    # We can split the drawing into a few velocity buckets to give different colors
    fast_mask = vel > 6.0
    mid_mask = (vel <= 6.0) & (vel > 2.0)
    slow_mask = vel <= 2.0
    
    if np.any(fast_mask):
        py5.stroke(0, 255, 255, 30) # Cyan
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts[fast_mask])
        py5.end_shape()
        
    if np.any(mid_mask):
        py5.stroke(200, 100, 255, 30) # Purple
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts[mid_mask])
        py5.end_shape()
        
    if np.any(slow_mask):
        py5.stroke(255, 50, 150, 30) # Magenta
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts[slow_mask])
        py5.end_shape()

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
