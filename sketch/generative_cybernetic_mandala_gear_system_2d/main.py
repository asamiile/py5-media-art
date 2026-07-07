from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

class Layer:
    def __init__(self, radius, style, color, speed, num_segments, is_stepped):
        self.radius = radius
        self.style = style # 'arc', 'dots', 'cogs'
        self.color = color
        self.speed = speed
        self.num_segments = num_segments
        self.is_stepped = is_stepped
        
        self.thickness = random.uniform(2, 25)
        self.gap = random.uniform(0.1, 0.5)

    def get_angle(self, t):
        if self.is_stepped:
            # Mechanical stepping
            t_scaled = t * abs(self.speed) * 2.0
            step = np.floor(t_scaled)
            frac = t_scaled - step
            # Ease in-out
            ease = frac * frac * (3 - 2 * frac)
            # Make the motion sharp
            ease = np.power(ease, 3.0)
            angle = (step + ease) * (py5.TWO_PI / self.num_segments)
            return angle if self.speed > 0 else -angle
        else:
            return t * self.speed

    def draw(self, t):
        angle = self.get_angle(t)
        
        py5.push_matrix()
        py5.rotate(angle)
        
        py5.stroke(*self.color)
        py5.stroke_weight(self.thickness)
        py5.no_fill()
        
        seg_angle = py5.TWO_PI / self.num_segments
        
        if self.style == 'arc':
            py5.stroke_cap(py5.SQUARE)
            for i in range(self.num_segments):
                start_a = i * seg_angle
                end_a = start_a + seg_angle * (1.0 - self.gap)
                py5.arc(0, 0, self.radius*2, self.radius*2, start_a, end_a)
                
        elif self.style == 'dots':
            py5.stroke_weight(self.thickness * 1.5)
            py5.stroke_cap(py5.ROUND)
            for i in range(self.num_segments):
                a = i * seg_angle
                x = self.radius * np.cos(a)
                y = self.radius * np.sin(a)
                py5.point(x, y)
                
        elif self.style == 'cogs':
            py5.stroke_weight(2)
            py5.fill(*self.color, 100)
            py5.begin_shape()
            for i in range(self.num_segments * 2):
                a = i * (seg_angle / 2)
                r = self.radius + (self.thickness if i % 2 == 0 else -self.thickness)
                py5.vertex(r * np.cos(a), r * np.sin(a))
            py5.end_shape(py5.CLOSE)

        py5.pop_matrix()

layers = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 15, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    
    # Palette
    colors = [
        (0, 255, 128),   # Neon Green
        (255, 180, 0),   # Amber
        (0, 200, 255),   # Cyan
        (255, 50, 100),  # Pink/Red
        (200, 200, 200)  # White/Gray
    ]
    
    num_layers = 18
    max_radius = min(SIZE[0], SIZE[1]) * 0.45
    
    for i in range(num_layers):
        radius = py5.remap(i, 0, num_layers-1, 50, max_radius)
        style = random.choice(['arc', 'arc', 'dots', 'cogs'])
        color = random.choice(colors)
        speed = random.uniform(0.1, 1.0) * random.choice([1, -1])
        num_segments = random.choice([4, 6, 8, 12, 24, 36])
        is_stepped = random.choice([True, False, False])
        
        layers.append(Layer(radius, style, color, speed, num_segments, is_stepped))

def draw():
    # Motion blur / trail effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15, 20, 60)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = py5.frame_count * 0.02
    
    for layer in layers:
        layer.draw(t)
        
    # Draw a central glowing core
    py5.fill(0, 255, 128, 50)
    py5.no_stroke()
    core_r = 30 + 10 * np.sin(t * 5.0)
    py5.circle(0, 0, core_r * 2)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
