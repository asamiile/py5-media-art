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

# Parameters for layers
layers = []
for i in range(8):
    layers.append({
        'radius': 100 + i * 150,
        'points': random.randint(3, 8),
        'freq': random.uniform(1.0, 5.0),
        'speed': random.uniform(-0.05, 0.05),
        'hue_offset': random.uniform(0, 360)
    })

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion blur / fade
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.02
    
    py5.blend_mode(py5.ADD)
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    slices = 12
    slice_angle = py5.TWO_PI / slices
    
    for layer in layers:
        r_base = layer['radius']
        pts = layer['points']
        freq = layer['freq']
        rot = t * layer['speed']
        hue = (layer['hue_offset'] + t * 10) % 360
        
        # Breathing radius
        r = r_base + np.sin(t * freq * 0.5) * 50
        
        py5.stroke(hue, 80, 100, 60)
        py5.stroke_weight(2)
        py5.no_fill()
        
        for i in range(slices):
            py5.push_matrix()
            py5.rotate(i * slice_angle + rot)
            
            # Draw an organic petal shape
            py5.begin_shape()
            for j in range(pts + 1):
                ang = py5.remap(j, 0, pts, -slice_angle/2, slice_angle/2)
                # Modulate the radius of the petal
                petal_r = r * (0.5 + 0.5 * np.cos(j * py5.PI / pts))
                
                # Add some secondary oscillation
                petal_r += np.sin(t * freq + j) * 30
                
                px = py5.cos(ang) * petal_r
                py_coord = py5.sin(ang) * petal_r
                py5.curve_vertex(px, py_coord)
            py5.end_shape()
            
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
