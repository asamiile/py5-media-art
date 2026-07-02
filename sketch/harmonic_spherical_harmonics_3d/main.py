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
DURATION_SEC = 10  # 10 seconds
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

def spherical_harmonic(m, l, theta, phi):
    r1 = py5.sin(m * theta) * py5.cos(l * phi)
    r2 = py5.sin(l * theta) * py5.cos(m * phi)
    return abs(r1 + r2)

def draw():
    py5.background(0)
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Smooth rotation
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_x(py5.frame_count * 0.003)
    py5.rotate_z(py5.frame_count * 0.002)
    
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    # Smooth parameter animation over the total frames
    t = (py5.frame_count / TOTAL_FRAMES) * py5.TWO_PI
    m = 3 + py5.sin(t) * 2
    l = 4 + py5.cos(t * 2) * 2
    
    base_radius = min(py5.width, py5.height) * 0.25
    
    res = 80  # Lower resolution for performance, still looks good with additive blending
    for i in range(res):
        lat0 = py5.PI * (-0.5 + float(i) / res)
        z0 = py5.sin(lat0)
        zr0 = py5.cos(lat0)
        
        lat1 = py5.PI * (-0.5 + float(i + 1) / res)
        z1 = py5.sin(lat1)
        zr1 = py5.cos(lat1)
        
        py5.begin_shape(py5.QUAD_STRIP)
        for j in range(res + 1):
            lng = py5.TWO_PI * float(j) / res
            x = py5.cos(lng)
            y = py5.sin(lng)
            
            theta0 = lat0 + py5.PI/2
            phi0 = lng
            rad0 = base_radius * (1 + 0.8 * spherical_harmonic(m, l, theta0, phi0))
            
            px0 = x * zr0 * rad0
            py0 = y * zr0 * rad0
            pz0 = z0 * rad0
            
            hue0 = (py5.degrees(phi0) * 2 + py5.frame_count) % 360
            py5.fill(hue0, 80, min(100, rad0/base_radius * 40), 40)
            py5.vertex(px0, py0, pz0)
            
            theta1 = lat1 + py5.PI/2
            phi1 = lng
            rad1 = base_radius * (1 + 0.8 * spherical_harmonic(m, l, theta1, phi1))
            
            px1 = x * zr1 * rad1
            py1 = y * zr1 * rad1
            pz1 = z1 * rad1
            
            hue1 = (py5.degrees(phi1) * 2 + py5.frame_count) % 360
            py5.fill(hue1, 80, min(100, rad1/base_radius * 40), 40)
            py5.vertex(px1, py1, pz1)
            
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
