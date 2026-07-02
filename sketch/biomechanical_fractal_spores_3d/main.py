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

# Parameters
NUM_SPORES = 25
BASE_RADIUS = 30

# State
spores = []
for _ in range(NUM_SPORES):
    x = np.random.uniform(-400, 400)
    y = np.random.uniform(-400, 400)
    z = np.random.uniform(-400, 400)
    spores.append({
        'pos': np.array([x, y, z]),
        'vel': np.random.uniform(-2, 2, 3),
        'phase': np.random.uniform(0, np.pi * 2),
        'scale': np.random.uniform(0.5, 1.5)
    })

def draw_fractal_spore(depth, radius):
    if depth == 0:
        return
        
    py5.sphere(radius)
    
    num_branches = 4
    for i in range(num_branches):
        py5.push_matrix()
        angle = (py5.frame_count * 0.02) + (i * np.pi * 2 / num_branches)
        py5.rotate_y(angle)
        py5.rotate_x(angle * 0.5)
        py5.translate(radius * 1.5, 0, 0)
        draw_fractal_spore(depth - 1, radius * 0.4)
        py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    py5.sphere_detail(12)

def draw():
    py5.background(5, 10, 20)
    
    # Lighting
    py5.ambient_light(20, 40, 50)
    py5.point_light(0, 255, 255, py5.width/2, py5.height/2, 200) # Cyan
    py5.point_light(50, 255, 50, 0, 0, -200) # Neon green
    py5.point_light(255, 150, 200, py5.width, py5.height, -200) # Pale pink
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.002)
    
    # Update and draw spores
    for i, spore in enumerate(spores):
        # Movement
        spore['pos'] += spore['vel']
        
        # Soft boundaries
        for axis in range(3):
            if abs(spore['pos'][axis]) > 500:
                spore['vel'][axis] *= -1
                spore['pos'][axis] = np.clip(spore['pos'][axis], -500, 500)
                
        # Gentle swirling force using noise
        nx = py5.os_noise(spore['pos'][0]*0.002, spore['pos'][1]*0.002, py5.frame_count*0.01) * 2 - 1
        ny = py5.os_noise(spore['pos'][1]*0.002, spore['pos'][2]*0.002, py5.frame_count*0.01) * 2 - 1
        nz = py5.os_noise(spore['pos'][2]*0.002, spore['pos'][0]*0.002, py5.frame_count*0.01) * 2 - 1
        
        spore['vel'] += np.array([nx, ny, nz]) * 0.05
        
        # Speed limit
        speed = np.linalg.norm(spore['vel'])
        if speed > 3.0:
            spore['vel'] = (spore['vel'] / speed) * 3.0
            
        # Draw
        py5.push_matrix()
        py5.translate(*spore['pos'])
        
        # Breathing scale
        breathe = 1.0 + 0.1 * np.sin(py5.frame_count * 0.05 + spore['phase'])
        py5.scale(spore['scale'] * breathe)
        
        # Material
        if i % 3 == 0:
            py5.emissive(0, 100, 100) # Cyan glow
            py5.fill(20, 200, 255, 200)
        elif i % 3 == 1:
            py5.emissive(0, 100, 0) # Green glow
            py5.fill(100, 255, 50, 200)
        else:
            py5.emissive(100, 50, 50) # Pink glow
            py5.fill(255, 150, 200, 200)
            
        # Slowly rotate individual spore
        py5.rotate_x(py5.frame_count * 0.01 + spore['phase'])
        py5.rotate_y(py5.frame_count * 0.015 + spore['phase'])
        
        draw_fractal_spore(3, BASE_RADIUS)
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
