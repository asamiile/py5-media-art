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
    py5.sphere_detail(12)

def draw():
    py5.background(10, 5, 10)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.03
    py5.rotate_z(py5.PI / 6)
    py5.rotate_y(t)
    
    num_pairs = 120
    spacing = 15
    radius = 150
    
    py5.translate(0, -num_pairs * spacing / 2, 0)
    
    for i in range(num_pairs):
        y = i * spacing
        angle = i * 0.15 + t
        
        # Strand 1
        x1 = radius * py5.cos(angle)
        z1 = radius * py5.sin(angle)
        
        # Strand 2
        x2 = radius * py5.cos(angle + py5.PI)
        z2 = radius * py5.sin(angle + py5.PI)
        
        glitch = py5.os_noise(i * 0.1, t * 2) > 0.8
        
        # Draw spheres for strand 1
        py5.push_matrix()
        py5.translate(x1, y, z1)
        py5.no_stroke()
        hue1 = 180 if not glitch else (0 + py5.random(60)) % 360
        py5.fill(hue1, 90, 100, 80)
        py5.sphere(6)
        py5.pop_matrix()
        
        # Draw spheres for strand 2
        py5.push_matrix()
        py5.translate(x2, y, z2)
        py5.no_stroke()
        hue2 = 300 if not glitch else (0 + py5.random(60)) % 360
        py5.fill(hue2, 90, 100, 80)
        py5.sphere(6)
        py5.pop_matrix()
        
        # Draw connecting base pair line
        if not glitch:
            py5.stroke(240, 50, 100, 40)
            py5.stroke_weight(2)
            py5.line(x1, y, z1, x2, y, z2)
        else:
            # Glitchy connection
            py5.stroke(60, 90, 100, 60)
            py5.stroke_weight(3)
            # Offset x2 slightly for glitch
            py5.line(x1, y, z1, x2 + 50, y, z2 - 20)


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
