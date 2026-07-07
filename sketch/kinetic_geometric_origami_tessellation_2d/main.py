from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_SIZE = 80
triangles = []

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.RGB, 255)
    
    # Generate a triangular grid
    w = np.sqrt(3) * GRID_SIZE
    h = 1.5 * GRID_SIZE
    
    cols = int(SIZE[0] / w) + 4
    rows = int(SIZE[1] / h) + 4
    
    # Store base vertices
    # Each row has slightly offset columns
    vertices = {}
    for r in range(-2, rows):
        for c in range(-2, cols):
            x = c * w + (w/2 if r % 2 != 0 else 0)
            y = r * h
            vertices[(r, c)] = np.array([x, y, 0.0])
            
    # Form triangles
    for r in range(-1, rows - 1):
        for c in range(-1, cols - 1):
            # Up-pointing triangle
            # r, c ; r, c+1 ; r-1, c (if r is odd) or r-1, c+1
            v0 = (r, c)
            v1 = (r, c+1)
            v2 = (r+1, c) if r % 2 == 0 else (r+1, c+1)
            if v0 in vertices and v1 in vertices and v2 in vertices:
                triangles.append([v0, v1, v2])
                
            # Down-pointing triangle
            v3 = (r+1, c)
            v4 = (r+1, c+1)
            v5 = (r, c) if r % 2 == 0 else (r, c+1)
            if v3 in vertices and v4 in vertices and v5 in vertices:
                triangles.append([v3, v4, v5])
                
    global base_vertices
    base_vertices = vertices

def draw():
    py5.background(250, 250, 250)
    
    t = py5.frame_count * 0.02
    
    # Calculate Z for all vertices based on waves
    current_vertices = {}
    for key, v in base_vertices.items():
        x, y, _ = v
        
        # Complex folding waves
        wave1 = np.sin(x * 0.005 + t * 1.5) * np.cos(y * 0.005 - t * 1.2)
        wave2 = np.sin(y * 0.008 + t * 2.0)
        noise = py5.os_noise(x * 0.002, y * 0.002, t * 0.5) - 0.5
        
        z = (wave1 + wave2 * 0.5 + noise) * 150.0
        current_vertices[key] = np.array([x, y, z])
        
    light_dir = np.array([np.cos(t * 0.5), np.sin(t * 0.5), 1.5])
    light_dir /= np.linalg.norm(light_dir)
    
    py5.no_stroke()
    
    # Colors
    c_peach = np.array([255, 218, 185])
    c_mint = np.array([152, 255, 152])
    c_lavender = np.array([230, 230, 250])
    palettes = [c_peach, c_mint, c_lavender]
    
    py5.begin_shape(py5.TRIANGLES)
    for i, tri in enumerate(triangles):
        p0 = current_vertices[tri[0]]
        p1 = current_vertices[tri[1]]
        p2 = current_vertices[tri[2]]
        
        # Calculate normal
        A = p1 - p0
        B = p2 - p0
        norm = np.cross(A, B)
        norm_len = np.linalg.norm(norm)
        if norm_len != 0:
            norm /= norm_len
        else:
            norm = np.array([0, 0, 1])
            
        # Ensure normal faces the camera
        if norm[2] < 0:
            norm = -norm
            
        shade = np.dot(norm, light_dir)
        # Remap shade from [-1, 1] to [0.3, 1.0]
        shade = py5.remap(shade, -1, 1, 0.4, 1.0)
        shade = py5.constrain(shade, 0.1, 1.0)
        
        base_color = palettes[i % 3]
        final_color = base_color * shade
        
        py5.fill(final_color[0], final_color[1], final_color[2])
        
        # Small projection for 3D effect
        def proj(p):
            # Orthographic with slight perspective
            z = p[2]
            f = 2000 / (2000 - z) if (2000 - z) != 0 else 1
            # Center around origin for projection, then translate back
            cx = p[0] - SIZE[0]/2
            cy = p[1] - SIZE[1]/2
            return cx * f + SIZE[0]/2, cy * f + SIZE[1]/2
            
        v0 = proj(p0)
        v1 = proj(p1)
        v2 = proj(p2)
        
        py5.vertex(v0[0], v0[1])
        py5.vertex(v1[0], v1[1])
        py5.vertex(v2[0], v2[1])
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
