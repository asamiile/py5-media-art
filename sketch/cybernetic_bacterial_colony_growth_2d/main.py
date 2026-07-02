from pathlib import Path
import shutil
import subprocess
import sys
import random
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

agents = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(10, 5, 5)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    for _ in range(50):
        agents.append([py5.width/2 + py5.random(-50, 50), py5.height/2 + py5.random(-50, 50), py5.random(py5.TWO_PI), 100, 0])

def draw():
    py5.push_style()
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 5, 5, 2)
    py5.rect(0, 0, py5.width, py5.height)
    py5.pop_style()
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    new_agents = []
    
    for a in agents:
        x, y, angle, energy, age = a
        
        speed = 2.5
        nx = x + py5.cos(angle) * speed
        ny = y + py5.sin(angle) * speed
        
        angle += py5.random(-0.4, 0.4)
        
        h = py5.remap(age, 0, 150, 70, -30)
        if h < 0: h += 360
        if age > 130: h = 180
        
        py5.stroke(h, 90, 80, 50)
        py5.line(x, y, nx, ny)
        
        a[0] = nx
        a[1] = ny
        a[2] = angle
        a[3] = energy - 1
        a[4] = age + 1
        
        if a[3] > 0 and py5.random(1) < 0.03 and len(agents) + len(new_agents) < 8000:
            new_agents.append([nx, ny, angle + py5.random(0.5, 1.5) * (1 if py5.random(1)>0.5 else -1), 100 + py5.random(-20, 20), 0])
            a[3] -= 30
            
    agents[:] = [a for a in agents if a[3] > 0 and 0 < a[0] < py5.width and 0 < a[1] < py5.height]
    agents.extend(new_agents)
    
    if len(agents) < 10 and py5.frame_count < TOTAL_FRAMES - 120:
        for _ in range(30):
            agents.append([py5.random(py5.width), py5.random(py5.height), py5.random(py5.TWO_PI), 100, 0])

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
