from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = 15  # 15s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Sand dunes data
GRID_W = 100
GRID_H = 100
W_STEP = 0
H_STEP = 0

def setup():
    global W_STEP, H_STEP
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    W_STEP = SIZE[0] / (GRID_W - 1) * 1.5
    H_STEP = SIZE[1] / (GRID_H - 1) * 1.5
    
def draw():
    py5.background(10, 5, 5) # Dark void
    py5.directional_light(255, 230, 200, 0.5, 0.5, -1) # Warm directional light
    py5.ambient_light(50, 20, 20)
    
    t = py5.frame_count * 0.005
    
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 200, -200)
    py5.rotate_x(py5.PI / 3)
    py5.translate(-SIZE[0]*0.75, -SIZE[1]*0.75, 0)
    
    py5.no_stroke()
    
    for y in range(GRID_H - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(GRID_W):
            for dy in (0, 1):
                cy = y + dy
                px = x * W_STEP
                py = cy * H_STEP
                
                # Perlin noise for dune height
                noise_val = py5.os_noise(x * 0.03 + t, cy * 0.03 + t, t * 0.5)
                # Create ridges using abs function on noise
                height = abs(noise_val) * 400
                
                # Colors
                if height < 100:
                    py5.fill(139, 58, 58) # Deep crimson/terracotta
                elif height < 300:
                    py5.fill(220, 140, 90) # Peach/gold
                else:
                    py5.fill(200, 240, 255) # Cyan ridges
                
                py5.vertex(px, py, height)
        py5.end_shape()

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
