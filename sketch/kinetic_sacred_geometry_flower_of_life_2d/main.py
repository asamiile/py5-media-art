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
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    py5.blend_mode(py5.BLEND)
    py5.background(250, 95, 3) 
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count / TOTAL_FRAMES
    loop_t = t * py5.TWO_PI
    
    D = 220 
    
    dy = D * math.sqrt(3) / 2
    
    cols = int(SIZE[0] / D) + 6
    rows = int(SIZE[1] / dy) + 6
    
    py5.no_fill()
    py5.stroke_weight(4)
    
    cx_screen = SIZE[0] / 2
    cy_screen = SIZE[1] / 2
    
    # Global rotation for hypnotic effect
    py5.translate(cx_screen, cy_screen)
    py5.rotate(math.sin(loop_t) * 0.1)
    py5.translate(-cx_screen, -cy_screen)
    
    for row in range(-rows//2, rows//2 + 1):
        for col in range(-cols//2, cols//2 + 1):
            
            x = cx_screen + col * D
            if row % 2 != 0:
                x += D / 2
                
            y = cy_screen + row * dy
            
            dist = math.hypot(x - cx_screen, y - cy_screen)
            
            # Rippling radius wave 
            wave = math.sin(dist * 0.003 - loop_t * 2)
            
            # To preserve the Flower of Life overlapping seed pattern, 
            # we need some circles to remain exactly at R=D, and maybe just animate thickness?
            # Or animating the radius slightly creates a breathing flower
            R = D * (1.0 + wave * 0.12)
            
            # Rainbow gradient expanding outward
            hue = (200 + dist * 0.08 - t * 360 * 2) % 360
            
            alpha = py5.remap(dist, 0, SIZE[1], 255, 0)
            if alpha < 0: alpha = 0
            
            if -R * 2 < x < SIZE[0] + R * 2 and -R * 2 < y < SIZE[1] + R * 2:
                # Main circle
                py5.stroke(hue, 85, 95, alpha)
                py5.circle(x, y, R * 2)
                
                # Secondary inner circle
                py5.stroke((hue + 180) % 360, 85, 95, alpha * 0.5)
                py5.circle(x, y, R * 1.5)

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
