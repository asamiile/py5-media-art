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
DURATION_SEC = random.randint(15, 20)  # Random duration up to 20s
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw_kaleidoscope(t, offset, color):
    num_petals = 12
    py5.fill(*color)
    py5.no_stroke()
    
    # We use 2D rotation for the petals
    for i in range(num_petals):
        angle = i * (py5.TWO_PI / num_petals)
        with py5.push_matrix():
            py5.rotate(angle)
            
            # Draw something complex
            for j in range(5):
                r = py5.noise(t * 0.5, i * 0.1, j * 0.2) * 500 + 100
                theta = py5.noise(t * 0.3 + 10, i * 0.1, j * 0.2) * py5.TWO_PI
                size = py5.noise(t * 0.8 + 20, i * 0.1, j * 0.2) * 150 + 20
                
                # Apply offset based on the channel
                x = math.cos(theta) * r + offset[0] * r * 0.05
                y = math.sin(theta) * r + offset[1] * r * 0.05
                
                with py5.push_matrix():
                    py5.translate(x, y)
                    py5.rotate(t + j)
                    # draw a sharp polygon
                    py5.begin_shape()
                    for k in range(3):
                        py5.vertex(math.cos(k * py5.TWO_PI / 3) * size, math.sin(k * py5.TWO_PI / 3) * size)
                    py5.end_shape(py5.CLOSE)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    t = py5.frame_count * 0.01
    
    # Slow rotation of the entire view
    py5.rotate(t * 0.5)
    
    # Calculate offset for chromatic aberration based on time
    ox = math.sin(t * 2) * 1.5
    oy = math.cos(t * 2.3) * 1.5
    
    draw_kaleidoscope(t, (-ox, -oy), (255, 0, 0, 150))
    draw_kaleidoscope(t, (0, 0), (0, 255, 0, 150))
    draw_kaleidoscope(t, (ox, oy), (0, 0, 255, 150))

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
