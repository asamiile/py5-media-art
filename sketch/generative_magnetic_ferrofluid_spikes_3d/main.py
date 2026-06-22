from pathlib import Path
import shutil
import subprocess
import sys
import random
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
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.sphere_detail(120)

def draw():
    py5.background(0, 0, 5) # Very dark background
    
    # Lighting to create glossy ferrofluid look
    py5.ambient_light(0, 0, 20)
    py5.directional_light(200, 50, 100, 1, 1, -1)
    py5.point_light(320, 80, 100, -SIZE[0]/2, -SIZE[1]/2, 500)
    py5.light_specular(0, 0, 100)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, 0)
    
    # Camera / object rotation
    py5.rotate_y(py5.frame_count * 0.01)
    py5.rotate_x(py5.sin(py5.frame_count * 0.005) * 0.5)
    
    py5.specular(0, 0, 100)
    py5.shininess(50)
    
    # Render deformed sphere manually using triangle strips to displace vertices
    radius = SIZE[1] * 0.25
    detail = 80
    
    for i in range(detail):
        lat0 = py5.PI * (-0.5 + float(i - 1) / detail)
        z0 = py5.sin(lat0)
        zr0 = py5.cos(lat0)
        
        lat1 = py5.PI * (-0.5 + float(i) / detail)
        z1 = py5.sin(lat1)
        zr1 = py5.cos(lat1)
        
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(detail + 1):
            lng = py5.TWO_PI * float(j - 1) / detail
            x = py5.cos(lng)
            y = py5.sin(lng)
            
            # Vertex 0
            vx0 = x * zr0
            vy0 = y * zr0
            vz0 = z0
            
            # Deformation based on 3D noise (simulating magnetic spikes)
            n_val0 = py5.os_noise(vx0 * 2 + py5.frame_count * 0.01, vy0 * 2, vz0 * 2 + py5.frame_count * 0.01)
            spike0 = pow(n_val0, 4) * 300 # Sharp spikes
            
            v_radius0 = radius + spike0
            
            # Base color is dark glossy black, tips glow with neon
            hue0 = (280 + spike0 * 0.5 + py5.frame_count * 0.5) % 360
            py5.fill(hue0, 80, min(10 + spike0 * 0.5, 100))
            py5.no_stroke()
            
            py5.normal(vx0, vy0, vz0)
            py5.vertex(vx0 * v_radius0, vy0 * v_radius0, vz0 * v_radius0)
            
            # Vertex 1
            vx1 = x * zr1
            vy1 = y * zr1
            vz1 = z1
            
            n_val1 = py5.os_noise(vx1 * 2 + py5.frame_count * 0.01, vy1 * 2, vz1 * 2 + py5.frame_count * 0.01)
            spike1 = pow(n_val1, 4) * 300
            
            v_radius1 = radius + spike1
            
            hue1 = (280 + spike1 * 0.5 + py5.frame_count * 0.5) % 360
            py5.fill(hue1, 80, min(10 + spike1 * 0.5, 100))
            py5.normal(vx1, vy1, vz1)
            py5.vertex(vx1 * v_radius1, vy1 * v_radius1, vz1 * v_radius1)
            
        py5.end_shape()
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

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
