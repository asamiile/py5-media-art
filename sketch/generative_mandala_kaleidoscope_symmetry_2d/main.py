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

SYMMETRY = 12

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 12, 18)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw_base_shape(t):
    # Draw a complex, evolving segment
    py5.no_fill()
    
    # We use multiple layers of curves
    for layer in range(15):
        # Noise inputs
        nx = layer * 0.1
        ny = layer * 0.1 + 100
        
        # Base angle and radius
        r1 = py5.os_noise(nx, ny, t * 0.5) * 800
        a1 = py5.os_noise(nx + 50, ny + 50, t * 0.3) * py5.TWO_PI / SYMMETRY
        
        r2 = py5.os_noise(nx + 10, ny + 10, t * 0.4) * 1000
        a2 = py5.os_noise(nx + 60, ny + 60, t * 0.2) * py5.TWO_PI / SYMMETRY
        
        r3 = py5.os_noise(nx + 20, ny + 20, t * 0.6) * 1200
        a3 = py5.os_noise(nx + 70, ny + 70, t * 0.4) * py5.TWO_PI / SYMMETRY
        
        # Calculate points
        x1, y1 = np.cos(a1) * r1, np.sin(a1) * r1
        x2, y2 = np.cos(a2) * r2, np.sin(a2) * r2
        x3, y3 = np.cos(a3) * r3, np.sin(a3) * r3
        
        # Dynamic coloring
        hue = (t * 20 + layer * 15) % 360
        # Iridescent opal colors (mostly cyan, pink, white)
        # We constrain hue to these ranges by remapping
        mapped_hue = py5.remap(py5.os_noise(layer, t * 0.1), 0, 1, 150, 300)
        
        # Fade edges
        alpha = py5.remap(np.sin(t * 2.0 + layer), -1, 1, 20, 90)
        
        py5.stroke_weight(1.5 + layer * 0.2)
        py5.stroke(mapped_hue, 40, 90, alpha)
        
        py5.bezier(0, 0, x1, y1, x2, y2, x3, y3)
        
        # Add sparkling nodes
        if py5.os_noise(layer, t) > 0.6:
            py5.no_stroke()
            py5.fill(mapped_hue, 20, 100, alpha * 1.5)
            py5.circle(x3, y3, 4 + layer)
            py5.no_fill()

def draw():
    # Motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 12, 18, 15)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = py5.frame_count * 0.015
    
    # Global slow rotation
    py5.rotate(t * 0.1)
    
    # Draw kaleidoscope
    for i in range(SYMMETRY):
        py5.push_matrix()
        py5.rotate(i * py5.TWO_PI / SYMMETRY)
        
        draw_base_shape(t)
        
        # Reflect
        py5.scale(1, -1)
        draw_base_shape(t)
        
        py5.pop_matrix()

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
