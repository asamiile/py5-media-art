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

GRID_SIZE = 36
CELL_W = 55

def iso(x, y, z):
    iso_x = (x - y) * math.cos(math.radians(30))
    iso_y = (x + y) * math.sin(math.radians(30)) - z
    return iso_x, iso_y

def draw_cube(x, y, z, w, h, depth, hue, saturation, brightness, alpha=255):
    py5.fill(hue, saturation, brightness, alpha)
    py5.begin_shape()
    py5.vertex(*iso(x, y, z + h))
    py5.vertex(*iso(x + w, y, z + h))
    py5.vertex(*iso(x + w, y + depth, z + h))
    py5.vertex(*iso(x, y + depth, z + h))
    py5.end_shape(py5.CLOSE)
    
    py5.fill(hue, saturation, brightness * 0.4, alpha)
    py5.begin_shape()
    py5.vertex(*iso(x, y, z))
    py5.vertex(*iso(x + w, y, z))
    py5.vertex(*iso(x + w, y, z + h))
    py5.vertex(*iso(x, y, z + h))
    py5.end_shape(py5.CLOSE)
    
    py5.fill(hue, saturation, brightness * 0.7, alpha)
    py5.begin_shape()
    py5.vertex(*iso(x + w, y, z))
    py5.vertex(*iso(x + w, y + depth, z))
    py5.vertex(*iso(x + w, y + depth, z + h))
    py5.vertex(*iso(x + w, y, z + h))
    py5.end_shape(py5.CLOSE)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.background(235, 90, 8) 
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.translate(SIZE[0] / 2, SIZE[1] * 0.75)
    
    py5.stroke(220, 50, 15, 100) 
    py5.stroke_weight(2)
    
    tx = math.cos(loop_t) * 0.6
    ty = math.sin(loop_t) * 0.6
    
    for i in range(-GRID_SIZE//2, GRID_SIZE//2):
        for j in range(-GRID_SIZE//2, GRID_SIZE//2):
            x = i * CELL_W
            y = j * CELL_W
            
            dist_center = math.sqrt(i**2 + j**2)
            
            n = py5.noise(i * 0.1, j * 0.1, tx)
            n2 = py5.noise(i * 0.1 + 100, j * 0.1 + 100, ty)
            
            center_factor = max(0, 1.0 - dist_center / (GRID_SIZE/2))
            # Smoothstep the center factor to create a distinct downtown area
            center_factor = center_factor * center_factor * (3 - 2 * center_factor)
            
            h = (n + n2) * 350 * center_factor + 15
            
            hue = (260 + n * 40) % 360 
            
            draw_cube(x, y, 0, CELL_W * 0.8, h, CELL_W * 0.8, hue, 70, 45)
            
            # High buildings have neon tops
            if h > 200 and n > 0.6:
                py5.no_stroke()
                draw_cube(x + CELL_W*0.1, y + CELL_W*0.1, h, CELL_W * 0.6, 5, CELL_W * 0.6, 180, 100, 100) 
                py5.stroke(220, 50, 15, 100)
            elif h > 100 and n2 > 0.7:
                py5.no_stroke()
                draw_cube(x + CELL_W*0.1, y + CELL_W*0.1, h, CELL_W * 0.6, 5, CELL_W * 0.6, 320, 100, 100) 
                py5.stroke(220, 50, 15, 100)
            
            # Traffic
            if i % 3 == 0:
                traffic_pos = ((j + t * GRID_SIZE * 1.5) % GRID_SIZE) - GRID_SIZE//2
                if abs(traffic_pos - j) < 0.5:
                    py5.no_stroke()
                    py5.blend_mode(py5.ADD)
                    draw_cube(x + CELL_W*0.8, y, 0, CELL_W * 0.2, 5, CELL_W * 0.2, 30, 100, 100)
                    py5.blend_mode(py5.BLEND)
                    py5.stroke(220, 50, 15, 100)
                    
            if j % 4 == 0:
                traffic_pos = ((i - t * GRID_SIZE * 2.0) % GRID_SIZE) - GRID_SIZE//2
                if abs(traffic_pos - i) < 0.5:
                    py5.no_stroke()
                    py5.blend_mode(py5.ADD)
                    draw_cube(x, y + CELL_W*0.8, 0, CELL_W * 0.2, 5, CELL_W * 0.2, 190, 100, 100) 
                    py5.blend_mode(py5.BLEND)
                    py5.stroke(220, 50, 15, 100)

    py5.color_mode(py5.RGB, 255)

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
