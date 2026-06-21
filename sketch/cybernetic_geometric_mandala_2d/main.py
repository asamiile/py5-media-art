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
    py5.background(5)
    py5.blend_mode(py5.ADD)

def draw_layer(num_petals, radius, rotation_speed, t, hue_base):
    py5.push_matrix()
    py5.rotate(t * rotation_speed)
    py5.stroke((hue_base + py5.sin(t) * 30) % 360, 80, 90, 80)
    py5.no_fill()
    py5.stroke_weight(2 + py5.sin(t * 2) * 1.5)
    
    for i in range(num_petals):
        angle = (i / num_petals) * py5.TWO_PI
        py5.push_matrix()
        py5.rotate(angle)
        
        # Draw a complex polygon petal
        py5.begin_shape()
        py5.vertex(0, 0)
        py5.vertex(radius * 0.3, radius * 0.5)
        py5.vertex(0, radius)
        py5.vertex(-radius * 0.3, radius * 0.5)
        py5.end_shape(py5.CLOSE)
        
        # Inner geometric lines
        r2 = radius * (0.5 + 0.3 * py5.sin(t * 3 + angle))
        py5.line(0, radius * 0.5, 0, r2)
        py5.circle(0, r2, 20)
        
        py5.pop_matrix()
        
    py5.pop_matrix()

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count * 0.02
    
    # Draw multiple layers of the mandala
    draw_layer(12, 800,  0.5, t, 180)
    draw_layer(24, 600, -0.3, t, 280)
    draw_layer(8,  400,  1.2, t, 50)
    draw_layer(36, 200, -0.8, t, 330)

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
