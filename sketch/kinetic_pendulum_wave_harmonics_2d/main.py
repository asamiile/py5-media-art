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

GRID_COLS = 60
GRID_ROWS = 60
SPACING = 30

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)
    
def draw():
    # Fading background for trails
    py5.fill(0, 40)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count / FPS  # Time in seconds
    
    cx = py5.width / 2
    cy = py5.height / 2
    
    offset_x = (GRID_COLS * SPACING) / 2
    offset_y = (GRID_ROWS * SPACING) / 2
    
    # We want exactly N complete cycles in DURATION_SEC for the first pendulum,
    # and N+k cycles for the subsequent pendulums.
    # We'll use radial distance from center as the index.
    
    py5.push_matrix()
    py5.translate(cx - offset_x, cy - offset_y)
    
    for i in range(GRID_COLS):
        for j in range(GRID_ROWS):
            x = i * SPACING
            y = j * SPACING
            
            # Distance from center of grid
            dx = i - (GRID_COLS - 1) / 2.0
            dy = j - (GRID_ROWS - 1) / 2.0
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Base frequency is 1 cycle per 15 seconds (DURATION_SEC)
            # Each unit of distance adds a harmonic offset
            freq = (1.0 / DURATION_SEC) * (15 + dist * 0.5)
            
            # Pendulum swing angle
            angle = math.sin(2 * math.pi * freq * t)
            
            # The swing amplitude
            amplitude = SPACING * 0.8
            
            px = x + amplitude * angle
            py = y
            
            # Color mapping
            ratio = dist / (GRID_COLS * 0.7)
            ratio = max(0, min(1, ratio))
            
            r = int(py5.lerp(255, 255, ratio))
            g = int(py5.lerp(215, 140, ratio))
            b = int(py5.lerp(0, 0, ratio))
            
            py5.fill(r, g, b, 200)
            py5.no_stroke()
            
            # Size pulses slightly
            size = SPACING * 0.3 * (1 + 0.3 * math.cos(2 * math.pi * freq * t + math.pi))
            py5.ellipse(px, py, size, size)
            
    py5.pop_matrix()
    
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
