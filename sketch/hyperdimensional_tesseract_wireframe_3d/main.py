from pathlib import Path
import shutil
import subprocess
import sys
import math
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
DURATION_SEC = 12
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# 4D Hypercube vertices (16 points)
vertices_4d = []
for i in range(16):
    x = (i & 1) * 2 - 1
    y = ((i >> 1) & 1) * 2 - 1
    z = ((i >> 2) & 1) * 2 - 1
    w = ((i >> 3) & 1) * 2 - 1
    vertices_4d.append([x, y, z, w])

# Edges (connect points differing by exactly 1 bit)
edges = []
for i in range(16):
    for j in range(4):
        neighbor = i ^ (1 << j)
        if i < neighbor:
            edges.append((i, neighbor))

def matmul(a, b):
    # a: 1x4, b: 4x4 -> 1x4
    res = [0, 0, 0, 0]
    for i in range(4):
        for j in range(4):
            res[i] += a[j] * b[j][i]
    return res

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)

def draw():
    py5.background(220, 90, 5) # Deep blue/black
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.015
    
    # 4D Rotation matrices
    # XY rotation
    r_xy = [
        [math.cos(t), -math.sin(t), 0, 0],
        [math.sin(t), math.cos(t), 0, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 1]
    ]
    
    # ZW rotation
    r_zw = [
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, math.cos(t * 1.5), -math.sin(t * 1.5)],
        [0, 0, math.sin(t * 1.5), math.cos(t * 1.5)]
    ]
    
    # XW rotation
    r_xw = [
        [math.cos(t * 0.5), 0, 0, -math.sin(t * 0.5)],
        [0, 1, 0, 0],
        [0, 0, 1, 0],
        [math.sin(t * 0.5), 0, 0, math.cos(t * 0.5)]
    ]
    
    projected_3d = []
    
    for v in vertices_4d:
        # Apply rotations
        rotated = matmul(v, r_xy)
        rotated = matmul(rotated, r_zw)
        rotated = matmul(rotated, r_xw)
        
        # Stereographic projection from 4D to 3D
        distance = 2.5
        w = 1.0 / (distance - rotated[3])
        
        x = rotated[0] * w
        y = rotated[1] * w
        z = rotated[2] * w
        
        # Scale for display
        scale = 600
        projected_3d.append((x * scale, y * scale, z * scale))
        
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(3)
    
    # Draw edges
    for e in edges:
        p1 = projected_3d[e[0]]
        p2 = projected_3d[e[1]]
        
        d = math.sqrt(p1[0]**2 + p1[1]**2 + p1[2]**2)
        hue = (180 + d * 0.2 + py5.frame_count) % 360
        
        py5.stroke(hue, 80, 100, 200)
        py5.line(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2])
        
    # Draw vertices as glowing nodes
    py5.no_stroke()
    for p in projected_3d:
        d = math.sqrt(p[0]**2 + p[1]**2 + p[2]**2)
        hue = (180 + d * 0.2 + py5.frame_count + 180) % 360
        py5.fill(hue, 90, 100, 180)
        py5.push_matrix()
        py5.translate(p[0], p[1], p[2])
        py5.sphere(12)
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)

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
