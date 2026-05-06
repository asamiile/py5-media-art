from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Constants
MAX_LEVEL = 8
STAR_COUNT = 3000

def generate_tree(p, angle_h, angle_v, length, level):
    if level >= MAX_LEVEL:
        return []
    
    # Calculate new point
    dx = length * np.sin(angle_v) * np.cos(angle_h)
    dy = length * np.cos(angle_v)
    dz = length * np.sin(angle_v) * np.sin(angle_h)
    p_new = p + np.array([dx, dy, dz])
    
    edges = [(p, p_new, level)]
    
    # Branching
    num_branches = np.random.randint(2, 4)
    for _ in range(num_branches):
        new_angle_h = angle_h + np.random.uniform(-0.8, 0.8)
        new_angle_v = angle_v + np.random.uniform(-0.6, 0.6)
        edges.extend(generate_tree(p_new, new_angle_h, new_angle_v, length * 0.75, level + 1))
        
    return edges

def setup():
    py5.size(*SIZE, py5.P3D)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global edges, pulses, stars
    root = np.array([0.0, 400.0, 0.0])
    edges = generate_tree(root, 0, py5.PI, 200, 0) # Growing upwards
    
    # Pulses: list of (edge_index, progress, speed)
    pulses = []
    stars = np.random.uniform(-3000, 3000, (STAR_COUNT, 3))

def draw():
    global pulses
    py5.background(0, 0, 15)
    
    time_val = py5.frame_count / 60.0
    
    # Camera
    cam_dist = 1000 + py5.sin(time_val * 0.1) * 200
    py5.camera(cam_dist * py5.cos(time_val * 0.1), 
               -200 + 100 * py5.sin(time_val * 0.15), 
               cam_dist * py5.sin(time_val * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # 1. Starfield
    py5.stroke(200, 200, 255, 100)
    py5.stroke_weight(1)
    for s in stars:
        py5.point(*s)
        
    # 2. Entanglement Tree
    py5.blend_mode(py5.ADD)
    for p1, p2, level in edges:
        # Alpha based on level
        alpha = 200 / (level + 1)
        py5.stroke(0, 200, 255, alpha) # Teal
        py5.stroke_weight(1)
        py5.line(*p1, *p2)
        
        # Subtle violet glow for nodes
        if level < 5:
            py5.stroke(138, 43, 226, alpha/2)
            py5.stroke_weight(3)
            py5.point(*p2)
            
    # 3. Information Pulses
    # Spawn new pulse at root occasionally
    if py5.frame_count % 30 == 0:
        # Find root edges (edges starting at root)
        root_pos = edges[0][0]
        for i, (p1, p2, level) in enumerate(edges):
            if np.array_equal(p1, root_pos):
                pulses.append([i, 0.0, np.random.uniform(0.02, 0.05)])

    new_pulses = []
    for i, prog, speed in pulses:
        p1, p2, level = edges[i]
        # Draw pulse
        pos = p1 + (p2 - p1) * prog
        py5.stroke(255, 255, 255, 200)
        py5.stroke_weight(4)
        py5.point(*pos)
        
        # Advance
        new_prog = prog + speed
        if new_prog < 1.0:
            new_pulses.append([i, new_prog, speed])
        else:
            # Split: find child edges
            child_found = False
            for j, (cp1, cp2, clevel) in enumerate(edges):
                if np.array_equal(cp1, p2):
                    new_pulses.append([j, 0.0, speed])
                    child_found = True
            # If no child, pulse dies
    pulses = new_pulses
    
    py5.blend_mode(py5.BLEND)
    
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            "-b:v", "10M",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

py5.run_sketch()
