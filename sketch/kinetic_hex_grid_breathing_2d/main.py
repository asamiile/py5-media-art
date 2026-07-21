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

R = 40.0
W = np.sqrt(3) * R
H = 1.5 * R
cols = int(SIZE[0] / W) + 3
rows = int(SIZE[1] / H) + 3

def draw_hex(radius):
    py5.begin_shape()
    for i in range(6):
        angle = py5.TWO_PI / 6 * i - py5.PI / 2
        py5.vertex(np.cos(angle) * radius, np.sin(angle) * radius)
    py5.end_shape(py5.CLOSE)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10, 5, 20)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.015
    
    # Noise offset for the entire grid to simulate flowing motion
    global_offset_x = time * 0.5
    global_offset_y = time * 0.3
    
    py5.no_fill()
    py5.stroke_weight(2.0)
    
    for r in range(-2, rows):
        for c in range(-2, cols):
            x = c * W + (W / 2 if r % 2 == 1 else 0)
            y = r * H
            
            # Sample noise for this specific hexagon
            n1 = py5.os_noise(x * 0.002 + global_offset_x, y * 0.002 + global_offset_y, time * 0.5)
            n2 = py5.os_noise(x * 0.004 - global_offset_x, y * 0.004 - global_offset_y, time * 0.3)
            
            # Determine base color from noise
            if n1 < -0.2:
                col = (0, 255, 255, 180) # Cyan
            elif n1 > 0.2:
                col = (255, 0, 255, 180) # Magenta
            else:
                col = (255, 200, 0, 180) # Yellow
                
            py5.push_matrix()
            py5.translate(x, y)
            
            # Rotation driven by noise
            rotation = n2 * py5.PI
            
            # Draw nested hexagons
            for i, scale_factor in enumerate([0.9, 0.6, 0.3]):
                py5.push_matrix()
                # Inner hexagons rotate in opposite directions or at different speeds
                dir_mult = 1 if i % 2 == 0 else -1
                py5.rotate(rotation * dir_mult * (i + 1))
                
                # Scale driven by noise to create "breathing"
                s = py5.remap(n1, -1, 1, 0.2, 1.2)
                current_r = R * scale_factor * s
                
                # Fade out smaller hexagons if they get too small
                alpha_mult = py5.constrain(py5.remap(current_r, 2, 15, 0, 1), 0, 1)
                py5.stroke(col[0], col[1], col[2], col[3] * alpha_mult)
                
                draw_hex(current_r)
                py5.pop_matrix()
                
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
