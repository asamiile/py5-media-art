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

R = 100 # Base radius of circles
LAYERS = 6 # Number of concentric hexagonal rings
nodes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate the nodes for a hexagonal grid (Flower of Life pattern)
    # Center node
    nodes.append((0, 0))
    
    for layer in range(1, LAYERS + 1):
        # Move to the first node of this layer (straight up in a hex grid, or angle 0)
        curr_x = layer * R * py5.cos(0)
        curr_y = layer * R * py5.sin(0)
        
        # Walk the hexagon
        for side in range(6):
            # Direction to move along this side
            angle = side * (py5.PI / 3) + (py5.PI * 2 / 3)
            dx = R * py5.cos(angle)
            dy = R * py5.sin(angle)
            
            for step in range(layer):
                nodes.append((curr_x, curr_y))
                curr_x += dx
                curr_y += dy
                
def draw():
    py5.background(10)
    
    # Add some subtle post-processing accumulation/blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(5, 5, 15, 30)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    t = py5.frame_count * 0.03
    
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    # Slow majestic rotation
    py5.rotate_z(t * 0.1)
    
    for i, (nx, ny) in enumerate(nodes):
        dist_from_center = np.sqrt(nx**2 + ny**2)
        
        # Calculate wave phase based on distance from center and time
        phase = dist_from_center * 0.01 - t * 2
        
        # Radius oscillates around the base R
        # It expands and contracts, creating overlapping interference patterns
        wave_val = py5.sin(phase)
        current_r = R * (1.0 + wave_val * 0.6)
        
        # Dynamic color based on position in wave
        hue = (dist_from_center * 0.5 - t * 50) % 360
        brightness = py5.remap(wave_val, -1, 1, 40, 100)
        
        py5.stroke(hue, 80, brightness, 80)
        py5.stroke_weight(py5.remap(wave_val, -1, 1, 1, 5))
        
        py5.push_matrix()
        py5.translate(nx, ny, py5.sin(phase * 0.5) * 50) # Slight 3D displacement
        
        py5.circle(0, 0, current_r * 2)
        
        # Draw an inner geometric connection point
        if wave_val > 0.8:
            py5.stroke(0, 0, 100, 90)
            py5.stroke_weight(2)
            py5.point(0, 0, 0)
            
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
