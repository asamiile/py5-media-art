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

GRID_SIZE = 12
SPACING = 50

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    py5.sphere_detail(6)

def draw():
    py5.background(245, 245, 240) # Bone white
    
    py5.directional_light(255, 255, 255, 1, 1, -1)
    py5.directional_light(200, 200, 200, -1, -1, 1)
    py5.ambient_light(80, 80, 80)
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    py5.rotate_x(-np.pi/4 + py5.frame_count * 0.002)
    py5.rotate_y(np.pi/4 + py5.frame_count * 0.003)
    
    offset = (GRID_SIZE - 1) * SPACING / 2
    py5.translate(-offset, -offset, -offset)
    
    t = py5.frame_count * 0.02
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for z in range(GRID_SIZE):
                
                # Global noise phase for this lattice point
                n = py5.os_noise(x * 0.15, y * 0.15, z * 0.15 + t)
                
                py5.push_matrix()
                py5.translate(x * SPACING, y * SPACING, z * SPACING)
                
                # Chiral folding: rotate based on noise gradient
                angle = n * np.pi * 2
                
                py5.rotate_x(angle)
                py5.rotate_y(angle * 1.5)
                py5.rotate_z(angle * 0.5)
                
                # Folding scale
                s = 0.2 + 0.8 * (0.5 + 0.5 * np.sin(n * np.pi * 4))
                py5.scale(s)
                
                # Color logic
                if n > 0.6:
                    py5.fill(255, 215, 0) # Gold
                elif n < -0.3:
                    py5.fill(220, 20, 60) # Crimson
                else:
                    py5.fill(20, 20, 20) # Matte black
                    
                py5.box(SPACING * 0.7)
                py5.pop_matrix()
                
                # Draw connecting lines (hinges) occasionally
                if n > 0.2:
                    py5.stroke(20, 20, 20, 100)
                    py5.stroke_weight(2)
                    if x < GRID_SIZE - 1:
                        py5.line(x * SPACING, y * SPACING, z * SPACING,
                                 (x+1) * SPACING, y * SPACING, z * SPACING)
                    if y < GRID_SIZE - 1:
                        py5.line(x * SPACING, y * SPACING, z * SPACING,
                                 x * SPACING, (y+1) * SPACING, z * SPACING)
                    if z < GRID_SIZE - 1:
                        py5.line(x * SPACING, y * SPACING, z * SPACING,
                                 x * SPACING, y * SPACING, (z+1) * SPACING)
                    py5.no_stroke()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
