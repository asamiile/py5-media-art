from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

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

num_nodes = 300
nodes = None
edges = []
signals = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global nodes, edges, signals
    
    nodes = np.zeros((num_nodes, 5), dtype=np.float32)
    nodes[:, 2] = np.random.uniform(0, SIZE[0], num_nodes)
    nodes[:, 3] = np.random.uniform(0, SIZE[1], num_nodes)
    nodes[:, 4] = np.random.uniform(0, py5.TWO_PI, num_nodes)
    nodes[:, 0] = nodes[:, 2]
    nodes[:, 1] = nodes[:, 3]
    
    for i in range(num_nodes):
        for j in range(i + 1, num_nodes):
            dx = nodes[i, 2] - nodes[j, 2]
            dy = nodes[i, 3] - nodes[j, 3]
            dist = np.sqrt(dx*dx + dy*dy)
            if dist < 250:
                if random.random() < 0.3: 
                    edges.append((i, j, dist))
                    
    for _ in range(150):
        spawn_signal()
        
    py5.background(5)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def spawn_signal():
    global edges, signals
    if not edges: return
    edge = random.choice(edges)
    speed = random.uniform(0.01, 0.03)
    if random.random() < 0.5:
        signals.append([edge[0], edge[1], 0.0, speed])
    else:
        signals.append([edge[1], edge[0], 0.0, speed])

def draw():
    global nodes, edges, signals
    
    py5.blend_mode(py5.BLEND)
    py5.fill(5, 10) 
    py5.no_stroke()
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    noise_scale = 0.002
    for i in range(num_nodes):
        nx = py5.os_noise(nodes[i, 2] * noise_scale, nodes[i, 3] * noise_scale, t) - 0.5
        ny = py5.os_noise(nodes[i, 2] * noise_scale + 100, nodes[i, 3] * noise_scale, t) - 0.5
        nodes[i, 0] = nodes[i, 2] + nx * 150
        nodes[i, 1] = nodes[i, 3] + ny * 150
        
    py5.stroke(200, 50, 50, 10)
    py5.stroke_weight(1)
    for e in edges:
        n1 = e[0]
        n2 = e[1]
        py5.line(nodes[n1, 0], nodes[n1, 1], nodes[n2, 0], nodes[n2, 1])
        
    py5.no_stroke()
    dead_signals = []
    for idx, s in enumerate(signals):
        s[2] += s[3] 
        
        if s[2] >= 1.0:
            dead_signals.append(idx)
            continue
            
        n1 = s[0]
        n2 = s[1]
        
        x = py5.lerp(nodes[n1, 0], nodes[n2, 0], s[2])
        y = py5.lerp(nodes[n1, 1], nodes[n2, 1], s[2])
        
        hue = (180 + s[2] * 60 + t * 50) % 360
        py5.fill(hue, 90, 100, 80)
        
        size = 3 + np.sin(s[2] * py5.PI) * 4
        py5.ellipse(x, y, size, size)
        
    for idx in reversed(dead_signals):
        signals.pop(idx)
        spawn_signal()
        
    for i in range(num_nodes):
        py5.fill((220 + i % 40) % 360, 60, 80, 40)
        size = 4 + np.sin(nodes[i, 4] + t * 5) * 2
        py5.ellipse(nodes[i, 0], nodes[i, 1], size, size)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            os._exit(1)

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
