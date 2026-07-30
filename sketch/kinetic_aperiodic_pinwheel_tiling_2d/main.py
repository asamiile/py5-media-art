from pathlib import Path
import math
import shutil
import subprocess
import sys
import numpy as np
import py5

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
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

# Pinwheel decomposition depth
DEPTH = 5


def subdivide_pinwheel(A, s, l, depth, triangles):
    """
    Exact Radin Pinwheel 5-fold decomposition of 1:2 right triangle (A, B, C)
    A: acute vertex (0,0)
    s: vector along short leg (length S)
    l: vector along long leg (length 2S, perpendicular to s)
    """
    if depth == 0:
        triangles.append((A, s, l))
        return

    # Normalized long-leg unit basis: v = l / 2.0 (same length as s)
    v = l * 0.5

    # 1. Sub-triangle 1
    subdivide_pinwheel(A, 0.4 * s + 0.2 * v, -0.2 * s + 0.4 * l, depth - 1, triangles)

    # 2. Sub-triangle 2
    subdivide_pinwheel(A + 0.8 * s + 0.4 * v, -0.4 * s - 0.2 * v, -0.2 * s + 0.4 * l, depth - 1, triangles)

    # 3. Sub-triangle 3
    subdivide_pinwheel(A + s, -0.2 * s + 0.4 * v, -0.8 * s - 0.4 * l, depth - 1, triangles)

    # 4. Sub-triangle 4
    subdivide_pinwheel(A + s, 0.8 * v, -0.4 * s, depth - 1, triangles)

    # 5. Sub-triangle 5
    subdivide_pinwheel(A + s + l, -0.4 * s - 0.2 * v, -0.4 * s + 0.8 * l, depth - 1, triangles)


def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)


def draw():
    py5.background(3, 7, 18)  # Obsidian void (#030712)
    
    w, h = float(SIZE[0]), float(SIZE[1])
    cx, cy = w / 2.0, h / 2.0
    
    # 2 exact 1:2 right triangles (short leg 2160, long leg 4320) tiling the full canvas gaplessly
    root_triangles = []
    
    # Root 1 (top triangle)
    A1 = np.array([-240.0, 0.0])
    s1 = np.array([0.0, h])        # short leg = (0, 2160)
    l1 = np.array([2.0 * h, 0.0])   # long leg = (4320, 0)
    root_triangles.append((A1, s1, l1))
    
    # Root 2 (bottom triangle)
    A2 = np.array([w + 240.0, h])
    s2 = np.array([0.0, -h])       # short leg = (0, -2160)
    l2 = np.array([-2.0 * h, 0.0])  # long leg = (-4320, 0)
    root_triangles.append((A2, s2, l2))
    
    all_tiles = []
    for rA, rs, rl in root_triangles:
        subdivide_pinwheel(rA, rs, rl, DEPTH, all_tiles)
        
    t = py5.frame_count / 60.0
    
    py5.stroke_weight(1.5)
    
    for idx, (A, s, l) in enumerate(all_tiles):
        B = A + s
        C = A + s + l
        
        # Center of triangle
        tx = (A[0] + B[0] + C[0]) / 3.0
        ty = (A[1] + B[1] + C[1]) / 3.0
        
        dx = tx - cx
        dy = ty - cy
        dist = math.sqrt(dx * dx + dy * dy)
        angle = math.atan2(dy, dx)
        
        # Phase wave animation
        phase = dist * 0.0018 - t * 2.0 + angle * 2.0
        wave = (math.sin(phase) + 1.0) * 0.5
        wave2 = (math.cos(dist * 0.0025 - t * 1.4) + 1.0) * 0.5
        
        # Radiant Palette Mapping:
        # Neon Cyan (#06b6d4) -> Electric Magenta (#ec4899) -> Solar Gold (#facc15) -> Deep Indigo (#4f46e5)
        r = 6.0 * (1 - wave) + 236.0 * wave * (1 - wave2) + 250.0 * wave2 + 79.0 * (1 - wave) * wave2
        g = 182.0 * (1 - wave) + 72.0 * wave * (1 - wave2) + 204.0 * wave2 + 70.0 * (1 - wave) * wave2
        b = 212.0 * (1 - wave) + 153.0 * wave * (1 - wave2) + 21.0 * wave2 + 229.0 * (1 - wave) * wave2
        
        r_col = int(np.clip(r, 0, 255))
        g_col = int(np.clip(g, 0, 255))
        b_col = int(np.clip(b, 0, 255))
        
        py5.fill(r_col, g_col, b_col, 220)
        py5.stroke(255, 255, 255, 100)
        py5.stroke_weight(1.0)
        
        py5.begin_shape()
        py5.vertex(A[0], A[1])
        py5.vertex(B[0], B[1])
        py5.vertex(C[0], C[1])
        py5.end_shape(py5.CLOSE)
        
    py5.blend_mode(py5.BLEND)
    
    # Save frame
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
