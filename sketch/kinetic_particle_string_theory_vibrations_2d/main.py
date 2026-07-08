from pathlib import Path
import shutil
import subprocess
import sys
import random
import numpy as np
import py5
from scipy.spatial import cKDTree

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

NUM_POINTS = 300
CONNECTIONS_PER_POINT = 3
points = []
connections = []

def rotate_3d(v, rx, ry, rz):
    mx = np.array([
        [1, 0, 0],
        [0, np.cos(rx), -np.sin(rx)],
        [0, np.sin(rx), np.cos(rx)]
    ])
    my = np.array([
        [np.cos(ry), 0, np.sin(ry)],
        [0, 1, 0],
        [-np.sin(ry), 0, np.cos(ry)]
    ])
    mz = np.array([
        [np.cos(rz), -np.sin(rz), 0],
        [np.sin(rz), np.cos(rz), 0],
        [0, 0, 1]
    ])
    return mz @ (my @ (mx @ v))

def setup():
    global points, connections
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(0)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Generate points on a 3D torus
    R = 400
    r = 150
    for _ in range(NUM_POINTS):
        u = random.uniform(0, py5.TWO_PI)
        v = random.uniform(0, py5.TWO_PI)
        x = (R + r * np.cos(v)) * np.cos(u)
        y = (R + r * np.cos(v)) * np.sin(u)
        z = r * np.sin(v)
        points.append(np.array([x, y, z]))
        
    points = np.array(points)
    
    # Build connections using KDTree
    tree = cKDTree(points)
    for i, p in enumerate(points):
        # find nearest neighbors
        dists, indices = tree.query(p, k=CONNECTIONS_PER_POINT + 1)
        for idx in indices[1:]:
            # To avoid duplicate pairs, only add if i < idx
            if i < idx:
                # Add connection with a random harmonic (1 to 4) and phase
                harmonic = random.randint(1, 4)
                phase_offset = random.uniform(0, py5.TWO_PI)
                freq = random.uniform(2.0, 5.0)
                connections.append((i, idx, harmonic, phase_offset, freq))

def draw():
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 40) # Fading trails
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    rx = t * 0.3
    ry = t * 0.5
    rz = t * 0.2
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2)
    
    # Project all points
    proj_pts = []
    for p in points:
        rp = rotate_3d(p, rx, ry, rz)
        # Perspective
        z = rp[2]
        f = 1200 / (1200 - z) if (1200 - z) != 0 else 1
        px = rp[0] * f
        py_coord = rp[1] * f
        proj_pts.append(np.array([px, py_coord, z]))
        
    # Draw connections
    py5.no_fill()
    py5.stroke_weight(1.5)
    
    for i, j, harmonic, phase_offset, freq in connections:
        p1 = proj_pts[i]
        p2 = proj_pts[j]
        
        # Calculate color based on depth
        z_avg = (p1[2] + p2[2]) / 2.0
        # Depth mapping: Back is dim violet, front is bright electric blue/cyan
        depth_factor = py5.constrain(py5.remap(z_avg, -500, 500, 0, 1), 0, 1)
        
        r_col = py5.lerp(30, 0, depth_factor)
        g_col = py5.lerp(0, 200, depth_factor)
        b_col = py5.lerp(150, 255, depth_factor)
        alpha = py5.lerp(50, 200, depth_factor)
        
        py5.stroke(r_col, g_col, b_col, alpha)
        
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        dist = np.sqrt(dx*dx + dy*dy)
        
        if dist < 1:
            continue
            
        # Normal vector for vibration offset
        nx = -dy / dist
        ny = dx / dist
        
        # Vibration amplitude
        amp = 15.0 * np.sin(t * freq + phase_offset)
        
        segments = int(dist / 10) + 5
        py5.begin_shape()
        for s in range(segments + 1):
            frac = s / segments
            # Base position
            bx = p1[0] + dx * frac
            by = p1[1] + dy * frac
            
            # Standing wave envelope (zero at ends)
            envelope = np.sin(frac * py5.PI)
            # Harmonic wave
            wave = np.sin(frac * py5.PI * harmonic)
            
            # Final offset
            offset = envelope * wave * amp
            
            py5.vertex(bx + nx * offset, by + ny * offset)
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
