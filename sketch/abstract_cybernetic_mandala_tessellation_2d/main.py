from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random

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

NUM_LAYERS = 8
SYMMETRY = 12
ANGLE = py5.PI * 2 / SYMMETRY

layers = []

class Layer:
    def __init__(self, idx):
        self.radius_inner = idx * 100 + 50
        self.radius_outer = self.radius_inner + random.uniform(50, 80)
        self.speed = random.uniform(-0.01, 0.01)
        self.hue = random.choice([160, 200, 280, 320, 60])
        self.shapes = []
        
        # Generate random geometry for this layer
        num_shapes = random.randint(1, 4)
        for _ in range(num_shapes):
            a_start = random.uniform(0, ANGLE * 0.8)
            a_span = random.uniform(0.1, ANGLE - a_start)
            r_start = random.uniform(self.radius_inner, self.radius_outer)
            r_span = random.uniform(10, self.radius_outer - r_start)
            self.shapes.append({
                'a1': a_start, 'a2': a_start + a_span,
                'r1': r_start, 'r2': r_start + r_span,
                'type': random.choice(['arc', 'line', 'triangle', 'dots'])
            })

    def draw(self, t):
        py5.push_matrix()
        py5.rotate(t * self.speed)
        
        py5.stroke(self.hue, 80, 100)
        py5.fill(self.hue, 80, 100, 50)
        
        for i in range(SYMMETRY):
            py5.push_matrix()
            py5.rotate(i * ANGLE)
            
            for s in self.shapes:
                if s['type'] == 'arc':
                    py5.no_fill()
                    py5.stroke_weight(4)
                    py5.arc(0, 0, s['r1']*2, s['r1']*2, s['a1'], s['a2'])
                elif s['type'] == 'line':
                    py5.stroke_weight(2)
                    py5.line(py5.cos(s['a1'])*s['r1'], py5.sin(s['a1'])*s['r1'],
                             py5.cos(s['a2'])*s['r2'], py5.sin(s['a2'])*s['r2'])
                elif s['type'] == 'triangle':
                    py5.fill(self.hue, 80, 100, 80)
                    py5.stroke_weight(1)
                    py5.triangle(py5.cos(s['a1'])*s['r1'], py5.sin(s['a1'])*s['r1'],
                                 py5.cos(s['a2'])*s['r1'], py5.sin(s['a2'])*s['r1'],
                                 py5.cos((s['a1']+s['a2'])/2)*s['r2'], py5.sin((s['a1']+s['a2'])/2)*s['r2'])
                elif s['type'] == 'dots':
                    py5.no_stroke()
                    py5.fill(self.hue, 80, 100)
                    py5.circle(py5.cos((s['a1']+s['a2'])/2) * s['r1'], py5.sin((s['a1']+s['a2'])/2) * s['r1'], 10)
            
            py5.pop_matrix()
            
        py5.pop_matrix()

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for i in range(NUM_LAYERS):
        layers.append(Layer(i))

def draw():
    py5.background(10, 15, 20, 100) # Slight motion blur
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    t = py5.frame_count
    
    # Pulse the whole mandala
    pulse = py5.sin(t * 0.05) * 0.05 + 1.0
    py5.scale(pulse)
    
    for layer in layers:
        layer.draw(t)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
