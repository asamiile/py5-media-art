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
    py5.no_stroke()
    
    t = py5.frame_count * 0.05
    
    cols = 60
    rows = 40
    w = py5.width / cols
    h = py5.height / rows
    
    def get_vertex(x_idx, y_idx):
        base_x = x_idx * w
        base_y = y_idx * h
        
        # Center-relative coordinates
        cx = base_x - py5.width/2
        cy = base_y - py5.height/2
        
        dist = py5.dist(cx, cy, 0, 0)
        angle = py5.atan2(cy, cx)
        
        # Deformation
        twist = py5.sin(dist * 0.005 - t) * 50
        noise_x = py5.os_noise(x_idx * 0.1, y_idx * 0.1, t * 0.5) * 40
        noise_y = py5.os_noise(x_idx * 0.1 + 100, y_idx * 0.1, t * 0.5) * 40
        
        # Spiral effect
        nx = base_x + py5.cos(angle + twist*0.01) * twist + noise_x
        ny = base_y + py5.sin(angle + twist*0.01) * twist + noise_y
        
        return nx, ny

    for y in range(rows):
        for x in range(cols):
            x1, y1 = get_vertex(x, y)
            x2, y2 = get_vertex(x+1, y)
            x3, y3 = get_vertex(x+1, y+1)
            x4, y4 = get_vertex(x, y+1)
            
            if (x + y) % 2 == 0:
                hue = (t * 20 + py5.dist(x1, y1, py5.width/2, py5.height/2) * 0.1) % 360
                py5.fill(hue, 80, 90)
            else:
                py5.fill(10, 10, 10)
                
            py5.begin_shape()
            py5.vertex(x1, y1)
            py5.vertex(x2, y2)
            py5.vertex(x3, y3)
            py5.vertex(x4, y4)
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
