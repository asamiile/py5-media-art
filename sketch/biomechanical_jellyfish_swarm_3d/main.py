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

class Jellyfish:
    def __init__(self):
        self.pos = np.array([
            (np.random.rand() - 0.5) * 2000,
            (np.random.rand() - 0.5) * 2000,
            (np.random.rand() - 0.5) * 2000
        ])
        self.speed = np.random.rand() * 2 + 1.0
        self.size = np.random.rand() * 50 + 20
        self.phase_offset = np.random.rand() * py5.TWO_PI
        self.tentacles = int(np.random.rand() * 6 + 4)
        
    def update(self, t):
        # Swim upwards
        self.pos[1] -= self.speed + np.sin(t*3 + self.phase_offset) * 2
        # Slight drift
        self.pos[0] += np.sin(t*0.5 + self.phase_offset)
        self.pos[2] += np.cos(t*0.5 + self.phase_offset)
        
        # Wrap vertically
        if self.pos[1] < -1500:
            self.pos[1] = 1500

NUM_JELLIES = 150
jellies = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global jellies
    for _ in range(NUM_JELLIES):
        jellies.append(Jellyfish())

def draw():
    py5.background(5, 5, 20) # Deep sea blue/black
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2, 0)
    py5.rotate_y(t * 0.2)
    py5.rotate_x(py5.PI/12)
    
    py5.blend_mode(py5.ADD)
    
    for j in jellies:
        j.update(t)
        
        py5.push_matrix()
        py5.translate(*j.pos)
        
        # Depth fade
        dist = np.sqrt(j.pos[0]**2 + j.pos[1]**2 + j.pos[2]**2)
        alpha = py5.remap(dist, 0, 1500, 80, 0)
        
        if alpha > 0:
            swim_cycle = np.sin(t*3 + j.phase_offset)
            
            # Draw bell (wireframe half sphere using lines)
            py5.no_fill()
            py5.stroke(180, 80, 100, alpha) # Cyan
            py5.stroke_weight(2)
            
            # Draw a simplified wireframe bell
            bell_radius = j.size + swim_cycle * j.size * 0.2
            bell_height = j.size * 0.8
            
            py5.begin_shape(py5.LINES)
            segments = 8
            for i in range(segments):
                angle1 = (py5.TWO_PI / segments) * i
                angle2 = (py5.TWO_PI / segments) * ((i+1)%segments)
                
                # Top to rim
                py5.vertex(0, -bell_height, 0)
                py5.vertex(np.cos(angle1)*bell_radius, 0, np.sin(angle1)*bell_radius)
                
                # Rim loop
                py5.vertex(np.cos(angle1)*bell_radius, 0, np.sin(angle1)*bell_radius)
                py5.vertex(np.cos(angle2)*bell_radius, 0, np.sin(angle2)*bell_radius)
            py5.end_shape()
            
            # Draw tentacles
            py5.stroke(280, 80, 90, alpha * 0.8) # Purple tentacles
            py5.stroke_weight(1.5)
            
            for i in range(j.tentacles):
                angle = (py5.TWO_PI / j.tentacles) * i
                py5.push_matrix()
                # Start at rim
                start_x = np.cos(angle)*bell_radius * 0.5
                start_z = np.sin(angle)*bell_radius * 0.5
                py5.translate(start_x, 0, start_z)
                
                # Draw trailing tentacle
                py5.begin_shape()
                segments_t = 15
                for s in range(segments_t):
                    tx = np.sin(t*2 + s*0.2 + j.phase_offset + angle) * 10
                    tz = np.cos(t*2 + s*0.2 + j.phase_offset + angle) * 10
                    ty = s * (j.size * 0.3)
                    py5.vertex(tx, ty, tz)
                py5.end_shape()
                
                py5.pop_matrix()

        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)

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
