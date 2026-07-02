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

GRID_RES = 60
SPACING = 25

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
def draw():
    py5.background(20, 22, 25) # Stark charcoal
    
    py5.directional_light(200, 200, 255, 1, 1, -1)
    py5.directional_light(255, 100, 200, -1, -1, 1)
    py5.ambient_light(50, 50, 70)
    
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    # Dynamic camera angle
    py5.rotate_x(np.pi/3 + np.sin(py5.frame_count * 0.01) * 0.1)
    py5.rotate_z(py5.frame_count * 0.005)
    
    offset = (GRID_RES - 1) * SPACING / 2
    py5.translate(-offset, -offset, 0)
    
    t = py5.frame_count * 0.05
    
    # Wave centers
    c1 = np.array([GRID_RES/3, GRID_RES/3])
    c2 = np.array([2*GRID_RES/3, 2*GRID_RES/3])
    
    for x in range(GRID_RES):
        for y in range(GRID_RES):
            
            p = np.array([x, y])
            d1 = np.linalg.norm(p - c1)
            d2 = np.linalg.norm(p - c2)
            
            # Interference of two waves
            w1 = np.sin(d1 * 0.5 - t)
            w2 = np.sin(d2 * 0.6 - t * 1.2)
            
            interference = w1 + w2
            
            # Add some glitch noise
            n = py5.os_noise(x * 0.2, y * 0.2, t * 0.5)
            if py5.random(1) < 0.01:
                interference += py5.random(-2, 2)
                
            z = interference * 80
            
            py5.push_matrix()
            py5.translate(x * SPACING, y * SPACING, z)
            
            amp = abs(interference)
            
            # Color based on amplitude
            if interference > 1.5:
                py5.fill(255, 20, 147) # Hot pink
            elif interference < -1.5:
                py5.fill(75, 0, 130) # Deep indigo
            else:
                c_val = int(100 + amp * 50)
                py5.fill(0, c_val, c_val + 50) # Quantum Cyan
                
            # Box size based on amplitude
            s = SPACING * (0.3 + 0.3 * amp)
            
            # Glitch scale
            if py5.random(1) < 0.005:
                py5.scale(1, 1, py5.random(2, 5))
                py5.fill(255)
                
            py5.box(s)
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
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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
