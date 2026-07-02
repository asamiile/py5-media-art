from pathlib import Path
import shutil
import subprocess
import sys
import py5
import random

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

# Keep track of points in polar coordinates
# (radius, angle)
web_points = []
num_rings = 40
num_spokes = 30

def setup():
    py5.size(*SIZE, py5.P2D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize the web
    for r_idx in range(1, num_rings + 1):
        radius = r_idx * 50
        for s_idx in range(num_spokes):
            angle = (py5.TWO_PI / num_spokes) * s_idx
            # Add some jitter
            jitter_r = random.uniform(-10, 10)
            jitter_a = random.uniform(-0.05, 0.05)
            web_points.append({"r": radius + jitter_r, "a": angle + jitter_a})

def draw():
    py5.background(5, 10, 15)
    
    py5.translate(SIZE[0]/2, SIZE[1]/2)
    
    time_val = py5.frame_count * 0.01
    
    # Slowly zoom in and spin
    # We want a continuous zoom effect. 
    # Scale by e^(time_val) gives exponential zoom, but we reset the view by looping points
    zoom = 1.0 + (py5.frame_count % 120) * 0.01 # Pulsing zoom or continuous
    
    # Actually, continuous infinite zoom is hard without recreating points dynamically. 
    # Let's just do a heavy scaling and we'll rely on the depth of the 40 rings.
    zoom_factor = 1.0 + time_val * 0.5
    py5.scale(zoom_factor)
    py5.rotate(time_val * 0.2)
    
    py5.blend_mode(py5.ADD)
    
    # Calculate cartesian coordinates once per frame
    cart_points = []
    for p in web_points:
        x = py5.cos(p["a"]) * p["r"]
        y = py5.sin(p["a"]) * p["r"]
        cart_points.append((x, y, p["r"]))
        
    py5.stroke_weight(1)
    
    # Draw connections
    for i, p1 in enumerate(cart_points):
        x1, y1, r1 = p1
        
        # Don't draw if it's way outside the screen or way too small
        if r1 * zoom_factor > SIZE[0] * 2 or r1 * zoom_factor < 10:
            continue
            
        hue = (time_val * 50 + r1 * 0.2) % 360
        
        # Find close points to connect
        connections = 0
        for j, p2 in enumerate(cart_points):
            if i == j: continue
            
            x2, y2, r2 = p2
            
            dx = x1 - x2
            dy = y1 - y2
            dist_sq = dx*dx + dy*dy
            
            if dist_sq < 6000: # Threshold for connection
                alpha = py5.remap(dist_sq, 0, 6000, 200, 0)
                py5.stroke(hue, 80, 100, alpha)
                py5.line(x1, y1, x2, y2)
                connections += 1
                if connections > 4: # Max connections per point
                    break

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
