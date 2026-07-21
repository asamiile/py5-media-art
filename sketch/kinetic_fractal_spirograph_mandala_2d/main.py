from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw_spirograph_layer(cx, cy, radii, speeds, phases, num_points, time, hue_base):
    py5.begin_shape()
    for i in range(num_points):
        theta = (i / num_points) * py5.TWO_PI
        
        x = cx
        y = cy
        
        for r, s, p in zip(radii, speeds, phases):
            angle = theta * s + time * py5.TWO_PI + p
            x += math.cos(angle) * r
            y += math.sin(angle) * r
            
        py5.vertex(float(x), float(y))
    py5.end_shape(py5.CLOSE)

def draw():
    # Subtle trailing effect
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    t = py5.frame_count / TOTAL_FRAMES
    cx = py5.width / 2
    cy = py5.height / 2
    
    # We will draw a few layers of spirographs
    num_layers = 15
    for layer in range(num_layers):
        layer_norm = layer / num_layers
        
        hue = (t * 360 + layer_norm * 180) % 360
        py5.stroke(hue, 80, 100, 40)
        py5.stroke_weight(2)
        
        # Radii change over time to make it bloom
        r1 = 400 * layer_norm + math.sin(t * py5.TWO_PI + layer_norm * py5.TWO_PI) * 100
        r2 = 200 * layer_norm + math.cos(t * py5.TWO_PI * 2 + layer_norm * py5.TWO_PI) * 150
        r3 = 100 * layer_norm + math.sin(t * py5.TWO_PI * 3 + layer_norm * py5.TWO_PI) * 50
        
        radii = [r1, r2, r3]
        
        # Speed ratios (integers create closed loops)
        s1 = 1 + int(layer_norm * 3)
        s2 = -2 - int(layer_norm * 5)
        s3 = 5 + int(layer_norm * 7)
        speeds = [s1, s2, s3]
        
        # Phases
        p1 = t * py5.TWO_PI
        p2 = -t * py5.TWO_PI * 1.5
        p3 = t * py5.TWO_PI * 2
        phases = [p1, p2, p3]
        
        num_points = 1000
        
        draw_spirograph_layer(cx, cy, radii, speeds, phases, num_points, t, hue)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
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
        import os
        os._exit(0)

py5.run_sketch()
