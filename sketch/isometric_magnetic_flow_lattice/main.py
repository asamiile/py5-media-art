from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle State
num_particles = 1500
positions = None
velocities = None
lifetimes = None

def setup():
    global positions, velocities, lifetimes
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    import numpy as np
    positions = np.random.rand(num_particles, 3) * 1000 - 500
    velocities = np.zeros((num_particles, 3))
    lifetimes = np.random.randint(50, 150, num_particles)

def draw():
    global positions, velocities, lifetimes
    import numpy as np
    
    # Motion Blur
    py5.push_style()
    py5.fill(0, 0, 0, 30)
    py5.no_stroke()
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.rect(0, 0, py5.width, py5.height)
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.pop_style()

    t = py5.frame_count * 0.015
    
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, -200)
    # Isometric camera setup
    py5.rotate_x(py5.asin(1 / py5.sqrt(3)))
    py5.rotate_y(py5.QUARTER_PI + t * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    py5.stroke_weight(2)
    
    grid_snap = 20.0
    
    for i in range(num_particles):
        px, py, pz = positions[i]
        
        # Magnetic vector field using Perlin noise
        nx = py5.noise(px * 0.002, py * 0.002, t) - 0.5
        ny = py5.noise(py * 0.002, pz * 0.002, t + 10) - 0.5
        nz = py5.noise(pz * 0.002, px * 0.002, t + 20) - 0.5
        
        # Constrain movement to cardinal axes to make it "isometric/lattice-like"
        if abs(nx) > abs(ny) and abs(nx) > abs(nz):
            velocities[i] = [np.sign(nx) * 5, 0, 0]
        elif abs(ny) > abs(nz):
            velocities[i] = [0, np.sign(ny) * 5, 0]
        else:
            velocities[i] = [0, 0, np.sign(nz) * 5]
            
        new_px = px + velocities[i][0]
        new_py = py + velocities[i][1]
        new_pz = pz + velocities[i][2]
        
        # Colors
        if i % 3 == 0:
            py5.stroke(0, 255, 255, 180) # Cyan
        elif i % 3 == 1:
            py5.stroke(255, 0, 255, 180) # Magenta
        else:
            py5.stroke(255, 200, 0, 180) # Gold
            
        py5.line(px, py, pz, new_px, new_py, new_pz)
        
        positions[i] = [new_px, new_py, new_pz]
        lifetimes[i] -= 1
        
        # Reset dead particles
        if lifetimes[i] <= 0 or abs(new_px) > 600 or abs(new_py) > 600 or abs(new_pz) > 600:
            positions[i] = np.random.rand(3) * 1000 - 500
            lifetimes[i] = np.random.randint(50, 150)
            
    py5.blend_mode(py5.BLEND)
    py5.pop_matrix()

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
