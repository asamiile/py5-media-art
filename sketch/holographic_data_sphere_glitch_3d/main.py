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
DURATION_SEC = 10
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
    py5.text_font(py5.create_font("Courier New", 24))
    py5.text_align(py5.CENTER, py5.CENTER)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -400)
    
    t = py5.frame_count * 0.015
    py5.rotate_y(t)
    py5.rotate_x(py5.sin(t * 0.5) * 0.5)
    
    num_latitudes = 30
    num_longitudes = 60
    radius = 500
    
    for i in range(num_latitudes):
        lat = py5.remap(i, 0, num_latitudes, 0, py5.PI)
        
        # Add glitchy banding effect
        is_glitched = py5.os_noise(i * 0.1, t * 5) > 0.7
        glitch_offset = py5.os_noise(i * 0.2, t * 10) * 100 if is_glitched else 0
        
        for j in range(num_longitudes):
            lon = py5.remap(j, 0, num_longitudes, 0, py5.TWO_PI)
            
            x = (radius + glitch_offset) * py5.sin(lat) * py5.cos(lon + (t if i % 2 == 0 else -t))
            y = (radius + glitch_offset) * py5.cos(lat)
            z = (radius + glitch_offset) * py5.sin(lat) * py5.sin(lon + (t if i % 2 == 0 else -t))
            
            py5.push_matrix()
            py5.translate(x, y, z)
            
            # Orient text to face outward
            py5.rotate_y(-lon - (t if i % 2 == 0 else -t) + py5.PI/2)
            py5.rotate_x(-lat + py5.PI/2)
            
            if is_glitched:
                hue = (0 + py5.random(60)) % 360 # Red/Orange error
                py5.fill(hue, 90, 100, 90)
                char_idx = int(py5.random(33, 126))
            else:
                hue = (180 + py5.sin(lat*2 + lon + t*2)*40) % 360 # Cyan/Blue data
                py5.fill(hue, 90, 80, 70)
                char_idx = 48 + int(py5.os_noise(i, j, t) * 2) # 0 or 1
            
            py5.text(chr(char_idx), 0, 0)
            py5.pop_matrix()
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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
