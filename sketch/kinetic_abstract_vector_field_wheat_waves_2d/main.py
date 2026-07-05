from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Grid of lines
RES = 40 # space between lines
cols = SIZE[0] // RES + 2
rows = SIZE[1] // RES + 2

# We need a 3D noise function. py5 has py5.noise(x, y, z), but it's slow to call in a loop.
# Let's just use numpy sine/cosine noise for speed and smoothness.
x_grid = np.linspace(0, SIZE[0], cols)
y_grid = np.linspace(0, SIZE[1], rows)
X, Y = np.meshgrid(x_grid, y_grid)
X_flat = X.flatten()
Y_flat = Y.flatten()

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(10, 15, 20)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.stroke_cap(py5.ROUND)

def draw():
    # Fade background slightly for a nice trail
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 15, 20, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.015
    
    # Procedural 2D noise field that evolves over time
    # Combine multiple sine waves for a complex "wind" field
    scale1 = 0.002
    scale2 = 0.005
    
    angle1 = np.sin(X_flat * scale1 + time_val) * np.cos(Y_flat * scale1 - time_val * 0.5)
    angle2 = np.cos(X_flat * scale2 - time_val * 1.2) * np.sin(Y_flat * scale2 + time_val * 0.8)
    
    angles = (angle1 + angle2) * np.pi
    
    # Calculate colors based on angles and position
    # Golden Hour Palette: Gold (40), Amber (30), Deep Brown (20)
    hues = 20 + ((angles + np.pi) / (2 * np.pi)) * 30
    brightness = 50 + ((angles + np.pi) / (2 * np.pi)) * 50
    
    py5.stroke_weight(RES * 0.2)
    
    length = RES * 0.8
    dx = np.cos(angles) * length
    dy = np.sin(angles) * length
    
    # Draw all vectors
    # py5 doesn't have a vectorized line drawing, so we use begin_shape(py5.LINES)
    py5.begin_shape(py5.LINES)
    for i in range(len(X_flat)):
        py5.stroke(hues[i], 80, brightness[i], 80)
        
        # Center the line
        x = X_flat[i]
        y = Y_flat[i]
        
        # We can simulate the lines bending by making them curves, but lines are faster.
        py5.vertex(x - dx[i]/2, y - dy[i]/2)
        py5.vertex(x + dx[i]/2, y + dy[i]/2)
        
    py5.end_shape()

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
