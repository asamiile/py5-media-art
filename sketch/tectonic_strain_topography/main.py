"""
tectonic_strain_topography
==========================
A dynamic 3D topographic map showing shifting fault lines and stress accumulation, 
glowing in thermal reds and cool blues.

Format: Animation (15s @ 60fps)
"""

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
from lib.sizes import get_sizes

# ── Configuration ────────────────────────────────────────────────────────────
SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

W, H = SIZE
GW, GH = 300, 200
MESH_SCALE_X = 2500 / GW
MESH_SCALE_Z = 2500 / GH

z_base = np.zeros((GH, GW), dtype=np.float32)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate base terrain
    py5.noise_detail(4, 0.5)
    for y in range(GH):
        for x in range(GW):
            z_base[y, x] = (py5.noise(x * 0.02, y * 0.02) - 0.5) * 400.0

def draw():
    fc = py5.frame_count
    
    py5.background(10, 10, 15)
    
    py5.push_matrix()
    py5.translate(W/2, H/2 + 200, -800)
    py5.rotate_x(1.2)
    py5.rotate_z(fc * 0.005)
    
    py5.translate(-1250, -1250, 0)
    
    py5.ambient_light(40, 50, 80)
    py5.directional_light(255, 100, 50, 1, 0, -1)
    py5.directional_light(50, 100, 255, -1, 1, -1)
    
    py5.no_stroke()
    
    # Add dynamic fault shift
    fault_offset = np.sin(fc * 0.05) * 50.0
    
    for y in range(GH - 1):
        py5.begin_shape(py5.QUAD_STRIP)
        for x in range(GW):
            for r in (y, y + 1):
                # Fault line runs through middle
                fault_x = x - GW/2
                shift = fault_offset if fault_x > 0 else -fault_offset
                
                # Strain heat coloring
                strain = abs(shift) / 50.0
                cr = 50 + strain * 200
                cb = 200 - strain * 150
                cg = 50
                
                z_val = z_base[r, x]
                if abs(fault_x) < 5:
                    z_val -= 100 # Fault trench
                    cr, cg, cb = 255, 200, 50 # Glow
                
                py5.fill(cr, cg, cb, 250)
                py5.vertex(x * MESH_SCALE_X, r * MESH_SCALE_Z + shift, z_val)
        py5.end_shape()
    
    py5.pop_matrix()
    
    py5.fill(255)
    py5.text_size(32)
    py5.text(f"TECTONIC STRAIN MAP // FAULT SLIP: {fault_offset:.1f}m", 50, 50)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if fc % 60 == 0:
        print(f"[Render Progress] Frame {fc}/{TOTAL_FRAMES}")

    if fc >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        mid = TOTAL_FRAMES // 2
        shutil.copyfile(str(FRAMES_DIR / f"frame-{mid:04d}.png"), str(SKETCH_DIR / PREVIEW_FILENAME))
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
        import os
        os._exit(0)

if __name__ == "__main__":
    py5.run_sketch()
