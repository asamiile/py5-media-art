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

MAX_CRACKS = 6000
W, H = SIZE
# Grid to track line positions for collisions (int 0-359 angles, -1 for empty)
cgrid = np.full((H, W), -1, dtype=np.int16)

class Crack:
    def __init__(self, x=None, y=None, angle=None):
        if x is None:
            self.x = np.random.randint(0, W)
            self.y = np.random.randint(0, H)
            self.angle = np.random.randint(0, 360)
        else:
            self.x = x
            self.y = y
            self.angle = angle
            
        # Add some slight organic drift to the straight angles occasionally
        self.active = True
        
        # Look for empty space
        for _ in range(100):
            if cgrid[int(self.y), int(self.x)] < 0:
                break
            self.x = np.random.randint(0, W)
            self.y = np.random.randint(0, H)
            
        # Color based on angle
        if (self.angle // 90) % 2 == 0:
            self.color = py5.color(240, 248, 255, 180)  # Silver/frost
        else:
            if np.random.rand() > 0.8:
                self.color = py5.color(255, 215, 0, 220)  # Gold
            else:
                self.color = py5.color(0, 206, 209, 150)  # Cyan
                
    def step(self):
        if not self.active:
            return
            
        cx = self.x + 1.2 * np.cos(np.radians(self.angle))
        cy = self.y + 1.2 * np.sin(np.radians(self.angle))
        
        # Check bounds
        if cx < 0 or cx >= W or cy < 0 or cy >= H:
            self.active = False
            return
            
        idx = int(cx)
        idy = int(cy)
        
        # Check collision
        if cgrid[idy, idx] >= 0 and cgrid[idy, idx] != self.angle:
            self.active = False
            # Try to spawn children at the collision point
            if len(cracks) < MAX_CRACKS and np.random.rand() < 0.6:
                # Turn 90 degrees left or right
                new_angle = (self.angle + (90 if np.random.rand() > 0.5 else -90)) % 360
                cracks.append(Crack(cx, cy, new_angle))
            return
            
        # Move
        py5.stroke(self.color)
        py5.stroke_weight(1.2)
        py5.line(self.x, self.y, cx, cy)
        
        self.x = cx
        self.y = cy
        cgrid[idy, idx] = self.angle
        
        # Random spawn along the path
        if np.random.rand() < 0.005 and len(cracks) < MAX_CRACKS:
            new_angle = (self.angle + (90 if np.random.rand() > 0.5 else -90)) % 360
            cracks.append(Crack(self.x, self.y, new_angle))

cracks = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.background(10, 10, 12)  # Obsidian
    
    # Initial seeds
    for _ in range(50):
        cracks.append(Crack())
        
def draw():
    # Execute multiple steps per frame to speed up the visual growth
    for _ in range(25):
        for c in cracks:
            c.step()
            
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%) | Cracks: {len(cracks)}")

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
