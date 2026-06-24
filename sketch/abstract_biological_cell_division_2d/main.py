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

cells = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    # Initialize a few starting cells
    for i in range(5):
        cells.append({
            "x": py5.width / 2 + py5.random(-200, 200),
            "y": py5.height / 2 + py5.random(-200, 200),
            "radius": py5.random(150, 250),
            "seed": py5.random(1000),
            "hue": py5.random(10, 40), # Peach to pink
            "split_phase": py5.random(0, py5.TWO_PI),
            "split_speed": py5.random(0.01, 0.02)
        })

def draw_cell(cell, t):
    num_points = 100
    py5.begin_shape()
    for i in range(num_points):
        angle = py5.remap(i, 0, num_points, 0, py5.TWO_PI)
        
        # Noise for organic shape
        nx = py5.remap(math.cos(angle), -1, 1, 0, 1) + cell["seed"]
        ny = py5.remap(math.sin(angle), -1, 1, 0, 1) + cell["seed"]
        noise_val = py5.os_noise(nx, ny, t * 2)
        
        r = cell["radius"] + py5.remap(noise_val, -1, 1, -50, 50)
        
        # Deformation for splitting
        split_val = math.sin(cell["split_phase"] + t * 5)
        if split_val > 0.5:
            # Stretch along X axis and pinch in middle
            if math.cos(angle) > 0.5 or math.cos(angle) < -0.5:
                r *= (1.0 + (split_val - 0.5) * 0.5)
            else:
                r *= (1.0 - (split_val - 0.5) * 0.8)

        x = cell["x"] + r * math.cos(angle)
        y = cell["y"] + r * math.sin(angle)
        
        py5.curve_vertex(x, y)
        
        # Close shape
        if i == 0:
            first_x, first_y = x, y
            
    py5.curve_vertex(first_x, first_y)
    py5.end_shape(py5.CLOSE)

def draw():
    py5.background(340, 60, 20) # Deep maroon
    
    t = py5.frame_count / 60.0
    
    # Blend modes and drawing
    py5.blend_mode(py5.ADD)
    
    for cell in cells:
        # Move slowly
        cell["x"] += math.cos(cell["seed"] + t * 0.5) * 2
        cell["y"] += math.sin(cell["seed"] + t * 0.5) * 2
        
        # Draw outer membrane
        py5.no_stroke()
        py5.fill(cell["hue"], 70, 80, 40)
        draw_cell(cell, t)
        
        # Draw inner core (nucleus)
        py5.fill(50, 90, 100, 80) # Bright yellow
        py5.push_matrix()
        py5.translate(cell["x"], cell["y"])
        py5.scale(0.3)
        py5.translate(-cell["x"], -cell["y"])
        draw_cell(cell, t * 1.5)
        py5.pop_matrix()

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
