from pathlib import Path
import shutil
import subprocess
import sys
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

# Pre-calculate center points for the Flower of Life grid
RADIUS = 120.0
center_points = []

# Generate a hexagonal lattice
# Axial coordinates (q, r)
layers = 5 # Number of concentric hexagonal rings
for q in range(-layers, layers + 1):
    for r in range(max(-layers, -q - layers), min(layers, -q + layers) + 1):
        x = RADIUS * np.sqrt(3) * (q + r/2.0)
        y = RADIUS * 3/2.0 * r
        # Store distance from center to control the blooming animation
        dist = np.sqrt(x*x + y*y)
        center_points.append({"x": x, "y": y, "d": dist, "q": q, "r": r})

# Sort points from center to outward
center_points.sort(key=lambda p: p["d"])

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(10)
    
    # Motion blur trail
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(10, 20)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    # Slowly rotate the entire mandala
    py5.rotate_z(t * 0.1)
    py5.rotate_x(py5.sin(t * 0.2) * 0.2)
    py5.rotate_y(py5.cos(t * 0.2) * 0.2)
    
    py5.no_fill()
    py5.stroke_weight(2.5)
    
    # Dynamic blooming radius
    global_scale = py5.remap(py5.sin(t * 0.5), -1, 1, 0.9, 1.1)
    
    for i, p in enumerate(center_points):
        x = p["x"]
        y = p["y"]
        d = p["d"]
        
        # Calculate a phase offset for the blooming animation
        phase = d * 0.01 - t * 2.0
        
        # Radius pulsates and scales based on distance
        current_radius = RADIUS * global_scale * (1.0 + 0.1 * py5.sin(phase))
        
        # Color gradient from center to edge
        hue = (t * 50 + d * 0.5) % 360
        
        # Inner petals glow brighter
        brightness = py5.remap(py5.sin(phase), -1, 1, 30, 100)
        alpha = py5.remap(d, 0, RADIUS * layers * 2, 90, 0)
        
        if alpha > 0:
            py5.stroke(hue, 80, brightness, alpha)
            
            # Draw the main circle
            py5.push_matrix()
            py5.translate(x, y, py5.sin(phase) * 50) # Z-axis ripple
            
            # Draw multiple concentric rings with additive blending for neon effect
            for r_offset in [1.0, 0.9, 0.8]:
                if r_offset == 1.0:
                    py5.stroke_weight(2.5)
                else:
                    py5.stroke_weight(1.0)
                    py5.stroke(hue, 50, brightness * 0.5, alpha * 0.5)
                    
                py5.circle(0, 0, current_radius * 2 * r_offset)
                
            py5.pop_matrix()

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
