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

RESOLUTION = 7 
cols = SIZE[0] // RESOLUTION
rows = SIZE[1] // RESOLUTION

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.BLEND)
    py5.background(225, 80, 8) 
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    n = 6
    m = 10
    
    a = math.cos(loop_t)
    b = math.sin(loop_t)
    
    n2 = 4
    m2 = 8
    a2 = math.cos(loop_t * 2) * 0.4
    b2 = math.sin(loop_t * 2) * 0.4
    
    py5.no_stroke()
    py5.blend_mode(py5.ADD)
    
    scale_x = py5.PI / (SIZE[0] / 2) * 1.5
    scale_y = py5.PI / (SIZE[1] / 2) * 1.5
    
    for i in range(cols):
        for j in range(rows):
            px = i * RESOLUTION
            py = j * RESOLUTION
            
            x = (px - SIZE[0] / 2) * scale_x
            y = (py - SIZE[1] / 2) * scale_y
            
            v1 = a * math.cos(n * x) * math.cos(m * y) - b * math.cos(m * x) * math.cos(n * y)
            v2 = a2 * math.cos(n2 * x) * math.cos(m2 * y) - b2 * math.cos(m2 * x) * math.cos(n2 * y)
            v = v1 + v2
            
            val = abs(v)
            if val < 0.2:
                brightness = py5.remap(val, 0, 0.2, 255, 0)
                radius = py5.remap(val, 0, 0.2, RESOLUTION * 1.5, RESOLUTION * 0.2)
                
                noise_val = py5.noise(px * 0.05, py * 0.05, t * 5)
                
                hue = (45 + noise_val * 25) % 360
                
                py5.fill(hue, 90, 100, brightness)
                py5.circle(px + (noise_val - 0.5) * RESOLUTION * 2, py + (noise_val - 0.5) * RESOLUTION * 2, radius * (0.5 + noise_val))

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
