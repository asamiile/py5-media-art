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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw_polygon(radius, sides):
    py5.begin_shape()
    for i in range(sides):
        angle = (i / sides) * py5.TWO_PI
        py5.vertex(radius * py5.cos(angle), radius * py5.sin(angle))
    py5.end_shape(py5.CLOSE)

def draw():
    py5.background(10)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2)
    
    # Zoom cycle length
    zoom_cycle = 2.0
    progress = (t % zoom_cycle) / zoom_cycle
    
    # Scale everything so that it zooms in continuously
    # By using exp, the zoom feels constant speed
    base_scale = 2.0 ** progress
    py5.scale(base_scale)
    
    # Draw many layers. 
    # Because we scale by 2^progress, when progress goes 0->1, scale goes 1->2.
    # To make it infinite, layer i and layer i+1 should differ by a factor of 2 in size.
    
    num_layers = 15
    for i in range(-5, num_layers):
        layer_scale = 2.0 ** -i
        
        py5.push_matrix()
        py5.scale(layer_scale)
        
        # Alternate rotation direction for each layer
        rot_dir = 1 if i % 2 == 0 else -1
        py5.rotate(t * 0.5 * rot_dir)
        
        # Color based on layer and time
        hue = (180 + i * 15 + t * 50) % 360
        py5.stroke(hue, 80, 90, 80)
        py5.stroke_weight(2 / (layer_scale * base_scale)) # Keep stroke weight constant visually
        py5.no_fill()
        
        # Draw complex geometry for this layer
        radius = 800
        
        draw_polygon(radius, 6)
        
        py5.push_matrix()
        py5.rotate(py5.PI / 6)
        draw_polygon(radius * 0.866, 6) # Inner hexagon
        py5.pop_matrix()
        
        # Draw connecting spokes
        py5.begin_shape(py5.LINES)
        for j in range(12):
            angle = (j / 12) * py5.TWO_PI
            py5.vertex(radius * 0.5 * py5.cos(angle), radius * 0.5 * py5.sin(angle))
            py5.vertex(radius * py5.cos(angle), radius * py5.sin(angle))
        py5.end_shape()
        
        # Inner circle
        py5.circle(0, 0, radius)
        
        py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
