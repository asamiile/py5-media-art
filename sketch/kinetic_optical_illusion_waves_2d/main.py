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

def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    py5.no_fill()
    py5.stroke_cap(py5.SQUARE)
    
    num_rings = 80
    max_radius = 2000
    
    for i in range(num_rings, 0, -1):
        r = (i / num_rings) * max_radius
        
        # Determine wave distortion for this ring
        wave = py5.sin(t * 2 - i * 0.2)
        
        # Calculate thickness based on noise and wave
        thickness = 10 + 20 * py5.os_noise(i * 0.1, t * 0.5) + wave * 10
        
        # Alternating black and neon colors
        if i % 2 == 0:
            hue = (t * 10 + i * 5) % 360
            py5.stroke(hue, 90, 100)
        else:
            py5.stroke(0, 0, 10)
            
        py5.stroke_weight(max(1, thickness))
        
        # Distort the circle into a slightly wobbly shape
        points = 100
        py5.begin_shape()
        for j in range(points + 1):
            angle = (j / points) * py5.TWO_PI
            
            # Wobbly offset
            offset = py5.os_noise(py5.cos(angle) + 1, py5.sin(angle) + 1, t * 0.2 + i * 0.05) * 50
            
            x = (r + offset) * py5.cos(angle)
            y = (r + offset) * py5.sin(angle)
            
            py5.vertex(x, y)
        py5.end_shape(py5.CLOSE)

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
