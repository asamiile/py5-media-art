from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import math
import os
import random

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10  # 10 seconds of animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Column attractions
COLUMNS = [SIZE[0] * 0.25, SIZE[0] * 0.5, SIZE[0] * 0.75]

class Vine:
    def __init__(self, target_col: float, rng: random.Random):
        self.rng = rng
        self.target_col = target_col
        self.reset()
        
    def reset(self):
        # Spawn near the bottom, centered around the target column
        self.x = self.target_col + self.rng.uniform(-150, 150)
        self.y = SIZE[1] + self.rng.uniform(10, 100)
        self.prev_x = self.x
        self.prev_y = self.y
        self.age = 0
        self.max_age = self.rng.randint(280, 520)
        self.speed = self.rng.uniform(2.5, 4.5)
        self.seed = self.rng.randint(0, 100000)
        self.active = True

    def update(self):
        if not self.active:
            return
            
        self.prev_x = self.x
        self.prev_y = self.y
        self.age += 1
        
        # Calculate curl noise using finite differences of Perlin noise
        scale = 0.003
        eps = 0.015
        
        n_left = py5.noise(self.x * scale - eps, self.y * scale, self.seed * 0.01)
        n_right = py5.noise(self.x * scale + eps, self.y * scale, self.seed * 0.01)
        n_up = py5.noise(self.x * scale, self.y * scale - eps, self.seed * 0.01)
        n_down = py5.noise(self.x * scale, self.y * scale + eps, self.seed * 0.01)
        
        dx = n_right - n_left
        dy = n_down - n_up
        
        # Angle from noise field
        curl_angle = math.atan2(dx, -dy) * 2.2
        
        # Horizontal pull towards column
        attraction = (self.target_col - self.x) * 0.008
        
        # Combine upward bias, noise, and attraction
        vx = math.cos(curl_angle) * self.speed * 0.65 + attraction
        vy = -self.speed * 0.8  # upward growth bias
        
        self.x += vx
        self.y += vy
        
        # Reset if too old or out of screen
        if self.age > self.max_age or self.y < -50:
            # We don't want to reset immediately for all vines to prevent popping.
            # Instead, we mark as inactive or reset smoothly.
            self.reset()
            
    def draw_segments(self):
        if not self.active:
            return
            
        # Draw segment with progressive tapering
        t = self.age / self.max_age
        
        # Tapering stroke weight
        weight = py5.remap(self.age, 0, self.max_age, 5.5, 0.4)
        alpha = py5.remap(self.age, 0, self.max_age, 82, 10)
        
        # Shift color along the vine: base is emerald/teal, tip is teal/neon yellow
        # Base: hue 160 (Emerald) -> 200 (Teal) -> 45 (Gold) at tip
        if t < 0.6:
            hue = py5.remap(t, 0.0, 0.6, 150, 195)
        else:
            hue = py5.remap(t, 0.6, 1.0, 195, 45)
            
        py5.stroke(hue, 68, 92, alpha)
        py5.stroke_weight(weight)
        py5.line(self.prev_x, self.prev_y, self.x, self.y)
        
        # Spawn leaf at intervals
        if self.age % 48 == 0 and self.rng.random() < 0.6:
            self.draw_leaf(hue)
            
    def draw_leaf(self, parent_hue: float):
        # Calculate angle of growth
        angle = math.atan2(self.y - self.prev_y, self.x - self.prev_x)
        
        py5.push_matrix()
        py5.translate(self.x, self.y)
        # Leaf points outwards
        py5.rotate(angle + self.rng.uniform(-0.9, 0.9))
        py5.no_stroke()
        
        # Translucent double-ellipse leaf
        leaf_hue = (parent_hue + 25) % 360
        py5.fill(leaf_hue, 55, 95, 34)
        size = self.rng.uniform(12, 28)
        py5.ellipse(0, -size * 0.45, size * 0.5, size)
        
        # Glow center
        py5.fill(leaf_hue, 15, 100, 18)
        py5.ellipse(0, -size * 0.45, size * 0.2, size * 0.6)
        
        py5.pop_matrix()

# World state
vines_list = []

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.stroke_cap(py5.ROUND)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize vines
    global vines_list
    rng = random.Random(321)  # Fixed internal seed
    py5.noise_seed(321)
    
    n_vines = 340
    for i in range(n_vines):
        # Evenly distribute target columns
        col = COLUMNS[i % len(COLUMNS)]
        vines_list.append(Vine(col, rng))
        
    # Clear canvas to dark slate once at start
    py5.background(210, 60, 6)

def draw():
    # Progressive clearing for trails
    py5.blend_mode(py5.BLEND)
    py5.fill(210, 60, 6, 6)  # Dark teal-black with 6/255 opacity
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    # Update and draw all vines
    for vine in vines_list:
        vine.update()
        vine.draw_segments()
        
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            os._exit(1)

    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        print("[Render Complete] Video and preview successfully generated.")
        os._exit(0)  # Force exit to prevent macOS JVM hangs

py5.run_sketch()
