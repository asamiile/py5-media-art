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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_spores = 3000
spores = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(5)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    
    for _ in range(num_spores):
        spawn_spore()

def spawn_spore():
    x = py5.random(-py5.width, py5.width)
    y = py5.random(-py5.height, py5.height)
    z = py5.random(-1000, 500)
    vx = 0
    vy = 0
    vz = 0
    size = py5.random(2, 12)
    hue = py5.random(120, 200) # greens and cyans
    spores.append([x, y, z, vx, vy, vz, size, hue])

def draw():
    py5.background(5, 5, 10)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Camera drifts forward
    py5.translate(0, 0, py5.frame_count * 5)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.005
    
    for s in spores:
        x, y, z, vx, vy, vz, size, hue = s
        
        # Noise field
        nx = py5.os_noise(x * 0.002, y * 0.002, z * 0.002 + t)
        ny = py5.os_noise(x * 0.002 + 100, y * 0.002 + 100, z * 0.002 + t)
        nz = py5.os_noise(x * 0.002 + 200, y * 0.002 + 200, z * 0.002 + t)
        
        ax = py5.remap(nx, 0, 1, -0.5, 0.5)
        ay = py5.remap(ny, 0, 1, -0.5, 0.5)
        az = py5.remap(nz, 0, 1, -0.5, 0.5)
        
        s[3] = (vx + ax) * 0.95
        s[4] = (vy + ay) * 0.95
        s[5] = (vz + az) * 0.95
        
        s[0] += s[3]
        s[1] += s[4]
        s[2] += s[5]
        
        # Wrapping
        if s[0] > py5.width: s[0] -= py5.width * 2
        if s[0] < -py5.width: s[0] += py5.width * 2
        if s[1] > py5.height: s[1] -= py5.height * 2
        if s[1] < -py5.height: s[1] += py5.height * 2
        
        # Draw spore with glowing aura
        py5.push_matrix()
        py5.translate(s[0], s[1], s[2])
        
        # core
        py5.fill(hue, 80, 100, 90)
        py5.sphere(size * 0.5)
        
        # aura
        py5.fill(hue, 90, 80, 20)
        py5.sphere(size * 2)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES}")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
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
