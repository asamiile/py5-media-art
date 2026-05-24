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

# Grid resolution for math
W = int(SIZE[0] / 2)
H = int(SIZE[1] / 2)

x = np.linspace(-6, 6, W)
y = np.linspace(-6, 6, H)
X, Y = np.meshgrid(x, y)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    # Subtle blur instead of pure clear
    py5.push_matrix()
    py5.reset_matrix()
    py5.no_lights()
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 0, 0, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_matrix()

    time = py5.frame_count * 0.015
    
    # 5 interfering wave sources
    Z = np.zeros_like(X)
    for i in range(5):
        angle = i * np.pi / 5 + time * 0.05
        kx = np.cos(angle)
        ky = np.sin(angle)
        phase = time * (1.0 + i * 0.1)
        # Adding some spatial distortion (like a strange attractor field)
        Z += np.sin(X * kx * 2.5 + Y * ky * 2.5 + phase + 0.5 * np.sin(X * 0.5))
    
    # Z is a complex scalar field. We extract contour lines where sin(Z) is near 0.
    # This creates thick, glowing bands
    contour_mask = np.abs(np.sin(Z * 3.5)) < 0.1
    
    iy, ix = np.where(contour_mask)
    
    # Map back to screen coords
    px = ix * (py5.width / W) - (py5.width / 2)
    py = iy * (py5.height / H) - (py5.height / 2)
    pz = Z[contour_mask] * 40
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Orbit camera slowly
    py5.rotate_x(py5.PI / 4 + np.sin(time * 0.5) * 0.1)
    py5.rotate_z(time * 0.2)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(3)
    
    # Calculate colors based on Z height and time
    # To use different colors per point efficiently, we map HSB values
    hues = ((pz * 3 + time * 100) % 360).astype(int)
    
    # Render points
    py5.begin_shape(py5.POINTS)
    for i in range(len(px)):
        # Vivid chartreuse/teal to magenta
        py5.stroke(hues[i], 85, 90, 80)
        py5.vertex(px[i], py[i], pz[i])
    py5.end_shape()

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
