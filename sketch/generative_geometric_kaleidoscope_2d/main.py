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

def draw_pattern(t, size):
    py5.no_fill()
    py5.stroke_weight(2 + size * 0.005)
    
    # Layered geometric shapes that mutate
    num_shapes = 12
    for i in range(num_shapes):
        hue = (t * 50 + i * 20 + size * 0.1) % 360
        py5.stroke(hue, 80, 90, 80)
        
        py5.push_matrix()
        py5.rotate(t * 0.2 + i * py5.TWO_PI / num_shapes)
        
        offset = size * 0.3 * py5.sin(t + i)
        rad = size * 0.5
        
        py5.begin_shape()
        py5.vertex(offset, rad)
        py5.bezier_vertex(rad, offset, rad, -offset, offset, -rad)
        py5.bezier_vertex(-rad, -offset, -rad, offset, -offset, rad)
        py5.end_shape(py5.CLOSE)
        
        # Internal sharp polygons
        if i % 2 == 0:
            py5.stroke((hue + 180) % 360, 80, 90, 60)
            py5.triangle(0, -rad*0.8, rad*0.7, rad*0.4, -rad*0.7, rad*0.4)
            
        py5.pop_matrix()

def draw():
    py5.background(5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width/2, py5.height/2)
    
    slices = 12
    slice_angle = py5.TWO_PI / slices
    
    # Infinite zoom effect
    zoom = (py5.frame_count % 120) / 120.0
    scale_factor = 2.0 ** zoom
    
    py5.scale(scale_factor)
    
    # We draw several nested scales to create the infinite zoom illusion
    for depth in range(4, -2, -1):
        s = 0.5 ** depth
        
        py5.push_matrix()
        py5.scale(s)
        py5.rotate(t * 0.1 * (1 if depth % 2 == 0 else -1))
        
        for i in range(slices):
            py5.push_matrix()
            py5.rotate(i * slice_angle)
            
            # Mirror alternate slices
            if i % 2 == 1:
                py5.scale(1, -1)
                
            draw_pattern(t, py5.width)
            
            py5.pop_matrix()
            
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
