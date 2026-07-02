from pathlib import Path
import shutil
import subprocess
import sys
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

NUM_RIBBONS = 20
SEGMENTS = 100

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion blur trail
    py5.no_stroke()
    py5.fill(10, 10, 15, 30)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    time_val = py5.frame_count * 0.015
    
    for i in range(NUM_RIBBONS):
        # Calculate ribbon base y and color
        base_y = py5.remap(i, 0, NUM_RIBBONS, SIZE[1] * 0.1, SIZE[1] * 0.9)
        hue = (i * (360 / NUM_RIBBONS) + time_val * 50) % 360
        
        # Ribbon style
        py5.fill(hue, 80, 100, 80)
        py5.stroke(hue, 60, 100, 150)
        py5.stroke_weight(1)
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(SEGMENTS + 1):
            # Calculate x position along the screen
            x = py5.remap(j, 0, SEGMENTS, -SIZE[0] * 0.1, SIZE[0] * 1.1)
            
            # Complex motion for the ribbon
            noise_val = py5.os_noise(x * 0.002, base_y * 0.01, time_val)
            y_offset = py5.sin(x * 0.005 + time_val * 2 + i * 0.2) * 200 * noise_val
            
            y = base_y + y_offset
            
            # Ribbon thickness varies with noise to simulate twisting
            thickness = py5.remap(py5.cos(x * 0.01 - time_val * 3 + i), -1, 1, 2, 40)
            
            # Add vertices for the top and bottom of the ribbon
            py5.vertex(x, y - thickness/2)
            py5.vertex(x, y + thickness/2)
            
        py5.end_shape()

    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
