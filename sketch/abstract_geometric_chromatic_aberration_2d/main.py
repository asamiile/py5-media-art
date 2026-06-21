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
    # Using RGB for easy channel separation
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw_shapes(offset_x, offset_y, c):
    py5.fill(c)
    py5.no_stroke()
    
    t = py5.frame_count * 0.05
    
    # Generate some floating intersecting geometry
    num_shapes = 20
    for i in range(num_shapes):
        x = py5.width/2 + py5.sin(t * 0.3 + i) * 600 + offset_x
        y = py5.height/2 + py5.cos(t * 0.4 + i * 2) * 400 + offset_y
        
        size = 100 + py5.sin(t * 0.5 + i * 3) * 50
        
        py5.push_matrix()
        py5.translate(x, y)
        py5.rotate(t * 0.2 + i)
        
        if i % 3 == 0:
            py5.rect_mode(py5.CENTER)
            py5.rect(0, 0, size * 2, size * 2)
        elif i % 3 == 1:
            py5.circle(0, 0, size * 2.5)
        else:
            py5.triangle(-size, size, size, size, 0, -size)
            
        py5.pop_matrix()

def draw():
    py5.background(10)
    
    t = py5.frame_count * 0.05
    
    # Chromatic aberration offset based on noise and time
    aberration_strength = 20 + py5.sin(t * 2) * 50 + py5.os_noise(t * 5, 0) * 30
    
    py5.blend_mode(py5.ADD)
    
    # Red channel
    draw_shapes(-aberration_strength, 0, py5.color(255, 0, 0))
    # Green channel
    draw_shapes(0, aberration_strength * 0.5, py5.color(0, 255, 0))
    # Blue channel
    draw_shapes(aberration_strength, -aberration_strength * 0.5, py5.color(0, 0, 255))
    
    # Draw central rotating object with extreme glitch
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2)
    py5.rotate(t * 0.5)
    size = 800 + py5.sin(t * 4) * 100
    py5.no_fill()
    py5.stroke_weight(max(1, 10 + py5.os_noise(t * 10, 0) * 40))
    
    py5.stroke(255, 0, 0)
    py5.rect_mode(py5.CENTER)
    py5.rect(-aberration_strength, 0, size, size)
    
    py5.stroke(0, 255, 0)
    py5.rect(0, aberration_strength, size, size)
    
    py5.stroke(0, 0, 255)
    py5.rect(aberration_strength, -aberration_strength, size, size)
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
