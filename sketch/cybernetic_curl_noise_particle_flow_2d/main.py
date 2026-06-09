from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PARTICLES = 150000
# Split into three groups for cyan, magenta, and yellow
P_EACH = NUM_PARTICLES // 3

pos_c = np.random.rand(P_EACH, 2) * [SIZE[0], SIZE[1]]
pos_m = np.random.rand(P_EACH, 2) * [SIZE[0], SIZE[1]]
pos_y = np.random.rand(P_EACH, 2) * [SIZE[0], SIZE[1]]

def get_curl(p, t, speed, scale):
    x = p[:, 0] * scale
    y = p[:, 1] * scale
    
    # Derivative of some pseudo-noise field to get divergence-free curl
    # Phi(x,y) = sin(x + t) * cos(y - t) + sin(x*2.1)*cos(y*1.7)
    # u = dPhi/dy, v = -dPhi/dx
    
    u = -np.sin(x + t*speed) * np.sin(y - t*speed) - 1.7 * np.sin(x*2.1) * np.sin(y*1.7)
    v = -np.cos(x + t*speed) * np.cos(y - t*speed) - 2.1 * np.cos(x*2.1) * np.cos(y*1.7)
    
    return np.column_stack((u, v))

def wrap_edges(p):
    p[:, 0] %= SIZE[0]
    p[:, 1] %= SIZE[1]

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 10, 15)

def draw():
    # Fade previous frame
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 10, 15, 12)  # Slight trail fade
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    global pos_c, pos_m, pos_y
    
    # Update positions
    # Cyan moves fast and wide
    pos_c += get_curl(pos_c, t, 1.0, 0.002) * 5.0
    wrap_edges(pos_c)
    
    # Magenta moves medium
    pos_m += get_curl(pos_m, t, 1.5, 0.004) * 4.0
    wrap_edges(pos_m)
    
    # Yellow moves tight and slow
    pos_y += get_curl(pos_y, t, 0.5, 0.008) * 3.0
    wrap_edges(pos_y)
    
    py5.stroke_weight(2)
    
    # Draw Cyan
    py5.stroke(0, 200, 255, 100)
    py5.points(pos_c)
    
    # Draw Magenta
    py5.stroke(255, 0, 200, 100)
    py5.points(pos_m)
    
    # Draw Yellow
    py5.stroke(255, 200, 0, 100)
    py5.points(pos_y)

    py5.blend_mode(py5.BLEND)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
