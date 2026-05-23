from pathlib import Path
import shutil
import subprocess
import sys
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_SLICES = 12
ANGLE = py5.TWO_PI / NUM_SLICES

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    # Motion blur instead of clearing
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2)
    py5.rotate(t * 0.2)
    
    # We will generate a base geometry for one slice, then mirror and rotate it 12 times
    
    for i in range(NUM_SLICES):
        py5.push_matrix()
        
        # Rotate to the correct slice
        py5.rotate(i * ANGLE)
        
        # Alternate slices are mirrored (flipped on X axis) to create perfect symmetry
        if i % 2 == 1:
            py5.scale(1, -1)
            
        # Draw the geometry for this slice
        draw_kaleidoscope_slice(t)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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

def draw_kaleidoscope_slice(t):
    # This geometry is drawn in the wedge from angle 0 to ANGLE
    
    py5.no_fill()
    py5.stroke_weight(2.0)
    
    # 1. Outer fractal ribbons
    for j in range(5):
        r1 = 200 + py5.sin(t * 1.5 + j) * 100
        r2 = 400 + py5.cos(t * 1.3 - j) * 150
        
        x1 = r1 * py5.cos(ANGLE * 0.2 * j)
        y1 = r1 * py5.sin(ANGLE * 0.2 * j)
        x2 = r2 * py5.cos(ANGLE * 0.8)
        y2 = r2 * py5.sin(ANGLE * 0.8)
        
        # Control points for bezier
        cx1 = x1 + py5.cos(t) * 100
        cy1 = y1 + py5.sin(t) * 100
        cx2 = x2 - py5.cos(t * 1.2) * 100
        cy2 = y2 - py5.sin(t * 0.8) * 100
        
        hue = (t * 50 + j * 20) % 360
        py5.stroke(hue, 80, 80, 50)
        
        py5.bezier(x1, y1, cx1, cy1, cx2, cy2, x2, y2)
        
    # 2. Inner glowing polygons
    num_poly = 3
    for k in range(num_poly):
        rad = 50 + k * 40 + py5.sin(t * 2.0 + k) * 20
        hue = (200 + t * 30 + k * 40) % 360
        
        py5.stroke(hue, 90, 100, 80)
        py5.fill(hue, 90, 100, 10)
        
        py5.begin_shape()
        # Draw a small jagged line inside the slice
        for step in range(4):
            a = step * (ANGLE / 3)
            r = rad + py5.noise(step * 0.5, k, t) * 100
            py5.vertex(r * py5.cos(a), r * py5.sin(a))
        py5.end_shape()

py5.run_sketch()
