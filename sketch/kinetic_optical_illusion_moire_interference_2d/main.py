from pathlib import Path
import shutil
import subprocess
import sys
import math
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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_lines(spacing, angle, offset_x, offset_y, color):
    py5.push_matrix()
    py5.translate(SIZE[0]/2 + offset_x, SIZE[1]/2 + offset_y)
    py5.rotate(angle)
    py5.stroke(*color)
    py5.stroke_weight(spacing * 0.45)
    diag = math.hypot(SIZE[0], SIZE[1])
    num_lines = int(diag / spacing) + 2
    for i in range(-num_lines, num_lines):
        py5.line(-diag, i * spacing, diag, i * spacing)
    py5.pop_matrix()

def draw_circles(spacing, center_x, center_y, color):
    py5.push_matrix()
    py5.translate(center_x, center_y)
    py5.no_fill()
    py5.stroke(*color)
    py5.stroke_weight(spacing * 0.45)
    diag = math.hypot(SIZE[0], SIZE[1])
    num_circles = int(diag / spacing) + 2
    for i in range(1, num_circles):
        py5.circle(0, 0, i * spacing * 2)
    py5.pop_matrix()

def draw():
    py5.background(5)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.blend_mode(py5.ADD)
    
    # Layer 1: Concentric circles slowly orbiting
    spacing1 = 16
    cx1 = SIZE[0]/2 + math.sin(loop_t) * 200
    cy1 = SIZE[1]/2 + math.cos(loop_t * 2) * 100
    draw_circles(spacing1, cx1, cy1, (255, 30, 100)) # Deep Pink
    
    # Layer 2: Concentric circles orbiting out of phase
    spacing2 = 16
    cx2 = SIZE[0]/2 + math.sin(loop_t + py5.PI) * 200
    cy2 = SIZE[1]/2 + math.cos(loop_t * 2 + py5.PI) * 100
    draw_circles(spacing2, cx2, cy2, (30, 200, 255)) # Cyan
    
    # Layer 3: Rotating grid of straight lines (clockwise)
    spacing3 = 18
    angle3 = loop_t * 0.5
    draw_lines(spacing3, angle3, math.cos(loop_t)*50, math.sin(loop_t)*50, (100, 255, 50)) # Lime green
    
    # Layer 4: Rotating grid of straight lines (counter-clockwise)
    spacing4 = 18
    angle4 = -loop_t * 0.5 + py5.PI / 4
    draw_lines(spacing4, angle4, math.sin(loop_t)*-50, math.cos(loop_t)*-50, (255, 150, 0)) # Orange

    py5.blend_mode(py5.BLEND)

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
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        import os
        os._exit(0)

py5.run_sketch()
