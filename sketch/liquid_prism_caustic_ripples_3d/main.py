from pathlib import Path
import shutil
import subprocess
import sys
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

# Parameters
GRID_SIZE = 200
SPACING = 15
WAVE_COUNT = 5
waves = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True, parents=True)
    
    # Initialize random wave parameters
    np.random.seed(42)  # Just for initializing consistent wave directions, phase will change
    for _ in range(WAVE_COUNT):
        angle = np.random.uniform(0, py5.TWO_PI)
        freq = np.random.uniform(0.01, 0.05)
        amp = np.random.uniform(20, 80)
        speed = np.random.uniform(0.02, 0.08)
        waves.append({
            'dx': np.cos(angle) * freq,
            'dy': np.sin(angle) * freq,
            'amp': amp,
            'speed': speed,
            'phase': np.random.uniform(0, py5.TWO_PI)
        })

def get_z(x, y, t):
    z = 0
    for w in waves:
        val = w['dx'] * x + w['dy'] * y + w['speed'] * t + w['phase']
        z += np.sin(val) * w['amp']
    return z

def get_normal(x, y, t):
    eps = 1.0
    z_center = get_z(x, y, t)
    z_dx = get_z(x + eps, y, t)
    z_dy = get_z(x, y + eps, t)
    
    nx = z_center - z_dx
    ny = z_center - z_dy
    nz = eps
    
    length = np.sqrt(nx*nx + ny*ny + nz*nz)
    return nx/length, ny/length, nz/length

def draw():
    py5.background(5, 5, 10) # Dark obsidian void
    
    py5.push_matrix()
    py5.translate(py5.width/2, py5.height/2 + 200, -500)
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(py5.frame_count * 0.002)
    
    py5.directional_light(0, 255, 255, 1, 1, -1) # Cyan
    py5.directional_light(255, 0, 255, -1, 1, -1) # Magenta
    py5.directional_light(255, 200, 0, 0, -1, -1) # Gold
    py5.ambient_light(20, 20, 30)
    
    t = py5.frame_count
    
    py5.no_stroke()
    
    offset = (GRID_SIZE * SPACING) / 2
    py5.translate(-offset, -offset, 0)
    
    for i in range(GRID_SIZE - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for j in range(GRID_SIZE):
            x = i * SPACING
            y = j * SPACING
            z1 = get_z(x, y, t)
            z2 = get_z(x + SPACING, y, t)
            
            # Simple caustic coloring based on normal z component
            nx1, ny1, nz1 = get_normal(x, y, t)
            nx2, ny2, nz2 = get_normal(x + SPACING, y, t)
            
            # Mix colors: 
            # High nz (flat) = base glass (cyan-ish)
            # Steep slope = more magenta/gold
            c1_r = int(py5.remap(abs(nx1), 0, 1, 0, 255))
            c1_g = int(py5.remap(abs(ny1), 0, 1, 100, 255))
            c1_b = int(py5.remap(nz1, 0, 1, 200, 255))
            py5.fill(c1_r, c1_g, c1_b, 220)
            py5.vertex(x, y, z1)
            
            c2_r = int(py5.remap(abs(nx2), 0, 1, 0, 255))
            c2_g = int(py5.remap(abs(ny2), 0, 1, 100, 255))
            c2_b = int(py5.remap(nz2, 0, 1, 200, 255))
            py5.fill(c2_r, c2_g, c2_b, 220)
            py5.vertex(x + SPACING, y, z2)
        py5.end_shape()
    
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
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
