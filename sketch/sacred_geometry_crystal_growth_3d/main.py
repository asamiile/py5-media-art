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

# Pre-calculate crystal vectors
NUM_CRYSTALS = 300
crystals = []
for i in range(NUM_CRYSTALS):
    # Random direction
    v = np.random.randn(3)
    v /= np.linalg.norm(v)
    
    # Growth offsets and speeds
    phase_offset = np.random.uniform(0, 2*np.pi)
    speed = np.random.uniform(0.5, 1.5)
    max_length = np.random.uniform(100, 400)
    thickness = np.random.uniform(20, 60)
    color_shift = np.random.uniform(0, 1)
    
    crystals.append({
        'dir': v,
        'phase': phase_offset,
        'speed': speed,
        'max_len': max_length,
        'thick': thickness,
        'c_shift': color_shift
    })

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw_octahedron(length, thickness):
    py5.begin_shape(py5.TRIANGLES)
    # Top point
    top = [0, 0, length/2]
    # Bottom point
    bottom = [0, 0, -length/2]
    # Middle vertices
    mid = [
        [thickness, 0, 0],
        [0, thickness, 0],
        [-thickness, 0, 0],
        [0, -thickness, 0]
    ]
    
    # Top pyramid
    for i in range(4):
        py5.vertex(*top)
        py5.vertex(*mid[i])
        py5.vertex(*mid[(i+1)%4])
        
    # Bottom pyramid
    for i in range(4):
        py5.vertex(*bottom)
        py5.vertex(*mid[(i+1)%4])
        py5.vertex(*mid[i])
        
    py5.end_shape()

def draw():
    py5.background(10, 0, 20) # Very dark purple
    
    # Additive blend mode for glowing crystals
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST) # Looks better with additive blending
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Global camera rotation
    py5.rotate_y(py5.frame_count * 0.003)
    py5.rotate_x(py5.frame_count * 0.002)
    py5.rotate_z(py5.frame_count * 0.001)
    
    t = py5.frame_count * 0.03
    
    # Core glow
    py5.push_matrix()
    core_pulse = 100 + 20 * np.sin(t * 2)
    py5.fill(255, 200, 255, 100)
    py5.sphere_detail(16)
    py5.sphere(core_pulse)
    py5.pop_matrix()
    
    # Draw crystals
    for c in crystals:
        py5.push_matrix()
        
        # Align with direction vector
        d = c['dir']
        # Compute angles to rotate z-axis to vector d
        theta = np.arccos(d[2])
        phi = np.arctan2(d[1], d[0])
        
        py5.rotate_z(phi)
        py5.rotate_y(theta)
        
        # Growth dynamics
        # Cyclic growth and shrinking
        growth = max(0, np.sin(t * c['speed'] + c['phase'])) ** 2
        
        # Move outward based on growth
        offset = 50 + growth * 100
        py5.translate(0, 0, offset)
        
        l = growth * c['max_len']
        th = c['thick'] * (0.2 + 0.8 * growth)
        
        if l > 5:
            # Determine color
            if c['c_shift'] < 0.6:
                py5.fill(138, 43, 226, 40) # Amethyst / Violet
            elif c['c_shift'] < 0.9:
                py5.fill(255, 182, 193, 40) # Rose Quartz / Pink
            else:
                py5.fill(255, 255, 255, 60) # Pure White energy
                
            draw_octahedron(l, th)
            
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
