from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
from scipy.spatial import Delaunay

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

NUM_NODES = 350
RADIUS = 400

# Generate nodes within a sphere
nodes = []
while len(nodes) < NUM_NODES:
    v = np.random.uniform(-RADIUS, RADIUS, 3)
    if np.linalg.norm(v) <= RADIUS:
        nodes.append(v)
nodes = np.array(nodes)

# Connect nodes using Delaunay triangulation
tri = Delaunay(nodes)
edges = set()
for simplex in tri.simplices:
    for i in range(4):
        for j in range(i+1, 4):
            # Sort to avoid duplicates
            edge = tuple(sorted([simplex[i], simplex[j]]))
            edges.add(edge)
            
edges = list(edges)

# Remove very long edges to keep it looking like a local network
filtered_edges = []
for e in edges:
    n1, n2 = nodes[e[0]], nodes[e[1]]
    if np.linalg.norm(n1 - n2) < 150:
        filtered_edges.append(e)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.sphere_detail(5)

def draw():
    py5.background(5, 5, 10) # Very dark
    
    # Lighting for nodes
    py5.ambient_light(50, 50, 80)
    py5.directional_light(200, 100, 255, 1, 1, -1)
    py5.directional_light(100, 200, 255, -1, -1, 1)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Slow rotation
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.002 + np.pi/8)
    
    t = py5.frame_count * 0.02
    
    # Draw edges
    py5.hint(py5.DISABLE_DEPTH_TEST)
    py5.blend_mode(py5.ADD)
    
    py5.stroke_weight(1.5)
    
    for e in filtered_edges:
        n1 = nodes[e[0]]
        n2 = nodes[e[1]]
        
        # Determine if this edge is active (pulsing)
        # We use a noise function based on the midpoint and time
        mid = (n1 + n2) / 2
        pulse = py5.os_noise(mid[0]*0.01, mid[1]*0.01, mid[2]*0.01 - t*3)
        
        if pulse > 0.65:
            # Hot Magenta active pulse
            intensity = int(255 * (pulse - 0.65) / 0.35)
            py5.stroke(255, 20, 147, intensity + 50)
            py5.stroke_weight(3)
        else:
            # Default Electric Blue / Deep Purple
            c_val = int(50 + 100 * pulse)
            py5.stroke(c_val, c_val // 2, 255, 60)
            py5.stroke_weight(1.5)
            
        py5.line(n1[0], n1[1], n1[2], n2[0], n2[1], n2[2])
        
    # Draw nodes
    py5.hint(py5.ENABLE_DEPTH_TEST)
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    
    for i, n in enumerate(nodes):
        py5.push_matrix()
        
        # Add slight wobble to nodes
        wobble_x = py5.os_noise(n[0]*0.02, t) * 10
        wobble_y = py5.os_noise(n[1]*0.02, t+100) * 10
        wobble_z = py5.os_noise(n[2]*0.02, t+200) * 10
        
        py5.translate(n[0] + wobble_x, n[1] + wobble_y, n[2] + wobble_z)
        
        # Node activity pulse
        node_pulse = py5.os_noise(n[0]*0.01, n[1]*0.01, n[2]*0.01 + t*2)
        
        if node_pulse > 0.7:
            py5.fill(255, 100, 255, 255)
            py5.scale(1.5 + (node_pulse - 0.7) * 3)
        else:
            py5.fill(0, 200, 255, 180)
            
        py5.sphere(4)
        py5.pop_matrix()

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
