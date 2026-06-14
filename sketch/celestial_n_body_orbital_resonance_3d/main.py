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

# Physics variables
num_particles = 3000
positions = None
velocities = None
masses = None
attractors = None

def setup():
    global positions, velocities, masses, attractors
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize N-body
    positions = np.random.randn(num_particles, 3) * 500
    positions[:, 2] *= 0.1 # Flatter disk
    
    # Initial velocity perpendicular to center to orbit
    r = np.linalg.norm(positions, axis=1, keepdims=True) + 1e-5
    v_dir = np.cross(positions, np.array([[0, 0, 1]]))
    v_dir = v_dir / (np.linalg.norm(v_dir, axis=1, keepdims=True) + 1e-5)
    velocities = v_dir * 15.0 * (1000 / r)
    
    masses = np.ones((num_particles, 1))
    
    # Set up 3 heavy central attractors in a triangle to create resonance
    R = 400
    attractors = np.array([
        [R*np.cos(0), R*np.sin(0), 0],
        [R*np.cos(2*np.pi/3), R*np.sin(2*np.pi/3), 0],
        [R*np.cos(4*np.pi/3), R*np.sin(4*np.pi/3), 0]
    ])

def draw():
    global positions, velocities
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width/2, py5.height/2, -1000)
    
    # Rotate the whole scene slowly
    py5.rotate_x(py5.frame_count * 0.002)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_z(py5.frame_count * 0.001)
    
    G = 80000.0
    dt = 0.05
    
    # Physics step
    forces = np.zeros_like(positions)
    for attr in attractors:
        diff = attr - positions
        dist_sq = np.sum(diff**2, axis=1, keepdims=True) + 5000.0 # Softening
        f = G * diff / (dist_sq * np.sqrt(dist_sq))
        forces += f
        
    velocities += forces * dt
    positions += velocities * dt
    
    py5.stroke_weight(2)
    
    # Color based on speed
    speeds = np.linalg.norm(velocities, axis=1)
    
    py5.begin_shape(py5.POINTS)
    for i in range(num_particles):
        s = speeds[i]
        if s > 40:
            py5.stroke(0, 255, 255, 30) # Cyan
        elif s > 20:
            py5.stroke(255, 150, 0, 20) # Amber
        else:
            py5.stroke(0, 50, 150, 10) # Navy
            
        py5.vertex(positions[i, 0], positions[i, 1], positions[i, 2])
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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
