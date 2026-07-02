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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(280, 80, 5) # Deep purple dark background
    
    time = py5.frame_count * 0.05
    
    # Draw retro sun
    py5.push_matrix()
    py5.translate(SIZE[0]/2, SIZE[1]/2 - 300, -1500)
    py5.no_stroke()
    
    # Draw sun in slices
    sun_r = 1200
    for y in range(-sun_r, sun_r, 40):
        # Calculate horizontal slice
        w = py5.sqrt(max(0, sun_r**2 - y**2)) * 2
        h = 30
        
        # Slices get thinner at the bottom, and scroll up slowly
        offset_y = (y - time * 20) % (sun_r * 2) - sun_r
        
        if offset_y > 0:
            # lower half
            if offset_y % 150 < 40:
                continue # cut out
                
        w_offset = py5.sqrt(max(0, sun_r**2 - offset_y**2)) * 2
        
        # Gradient hue
        hue = py5.remap(offset_y, -sun_r, sun_r, 50, 340)
        py5.fill(hue, 90, 100, 90)
        py5.rect(-w_offset/2, offset_y, w_offset, h)
        
    py5.pop_matrix()
    
    # Setup camera for terrain
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 100, 0)
    py5.rotate_x(py5.PI / 2.5)
    
    py5.translate(-SIZE[0]*1.5, -SIZE[1], -800)
    
    cols = 60
    rows = 60
    scl = 150
    
    py5.stroke(320, 90, 100, 80) # Neon magenta grid
    py5.fill(280, 80, 5, 90) # Dark fill to block background lines
    
    py5.stroke_weight(3)
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            # calculate noise terrain
            nx1 = x * 0.1
            ny1 = (y - time * 0.5) * 0.1
            z1 = py5.os_noise(nx1, ny1) * 600 - 300
            
            nx2 = x * 0.1
            ny2 = (y + 1 - time * 0.5) * 0.1
            z2 = py5.os_noise(nx2, ny2) * 600 - 300
            
            # Attenuate z towards the sides for a valley effect
            dist_from_center = abs(x - cols/2) / (cols/2)
            z1 += dist_from_center**2 * 800
            z2 += dist_from_center**2 * 800
            
            py5.vertex(x * scl, y * scl, z1)
            py5.vertex(x * scl, (y + 1) * scl, z2)
        py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
