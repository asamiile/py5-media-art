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

# Network architecture
LAYERS = 8
NODES_PER_LAYER = 60
RADIUS = 400
Z_SPACING = 150

# Pre-calculate node positions
nodes = [] # List of layers, each layer is a list of (x, y, z)
for i in range(LAYERS):
    layer_nodes = []
    z = (i - LAYERS/2 + 0.5) * Z_SPACING
    
    # We arrange nodes in a circle for each layer to form a cylinder
    for j in range(NODES_PER_LAYER):
        angle = j * py5.TWO_PI / NODES_PER_LAYER
        # Add some noise to make it look organic
        nx = py5.cos(angle)
        ny = py5.sin(angle)
        r_noise = py5.noise(nx * 0.5, ny * 0.5, i * 0.2) * 100 - 50
        r = RADIUS + r_noise
        x = r * py5.cos(angle)
        y = r * py5.sin(angle)
        layer_nodes.append((x, y, z))
    nodes.append(layer_nodes)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(5)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width / 2, py5.height / 2, -300)
    py5.rotate_y(t * 0.5)
    py5.rotate_x(py5.sin(t * 0.3) * 0.2)
    
    # Global "pulse" driving the data flow
    pulse_t = (t * 2) % LAYERS
    
    # Draw edges
    py5.stroke_weight(1)
    for i in range(LAYERS - 1):
        # Distance of this layer pair from the current pulse
        dist_to_pulse = abs(i - pulse_t)
        if dist_to_pulse > LAYERS / 2:
            dist_to_pulse = LAYERS - dist_to_pulse
            
        layer_active = max(0, 1.0 - dist_to_pulse * 0.8)
        
        hue = (i / LAYERS * 120 + t * 20 + 200) % 360
        
        # Draw connections between layer i and i+1
        # To avoid drawing 60x60=3600 lines per layer, we only connect nearest neighbors in angle
        for j1, (x1, y1, z1) in enumerate(nodes[i]):
            for j2, (x2, y2, z2) in enumerate(nodes[i+1]):
                # Angle difference
                a1 = j1 * py5.TWO_PI / NODES_PER_LAYER
                a2 = j2 * py5.TWO_PI / NODES_PER_LAYER
                diff = abs(a1 - a2)
                if diff > py5.PI: diff = py5.TWO_PI - diff
                
                if diff < py5.PI / 4:  # Only connect if angle is close
                    # Determine activity of this specific synapse using noise
                    activity = py5.noise(j1 * 0.1, j2 * 0.1, t)
                    
                    if activity > 0.4:
                        alpha = py5.remap(activity, 0.4, 1.0, 5, 40)
                        # Boost brightness if the pulse is passing through
                        alpha += layer_active * 60
                        
                        py5.stroke(hue, 80, 100, alpha)
                        py5.line(x1, y1, z1, x2, y2, z2)

    # Draw nodes
    py5.no_stroke()
    for i in range(LAYERS):
        dist_to_pulse = abs(i - pulse_t)
        if dist_to_pulse > LAYERS / 2:
            dist_to_pulse = LAYERS - dist_to_pulse
        layer_active = max(0, 1.0 - dist_to_pulse * 0.8)
        
        hue = (i / LAYERS * 120 + t * 20 + 200) % 360
        
        for j, (x, y, z) in enumerate(nodes[i]):
            activity = py5.noise(i * 0.5, j * 0.2, t * 1.5)
            
            if activity > 0.5:
                brightness = 50 + layer_active * 50
                size = 3 + layer_active * 5 + activity * 2
                
                py5.push_matrix()
                py5.translate(x, y, z)
                py5.fill(hue, 80, brightness, 80)
                
                # We use points/spheres based on distance
                # Just draw a quad facing the camera (billboard) for speed instead of sphere
                py5.rect_mode(py5.CENTER)
                py5.rect(0, 0, size, size)
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
