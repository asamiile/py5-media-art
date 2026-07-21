from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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

MAX_DEPTH = 7
PALETTE = [
    (250, 250, 245), # Off-white
    (15, 15, 20),    # Deep black
    (220, 40, 40),   # Bauhaus Red
    (30, 80, 200),   # Bauhaus Blue
    (240, 200, 30)   # Bauhaus Yellow
]

def draw_quadtree(x, y, w, h, depth, time):
    cx = x + w / 2
    cy = y + h / 2
    
    # Sample 3D noise using center coordinate and time
    # We use different frequencies for different depths to make it organic
    noise_freq = 0.001 * (depth + 1)
    n = py5.os_noise(cx * noise_freq, cy * noise_freq, time)
    
    # Threshold for subdivision changes based on depth
    # Shallow depths subdivide easily, deep depths require higher noise
    threshold = py5.remap(depth, 0, MAX_DEPTH, -0.5, 0.4)
    
    if depth < MAX_DEPTH and n > threshold:
        # Subdivide
        hw = w / 2
        hh = h / 2
        draw_quadtree(x, y, hw, hh, depth + 1, time)
        draw_quadtree(x + hw, y, hw, hh, depth + 1, time)
        draw_quadtree(x, y + hh, hw, hh, depth + 1, time)
        draw_quadtree(x + hw, y + hh, hw, hh, depth + 1, time)
    else:
        # Draw leaf node
        
        # Determine color based on noise and depth
        c_idx = int(py5.remap(n + py5.random(-0.1, 0.1), -1, 1, 0, len(PALETTE) * 1.5))
        c_idx = py5.constrain(c_idx, 0, len(PALETTE) - 1)
        col = PALETTE[c_idx]
        
        py5.fill(*col)
        py5.stroke(15, 15, 20)
        py5.stroke_weight(py5.remap(depth, 0, MAX_DEPTH, 8.0, 1.0))
        
        # Inner padding for visual interest
        pad = py5.remap(depth, 0, MAX_DEPTH, 10, 0)
        py5.rect(x + pad, y + pad, w - pad*2, h - pad*2)
        
        # Add internal geometric motifs for some cells
        if depth >= 2 and n > (threshold - 0.2):
            motif = int(py5.random(4))
            py5.fill(15, 15, 20) # Black motifs
            py5.no_stroke()
            if motif == 0:
                py5.circle(cx, cy, min(w, h) * 0.4)
            elif motif == 1:
                py5.rect(cx - w*0.1, y + pad, w*0.2, h - pad*2)
            elif motif == 2:
                py5.rect(x + pad, cy - h*0.1, w - pad*2, h*0.2)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(*PALETTE[0])
    py5.random_seed(42) # Keep the motifs consistent across frames for a given layout
    
    time = py5.frame_count * 0.008
    
    # Add a global pan to the noise field
    time_pan_x = py5.frame_count * 2.0
    time_pan_y = py5.frame_count * 1.5
    
    py5.push_matrix()
    # We pass time, but the position is shifted by time_pan internally or we can just shift the coordinates we pass to noise
    # We will modify the draw_quadtree function to accept shifted coordinates? No, we'll just shift the canvas and draw a larger tree
    
    # To pan, we draw a larger quadtree and translate it
    # We need to draw from -w to 2w etc, but quadtree naturally handles this if we just pass a larger initial rectangle
    # Actually, shifting the canvas with translate doesn't change the absolute coordinates if we use screen coords for noise.
    # So we'll just translate the canvas.
    py5.translate(-time_pan_x % SIZE[0], -time_pan_y % SIZE[1])
    
    # Draw a 2x2 grid of full-screen quadtrees to cover the panning
    for i in range(-1, 2):
        for j in range(-1, 2):
            draw_quadtree(i * SIZE[0], j * SIZE[1], SIZE[0], SIZE[1], 0, time)
            
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
