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
    py5.background(15, 10, 15)
    py5.blend_mode(py5.BLEND)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.2)
    
    py5.no_stroke()
    
    num_ribbons = 8
    ribbon_length = 200
    
    for r in range(num_ribbons):
        py5.begin_shape(py5.QUAD_STRIP)
        
        angle_offset = (py5.TWO_PI / num_ribbons) * r
        
        for i in range(ribbon_length):
            # Parametric coordinates for the ribbon path
            z = py5.remap(i, 0, ribbon_length, -600, 600)
            
            # Twisting radius
            radius = 150 + py5.sin(z * 0.01 + t) * 50
            
            # The twist angle
            angle = z * 0.02 + angle_offset + t
            
            x1 = py5.cos(angle) * radius
            y1 = py5.sin(angle) * radius
            
            # Ribbon width
            w = 40 + py5.sin(z * 0.05 - t * 2) * 20
            
            # Normal for the ribbon width (tangent to the circle)
            dx = py5.cos(angle + py5.PI/2) * w
            dy = py5.sin(angle + py5.PI/2) * w
            
            hue = (i + r * 30 + t * 20) % 360
            py5.fill(hue, 80, 90, 60)
            
            py5.vertex(x1 - dx, y1 - dy, z)
            py5.vertex(x1 + dx, y1 + dy, z)
            
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
