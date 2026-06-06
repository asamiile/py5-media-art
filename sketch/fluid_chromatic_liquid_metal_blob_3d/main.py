from pathlib import Path
import shutil
import subprocess
import sys
import py5
import math

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

def draw():
    py5.background(10)
    
    # Complex lighting to make it look metallic and shiny
    py5.ambient_light(40, 40, 40)
    py5.directional_light(0, 0, 100, 0, 1, -1)
    py5.point_light(200, 80, 100, py5.width/2 - 400, py5.height/2 - 400, 400)
    py5.point_light(320, 80, 100, py5.width/2 + 400, py5.height/2 + 400, 400)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    py5.rotate_x(t * 0.2)
    py5.rotate_y(t * 0.3)
    
    py5.no_stroke()
    
    cols = 80
    rows = 40
    r_base = 350
    
    for i in range(rows):
        lat0 = py5.PI * (-0.5 + float(i - 1) / rows)
        z0  = py5.sin(lat0)
        zr0 = py5.cos(lat0)
        
        lat1 = py5.PI * (-0.5 + float(i) / rows)
        z1 = py5.sin(lat1)
        zr1 = py5.cos(lat1)
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(cols + 1):
            lng = py5.TWO_PI * float(j - 1) / cols
            x = py5.cos(lng)
            y = py5.sin(lng)
            
            # Smooth low-frequency noise for big blobs
            n0 = py5.os_noise(x * zr0 * 1.5 + t*0.5, y * zr0 * 1.5, z0 * 1.5 + t)
            n1 = py5.os_noise(x * zr1 * 1.5 + t*0.5, y * zr1 * 1.5, z1 * 1.5 + t)
            
            # High-frequency noise for ripples
            n0_high = py5.os_noise(x * zr0 * 4 - t, y * zr0 * 4, z0 * 4) * 0.2
            n1_high = py5.os_noise(x * zr1 * 4 - t, y * zr1 * 4, z1 * 4) * 0.2
            
            r0 = r_base + n0 * 200 + n0_high * 100
            r1 = r_base + n1 * 200 + n1_high * 100
            
            # Chromatic shifting color mapped to the noise value
            hue0 = (n0 * 360 * 2 + t * 20) % 360
            hue1 = (n1 * 360 * 2 + t * 20) % 360
            
            py5.fill(hue0, 90, 90)
            py5.vertex(x * zr0 * r0, y * zr0 * r0, z0 * r0)
            
            py5.fill(hue1, 90, 90)
            py5.vertex(x * zr1 * r1, y * zr1 * r1, z1 * r1)
        py5.end_shape()

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2. Aborting.")
            import os
            os._exit(1)

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
