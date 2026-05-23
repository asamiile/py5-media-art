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
DURATION_SEC = 3
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_PARTICLES = 150000

# Global states
pos = None
vel = None
age = None
life = None
kind = None

def setup():
    global pos, vel, age, life, kind
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.background(5, 10, 20)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    pos = np.random.rand(NUM_PARTICLES, 2).astype(np.float32)
    pos[:, 0] *= py5.width
    pos[:, 1] *= py5.height
    
    vel = np.zeros((NUM_PARTICLES, 2), dtype=np.float32)
    age = np.random.rand(NUM_PARTICLES).astype(np.float32) * 100
    life = np.random.rand(NUM_PARTICLES).astype(np.float32) * 100 + 50
    kind = np.random.randint(0, 2, NUM_PARTICLES).astype(np.int32) # 0 = salt, 1 = thermal

def draw():
    global pos, vel, age, life, kind
    
    # Fade background
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 10, 20, 25)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / 120.0
    
    # Simulate salt finger instability flow field
    # We create a periodic field with falling and rising plumes
    x_norm = pos[:, 0] / py5.width * 20.0 # 20 fingers across
    y_norm = pos[:, 1] / py5.height * 10.0
    
    # Vertical advection based on horizontal position (fingers)
    # Fingers shift slowly
    finger_phase = np.sin(x_norm * np.pi + t) * np.cos(y_norm * 0.5 - t)
    
    vy = np.sin(x_norm * 2 * np.pi + np.sin(y_norm + t)) * 3.0
    vx = np.cos(x_norm * 2 * np.pi) * np.sin(y_norm * np.pi) * 1.5
    
    # Buoyancy: kind 0 (salt) falls, kind 1 (thermal) rises
    buoyancy = np.where(kind == 0, 1.5, -1.5)
    
    vel[:, 0] = vel[:, 0] * 0.9 + vx * 0.1
    vel[:, 1] = vel[:, 1] * 0.9 + (vy + buoyancy) * 0.1
    
    pos += vel
    age += 1
    
    # Wrap horizontally
    pos[:, 0] %= py5.width
    
    # Respawn vertically or if old
    dead = (age > life) | (pos[:, 1] < -50) | (pos[:, 1] > py5.height + 50)
    num_dead = np.sum(dead)
    if num_dead > 0:
        pos[dead, 0] = np.random.rand(num_dead) * py5.width
        # Salt respawns at top, thermal at bottom
        pos[dead, 1] = np.where(kind[dead] == 0, 
                                np.random.rand(num_dead) * 50 - 50, 
                                py5.height + np.random.rand(num_dead) * 50)
        vel[dead] = 0
        age[dead] = 0
        life[dead] = np.random.rand(num_dead) * 100 + 50
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    salt_mask = kind == 0
    therm_mask = kind == 1
    
    # Salt fingers (cyan)
    if np.any(salt_mask):
        py5.stroke(20, 200, 255, 60)
        py5.points(pos[salt_mask])
        
    # Thermal plumes (gold)
    if np.any(therm_mask):
        py5.stroke(255, 180, 50, 60)
        py5.points(pos[therm_mask])

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

if __name__ == '__main__':
    py5.run_sketch()
