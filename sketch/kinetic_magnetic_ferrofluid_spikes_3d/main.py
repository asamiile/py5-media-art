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
    py5.no_stroke()

def draw():
    py5.background(10, 10, 15)
    
    # Lighting for the shiny ferrofluid look
    py5.ambient_light(200, 50, 20)
    py5.directional_light(0, 0, 100, 1, 1, -1)
    py5.directional_light(240, 80, 80, -1, -1, -1)
    py5.light_specular(0, 0, 100)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    py5.rotate_y(t * 0.5)
    py5.rotate_x(t * 0.2)
    
    py5.specular(255)
    py5.shininess(50)
    py5.fill(0, 0, 10) # Very dark grey/black
    
    r = 200
    res = 60
    
    # We will build a distorted sphere using triangle strips
    for i in range(res):
        lat0 = py5.PI * (-0.5 + float(i) / res)
        z0  = py5.sin(lat0)
        zr0 = py5.cos(lat0)
        
        lat1 = py5.PI * (-0.5 + float(i+1) / res)
        z1  = py5.sin(lat1)
        zr1 = py5.cos(lat1)
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(res + 1):
            lng = py5.TWO_PI * float(j) / res
            x = py5.cos(lng)
            y = py5.sin(lng)
            
            # Point 0
            nx0 = x * zr0
            ny0 = y * zr0
            nz0 = z0
            
            # Displacement using 3D noise
            noise0 = py5.os_noise(nx0 * 3, ny0 * 3, nz0 * 3 + t)
            # Threshold noise to create spikes
            spike0 = py5.remap(max(0, noise0 - 0.4), 0, 0.6, 0, 150)
            
            r0 = r + spike0
            py5.normal(nx0, ny0, nz0)
            py5.vertex(nx0 * r0, ny0 * r0, nz0 * r0)
            
            # Point 1
            nx1 = x * zr1
            ny1 = y * zr1
            nz1 = z1
            
            noise1 = py5.os_noise(nx1 * 3, ny1 * 3, nz1 * 3 + t)
            spike1 = py5.remap(max(0, noise1 - 0.4), 0, 0.6, 0, 150)
            
            r1 = r + spike1
            py5.normal(nx1, ny1, nz1)
            py5.vertex(nx1 * r1, ny1 * r1, nz1 * r1)
            
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
