from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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

class Fungi:
    def __init__(self, x, z):
        self.x = x
        self.z = z
        self.segments = int(np.random.rand() * 5 + 5)
        self.heights = np.random.rand(self.segments) * 30 + 10
        self.angles = (np.random.rand(self.segments) - 0.5) * 0.5
        self.cap_size = np.random.rand() * 40 + 20
        self.phase = np.random.rand() * py5.TWO_PI
        
NUM_FUNGI = 40
fungi_list = []
spores = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global fungi_list, spores
    for _ in range(NUM_FUNGI):
        fungi_list.append(Fungi(
            np.random.randn() * 300,
            np.random.randn() * 300
        ))
        
    for _ in range(200):
        spores.append({
            "pos": [np.random.randn()*400, -np.random.rand()*600, np.random.randn()*400],
            "speed": np.random.rand() * 2 + 0.5,
            "phase": np.random.rand() * py5.TWO_PI
        })

def draw():
    py5.background(10, 8, 5) # Dark earthy brown
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.02
    
    py5.ambient_light(20, 30, 20)
    py5.directional_light(180, 100, 40, 0, 1, -1) # Cyan glow
    
    py5.translate(py5.width/2, py5.height/2 + 300, 0)
    
    py5.rotate_y(t * 0.2)
    py5.rotate_x(py5.PI/12)
    
    # Draw floor
    py5.push_matrix()
    py5.rotate_x(py5.PI/2)
    py5.no_stroke()
    py5.fill(15, 60, 15)
    py5.rect(-1000, -1000, 2000, 2000)
    py5.pop_matrix()
    
    # Draw Fungi
    for f in fungi_list:
        py5.push_matrix()
        py5.translate(f.x, 0, f.z)
        
        sway = np.sin(t + f.phase) * 0.1
        
        # Stalk
        py5.stroke(140, 80, 50) # Deep green
        py5.stroke_weight(10)
        py5.no_fill()
        
        # Draw segments
        py5.begin_shape()
        py5.vertex(0,0,0)
        curr_x, curr_y, curr_z = 0, 0, 0
        
        for i in range(f.segments):
            curr_y -= f.heights[i]
            curr_x += np.sin(f.angles[i] + sway) * f.heights[i]
            curr_z += np.cos(f.angles[i] + sway) * f.heights[i] * 0.5
            py5.vertex(curr_x, curr_y, curr_z)
        py5.end_shape()
        
        # Cap
        py5.translate(curr_x, curr_y, curr_z)
        py5.no_stroke()
        py5.fill(180, 80, 100 + np.sin(t*2+f.phase)*20, 90) # Cyan glowing cap
        py5.rotate_x(sway)
        
        # Simple cap shape using a flattened sphere
        py5.scale(1, 0.3, 1)
        py5.sphere(f.cap_size)
        
        py5.pop_matrix()
        
    # Draw spores
    py5.no_stroke()
    py5.fill(30, 80, 100, 80) # Warm orange
    
    for s in spores:
        s["pos"][1] -= s["speed"]
        s["pos"][0] += np.sin(t + s["phase"]) * 2
        s["pos"][2] += np.cos(t + s["phase"]) * 2
        
        if s["pos"][1] < -800:
            s["pos"][1] = 0
            
        py5.push_matrix()
        py5.translate(*s["pos"])
        py5.sphere(3)
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
            
        os._exit(0)

py5.run_sketch()
