from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import cmath

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
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def complex_transform(z, t):
    # Droste effect mapping
    # Using complex logarithm and exponential to create infinite zoom
    # z = x + iy
    
    # Scale and twist
    scale = 1.0 + np.sin(t * 0.5) * 0.2
    twist = t * 0.2
    
    c = complex(scale, twist)
    
    try:
        # Avoid log(0)
        if abs(z) < 1e-5:
            return z
        
        # log(z) maps rings to vertical strips
        # Multiply by c scales and twists the strips
        # exp maps them back to rings
        w = cmath.exp(c * cmath.log(z))
        return w
    except:
        return z

def draw():
    # Subtle fade
    py5.blend_mode(py5.BLEND)
    py5.fill(20, 10, 5, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2)
    
    t = py5.frame_count * 0.02
    
    # Grid of polygons
    num_rings = 15
    num_segments = 24
    
    zoom_t = (t * 0.5) % 1.0
    
    py5.no_fill()
    py5.stroke_weight(2)
    
    # Draw concentric shapes
    for r_idx in range(1, num_rings + 1):
        r1 = py5.exp(r_idx - zoom_t) * 10
        r2 = py5.exp(r_idx + 1 - zoom_t) * 10
        
        py5.begin_shape(py5.QUADS)
        for s in range(num_segments):
            theta1 = (s / num_segments) * py5.TWO_PI
            theta2 = ((s + 1) / num_segments) * py5.TWO_PI
            
            z1 = complex(r1 * py5.cos(theta1), r1 * py5.sin(theta1))
            z2 = complex(r1 * py5.cos(theta2), r1 * py5.sin(theta2))
            z3 = complex(r2 * py5.cos(theta2), r2 * py5.sin(theta2))
            z4 = complex(r2 * py5.cos(theta1), r2 * py5.sin(theta1))
            
            # Apply transformation
            tz1 = complex_transform(z1, t)
            tz2 = complex_transform(z2, t)
            tz3 = complex_transform(z3, t)
            tz4 = complex_transform(z4, t)
            
            hue = (240 + r_idx * 15 + s * 10 - t * 30) % 360
            
            py5.stroke(hue, 90, 100, 60)
            py5.fill(hue, 80, 50, 15)
            
            py5.vertex(tz1.real, tz1.imag)
            py5.vertex(tz2.real, tz2.imag)
            py5.vertex(tz3.real, tz3.imag)
            py5.vertex(tz4.real, tz4.imag)
            
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
