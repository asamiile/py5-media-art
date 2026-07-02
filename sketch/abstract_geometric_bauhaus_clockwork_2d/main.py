import os
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
FINAL_VIDEO = SKETCH_DIR / f"{WORK_NAME}.mp4"

DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Bauhaus Palette
PALETTE = [
    "#E32636", # Alizarin Crimson (Red)
    "#0033A0", # Deep Blue
    "#FFD100", # Bauhaus Yellow
    "#1C1C1C", # Near Black
]
BG_COLOR = "#F4F0E6" # Off-white parchment

class Gear:
    def __init__(self, x, y, radius, speed, depth, max_depth):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.depth = depth
        self.children = []
        
        # Decide what geometric shape this gear represents
        self.shape_type = np.random.choice(['circle', 'semi', 'arc', 'cross'])
        self.color = np.random.choice(PALETTE)
        self.stroke_weight = np.random.uniform(5, 20)
        
        # Generate children if not at max depth
        if depth < max_depth:
            num_children = np.random.randint(1, 4)
            for _ in range(num_children):
                # Child sits on the rim of the parent
                angle = np.random.uniform(0, 2 * np.pi)
                child_r = self.radius * np.random.uniform(0.4, 0.8)
                child_x = np.cos(angle) * (self.radius + child_r * 0.1) # slight overlap
                child_y = np.sin(angle) * (self.radius + child_r * 0.1)
                
                # Gear ratio speed
                child_speed = -self.speed * (self.radius / child_r) * np.random.choice([0.5, 1.0, 2.0])
                
                self.children.append(Gear(child_x, child_y, child_r, child_speed, depth + 1, max_depth))

    def draw(self, t):
        py5.push_matrix()
        
        # Translate to position
        py5.translate(self.x, self.y)
        
        # Rotate based on time and speed
        rotation = t * self.speed
        py5.rotate(rotation)
        
        # Draw the primitive shape
        py5.stroke(self.color)
        py5.stroke_weight(self.stroke_weight)
        py5.no_fill()
        
        if self.shape_type == 'circle':
            # Solid filled circle occasionally
            if np.random.random() < 0.3:
                py5.fill(self.color)
                py5.no_stroke()
            py5.ellipse(0, 0, self.radius * 2, self.radius * 2)
            
            # Draw a spoke to show rotation
            py5.stroke(PALETTE[-1])
            py5.line(0, 0, self.radius, 0)
            
        elif self.shape_type == 'semi':
            py5.fill(self.color)
            py5.no_stroke()
            py5.arc(0, 0, self.radius * 2, self.radius * 2, 0, np.pi)
            
        elif self.shape_type == 'arc':
            py5.stroke_cap(py5.SQUARE)
            py5.arc(0, 0, self.radius * 2, self.radius * 2, 0, np.pi * 1.5)
            
        elif self.shape_type == 'cross':
            py5.line(-self.radius, 0, self.radius, 0)
            py5.line(0, -self.radius, 0, self.radius)

        # Draw children
        for child in self.children:
            child.draw(t)
            
        py5.pop_matrix()

# Global variables
root_gears = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize the clockwork mechanism
    # Create several large root hubs across the screen
    np.random.seed(42) # fixed seed for repeatable mechanism layout
    for _ in range(5):
        rx = np.random.uniform(0, SIZE[0])
        ry = np.random.uniform(0, SIZE[1])
        rr = np.random.uniform(200, 600)
        rs = np.random.uniform(-0.5, 0.5)
        root_gears.append(Gear(rx, ry, rr, rs, 0, 4))

def draw():
    py5.background(BG_COLOR)
    
    t = py5.frame_count / TOTAL_FRAMES * 2 * np.pi
    
    # We want a smooth loop, so rotation must complete integer multiples of 2PI
    # Gear speeds are arbitrary, to force a perfect loop we could lock them to integers
    # However, since we used random gear ratios, a perfect loop is mathematically impossible
    # without forcing speeds.
    # Let's dynamically force the speeds to be integers now
    # Actually, the user doesn't strictly demand seamless loops unless specified, 
    # but the prompt says 15s animation. We'll just let it spin dynamically.
    
    for gear in root_gears:
        gear.draw(t)

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
        
        import os
        os._exit(0)

if __name__ == '__main__':
    py5.run_sketch()
