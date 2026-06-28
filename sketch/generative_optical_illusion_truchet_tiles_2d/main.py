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
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.no_fill()
    py5.stroke_weight(12)
    py5.stroke_cap(py5.SQUARE)

def draw_tile(x, y, s, t):
    py5.push_matrix()
    py5.translate(x + s/2, y + s/2)
    
    # Noise determines rotation
    noise_val = py5.os_noise(x * 0.002, y * 0.002, t)
    
    # Smooth step for flipping 90 degrees
    # Scale noise to an angle multiplier
    angle_mult = py5.remap(math.sin(noise_val * py5.TWO_PI), -1, 1, 0, 1)
    
    # Snap to nearest 90 degrees but animate smoothly between them
    target = round(angle_mult)
    diff = angle_mult - target
    # smooth it out slightly
    eased_angle = target + diff * 0.5
    
    py5.rotate(eased_angle * py5.HALF_PI)
    
    # Draw standard Truchet arcs
    py5.translate(-s/2, -s/2)
    
    # Color based on position and time
    hue = (x * 0.05 + y * 0.05 + py5.frame_count * 0.5) % 360
    py5.stroke(hue, 80, 100)
    
    py5.arc(0, 0, s, s, 0, py5.HALF_PI)
    py5.arc(s, s, s, s, py5.PI, py5.PI + py5.HALF_PI)
    
    py5.pop_matrix()

def draw():
    py5.background(15, 80, 15)
    
    t = py5.frame_count * 0.02
    
    tile_size = 120
    
    for x in range(0, py5.width, tile_size):
        for y in range(0, py5.height, tile_size):
            draw_tile(x, y, tile_size, t)

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
