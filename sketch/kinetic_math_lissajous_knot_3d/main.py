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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 0, 20) # dark purple
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / FPS
    
    # Parametric equations for Lissajous knot
    nx = 3
    ny = 2
    nz = 5
    
    # Phase shift over time for a seamless loop (if nz*phase_z hits 2pi)
    phase_z = t * 2.0 * np.pi / DURATION_SEC
    
    num_pts = 2000
    u = np.linspace(0, 2*np.pi, num_pts)
    
    x = np.sin(nx * u)
    y = np.cos(ny * u)
    z = np.sin(nz * u + phase_z)
    
    # Rotate
    rot_y = t * 0.5
    rot_x = t * 0.3
    
    cy, sy = np.cos(rot_y), np.sin(rot_y)
    cx, sx = np.cos(rot_x), np.sin(rot_x)
    
    Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    
    pts = np.vstack((x, y, z)).T
    rotated = pts @ Ry.T @ Rx.T
    
    radius = min(SIZE) * 0.4
    z_offset = 2.5
    
    scale = radius * 3.0 / (rotated[:, 2] + z_offset)
    
    x2d = rotated[:, 0] * scale + SIZE[0] / 2
    y2d = rotated[:, 1] * scale + SIZE[1] / 2
    
    # Separate loops for stroke weights to mimic neon glow
    for w, a in [(15, 20), (6, 60), (2, 200)]:
        py5.stroke_weight(w)
        py5.no_fill()
        py5.begin_shape()
        for i in range(num_pts):
            c_val = i / num_pts
            r = int(255 * (1 - c_val))
            g = 255
            b = int(255 * c_val)
            py5.stroke(r, g, b, a)
            py5.vertex(x2d[i], y2d[i])
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
