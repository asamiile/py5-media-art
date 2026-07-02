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
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.02
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.PI / 6)
    
    # Draw the central prism
    py5.stroke(0, 0, 100, 80)
    py5.stroke_weight(2)
    py5.fill(200, 30, 100, 10)
    
    h = 300
    r = 200
    
    # Vertices of a triangular prism
    top = [(r * py5.cos(a), -h/2, r * py5.sin(a)) for a in (0, py5.TWO_PI/3, 2*py5.TWO_PI/3)]
    bot = [(r * py5.cos(a), h/2, r * py5.sin(a)) for a in (0, py5.TWO_PI/3, 2*py5.TWO_PI/3)]
    
    # Draw faces
    py5.begin_shape(py5.TRIANGLES)
    # Top and bottom
    for p in top: py5.vertex(*p)
    for p in bot: py5.vertex(*p)
    # Sides
    for i in range(3):
        j = (i + 1) % 3
        py5.vertex(*top[i])
        py5.vertex(*bot[i])
        py5.vertex(*bot[j])
        
        py5.vertex(*top[i])
        py5.vertex(*bot[j])
        py5.vertex(*top[j])
    py5.end_shape()

    # Draw scattering spectral light beams
    num_beams = 100
    py5.stroke_weight(3)
    
    for i in range(num_beams):
        idx = i / num_beams
        hue = (idx * 300 + t * 20) % 360 # Spread colors across spectrum
        
        # Origin point in the prism core
        ox = py5.os_noise(i, t * 0.5) * 100 - 50
        oy = py5.os_noise(i+100, t * 0.5) * 100 - 50
        oz = py5.os_noise(i+200, t * 0.5) * 100 - 50
        
        # Direction
        phi = py5.remap(py5.os_noise(i*2, t*0.1), 0, 1, 0, py5.PI)
        theta = py5.remap(py5.os_noise(i*3, t*0.1), 0, 1, 0, py5.TWO_PI)
        
        length = 800 + py5.os_noise(i*4, t*0.2) * 400
        
        dx = length * py5.sin(phi) * py5.cos(theta)
        dy = length * py5.cos(phi)
        dz = length * py5.sin(phi) * py5.sin(theta)
        
        py5.stroke(hue, 90, 100, 60)
        py5.line(ox, oy, oz, ox + dx, oy + dy, oz + dz)


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
