from pathlib import Path
import shutil
import subprocess
import sys
import cmath
import numpy as np
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Poincaré disk parameters
DISK_RADIUS = 500

def mobius_transform(z, a, b):
    # Möbius transformation for mapping the unit disk to itself
    # f(z) = e^{i*theta} * (z - a) / (1 - conj(a)*z)
    # We ignore rotation (e^{i*theta}) for simplicity here.
    return (z - a) / (1 - np.conj(a) * z)

def draw_hyperbolic_polygon(center, radius, points, color, t):
    # This is a highly simplified pseudo-hyperbolic drawing.
    # True hyperbolic tessellation requires finding circle intersections for lines.
    # Here we map standard polygon points through a time-varying Möbius transform.
    
    # We apply a global rotation/translation via Möbius transform
    # a determines the "center" of the transformation inside the unit disk
    a_real = 0.5 * py5.cos(t * 0.5)
    a_imag = 0.5 * py5.sin(t * 0.7)
    a = complex(a_real, a_imag)
    
    py5.fill(*color)
    py5.begin_shape()
    for i in range(points):
        angle = i * py5.TWO_PI / points
        # Original point in complex plane (relative to disk center)
        cx = center.real + radius * py5.cos(angle)
        cy = center.imag + radius * py5.sin(angle)
        z = complex(cx, cy)
        
        # Transform z through Möbius
        z_t = mobius_transform(z, a, 0)
        
        py5.vertex(z_t.real * DISK_RADIUS, z_t.imag * DISK_RADIUS)
    py5.end_shape(py5.CLOSE)

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5)
    py5.translate(py5.width / 2, py5.height / 2)
    
    # Draw outer boundary
    py5.stroke(0, 0, 100, 50)
    py5.stroke_weight(2)
    py5.no_fill()
    py5.circle(0, 0, DISK_RADIUS * 2)
    
    t = py5.frame_count * 0.015
    
    py5.stroke(0, 0, 100, 20)
    py5.stroke_weight(1)
    
    # Generate a fractal pattern inside the unit disk
    # We recursively create smaller circles towards the boundary
    # This is a simplified "flower" fractal rather than a perfect tiling
    def draw_fractal(z_center, r, depth, max_depth):
        if depth > max_depth:
            return
            
        hue = (depth * 40 + t * 50) % 360
        draw_hyperbolic_polygon(z_center, r, 6, (hue, 80, 90, 80), t)
        
        # Spawn children
        num_children = 6
        for i in range(num_children):
            angle = i * py5.TWO_PI / num_children + (t * 0.2 if depth % 2 == 0 else -t * 0.2)
            # Distance to child center
            d = r * 1.5
            child_z = z_center + complex(d * py5.cos(angle), d * py5.sin(angle))
            
            # Ensure child stays strictly inside unit disk before transformation
            if abs(child_z) + r * 0.5 < 1.0:
                draw_fractal(child_z, r * 0.45, depth + 1, max_depth)

    # Start recursion at the center of the unit disk
    draw_fractal(complex(0, 0), 0.2, 0, 4)

    # Masking out anything outside the disk just in case
    py5.no_stroke()
    py5.fill(5)
    py5.begin_shape()
    py5.vertex(-py5.width, -py5.height)
    py5.vertex(py5.width, -py5.height)
    py5.vertex(py5.width, py5.height)
    py5.vertex(-py5.width, py5.height)
    
    py5.begin_contour()
    for i in range(100):
        a = py5.TWO_PI - (i * py5.TWO_PI / 100)
        py5.vertex(py5.cos(a) * DISK_RADIUS, py5.sin(a) * DISK_RADIUS)
    py5.end_contour()
    py5.end_shape(py5.CLOSE)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
