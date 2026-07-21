from pathlib import Path
import shutil
import subprocess
import sys
import random
import math
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid properties
COLS = 50
ROWS = 60
CELL_SIZE = 120

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw_isometric_building(x, y, w, h, base_hue, brightness):
    # Isometric transformation angles
    angle = math.radians(30)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    # Left face
    py5.fill(base_hue, 80, brightness * 0.7, 90)
    py5.begin_shape()
    py5.vertex(float(x), float(y))
    py5.vertex(float(x - w * cos_a), float(y - w * sin_a))
    py5.vertex(float(x - w * cos_a), float(y - w * sin_a - h))
    py5.vertex(float(x), float(y - h))
    py5.end_shape(py5.CLOSE)
    
    # Right face
    py5.fill(base_hue, 80, brightness, 90)
    py5.begin_shape()
    py5.vertex(float(x), float(y))
    py5.vertex(float(x + w * cos_a), float(y - w * sin_a))
    py5.vertex(float(x + w * cos_a), float(y - w * sin_a - h))
    py5.vertex(float(x), float(y - h))
    py5.end_shape(py5.CLOSE)
    
    # Top face
    py5.fill(base_hue, 50, brightness * 1.2, 100)
    py5.begin_shape()
    py5.vertex(float(x), float(y - h))
    py5.vertex(float(x - w * cos_a), float(y - w * sin_a - h))
    py5.vertex(float(x), float(y - w * sin_a * 2 - h))
    py5.vertex(float(x + w * cos_a), float(y - w * sin_a - h))
    py5.end_shape(py5.CLOSE)

def draw():
    py5.background(10, 10, 15)
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.stroke(0)
    py5.stroke_weight(2)
    
    start_x = py5.width / 2
    start_y = py5.height * 0.8
    
    angle = math.radians(30)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    
    # Scroll speed
    scroll_offset = t * ROWS * 2.0
    
    # Draw from back to front to handle occlusion
    for row in range(ROWS, -1, -1):
        for col in range(COLS):
            # Calculate logical grid coordinates with scrolling
            grid_y = row - (scroll_offset % 1.0)
            grid_x = col - COLS / 2
            
            # Absolute noise coordinates
            noise_y = (row - int(scroll_offset)) * 0.1
            noise_x = col * 0.1
            
            # Map to screen space (Isometric)
            screen_x = start_x + (grid_x - grid_y) * CELL_SIZE * cos_a
            screen_y = start_y + (grid_x + grid_y) * CELL_SIZE * sin_a
            
            # Distance fade (depth of field / fog)
            dist = math.hypot(grid_x, grid_y)
            fog = max(0, 1.0 - (dist / (ROWS * 0.8)))
            
            # Building height based on noise
            h_noise = py5.noise(noise_x, noise_y)
            
            # Create a "city center" peaking effect
            center_dist = abs(grid_x) / (COLS / 2)
            height_mult = max(0, 1.0 - center_dist) ** 2 * 800 + 100
            
            h = h_noise ** 2 * height_mult
            
            # Color based on height and position
            base_hue = (280 + h_noise * 120 + t * 360) % 360
            brightness = 40 + h_noise * 60
            
            # Only draw if on screen and not completely faded
            if fog > 0.05 and screen_y - h < py5.height and screen_y > 0 and screen_x > -CELL_SIZE and screen_x < py5.width + CELL_SIZE:
                # Modulate brightness by fog
                draw_isometric_building(screen_x, screen_y, CELL_SIZE, h, base_hue, brightness * fog)

    # Global glow overlay
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    py5.fill(300, 80, 100, 10)
    py5.rect(0, 0, py5.width, py5.height)
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
        import os
        os._exit(0)

py5.run_sketch()
