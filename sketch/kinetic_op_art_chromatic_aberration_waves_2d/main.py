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

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.blend_mode(py5.BLEND)
    py5.background(10, 10, 10) 
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    py5.stroke_weight(4)
    py5.no_fill()
    
    num_lines = 150
    steps = 120 
    
    passes = [
        (255, 30, 30, 0.0),    
        (30, 255, 30, 0.05),   
        (30, 30, 255, 0.1)     
    ]
    
    for r, g, b, p_offset in passes:
        py5.stroke(r, g, b, 200)
        
        for i in range(num_lines):
            x_base = (i / (num_lines - 1)) * SIZE[0]
            
            py5.begin_shape()
            for j in range(steps + 1):
                y = (j / steps) * SIZE[1]
                
                dist_center_y = (y - SIZE[1]/2) / SIZE[1]
                dist_center_x = (x_base - SIZE[0]/2) / SIZE[0]
                
                envelope = max(0, 1.0 - math.sqrt(dist_center_x**2 + dist_center_y**2) * 1.5)
                # Apply smoothstep-like easing to envelope
                envelope = envelope * envelope * (3 - 2 * envelope)
                
                wave1 = math.sin(y * 0.005 + loop_t + p_offset * py5.TWO_PI)
                wave2 = math.cos(x_base * 0.01 - y * 0.01 + loop_t * 2 + p_offset * py5.TWO_PI)
                wave3 = math.sin(x_base * 0.003 + y * 0.008 - loop_t * 1.5)
                
                x_distortion = (wave1 + wave2 + wave3) * envelope * 250.0
                
                py5.vertex(x_base + x_distortion, y)
                
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
