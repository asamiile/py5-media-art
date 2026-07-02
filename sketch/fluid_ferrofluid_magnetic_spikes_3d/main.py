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

def draw():
    py5.background(10)
    
    # Lighting to make it look shiny/metallic
    py5.ambient_light(30, 30, 30)
    py5.directional_light(0, 0, 100, 0, 1, -1)
    py5.point_light(220, 80, 100, py5.width/2 - 200, py5.height/2 - 200, 200)
    py5.point_light(280, 80, 100, py5.width/2 + 200, py5.height/2 + 200, 200)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    py5.rotate_x(t * 0.2)
    py5.rotate_y(t * 0.3)
    
    py5.no_stroke()
    
    # We will draw a sphere using a 2D grid of angles (theta, phi)
    cols = 80
    rows = 40
    r_base = 250
    
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
            
            # Use 3D noise to displace the radius
            # Create spiked effect by cubing/squaring the noise
            n0 = py5.os_noise(x * zr0 * 2 + t*0.5, y * zr0 * 2, z0 * 2 + t)
            n1 = py5.os_noise(x * zr1 * 2 + t*0.5, y * zr1 * 2, z1 * 2 + t)
            
            # Threshold noise to create spikes
            spike0 = pow(n0, 3) * 300
            spike1 = pow(n1, 3) * 300
            
            r0 = r_base + spike0
            r1 = r_base + spike1
            
            hue0 = (240 + spike0 * 0.5) % 360
            hue1 = (240 + spike1 * 0.5) % 360
            
            py5.fill(hue0, 90, 80)
            py5.vertex(x * zr0 * r0, y * zr0 * r0, z0 * r0)
            
            py5.fill(hue1, 90, 80)
            py5.vertex(x * zr1 * r1, y * zr1 * r1, z1 * r1)
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
