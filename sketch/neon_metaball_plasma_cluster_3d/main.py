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

N_SPHERES = 80
positions = np.zeros((N_SPHERES, 3), dtype=np.float32)
velocities = np.zeros((N_SPHERES, 3), dtype=np.float32)
colors = np.zeros((N_SPHERES,), dtype=np.float32)
radii = np.zeros((N_SPHERES,), dtype=np.float32)

def setup():
    global positions, velocities, colors, radii
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_stroke()
    py5.sphere_detail(20)
    
    scale_factor = SIZE[1] / 1080.0
    
    for i in range(N_SPHERES):
        positions[i] = np.random.uniform(-300 * scale_factor, 300 * scale_factor, 3)
        velocities[i] = np.random.uniform(-2, 2, 3)
        colors[i] = np.random.uniform(260, 320)  # Violet to Magenta
        radii[i] = np.random.uniform(40, 120) * scale_factor

def draw():
    global positions, velocities
    
    py5.background(0)
    
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -400)
    
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.rotate_x(t * py5.TWO_PI)
    py5.rotate_y(t * py5.TWO_PI * 0.5)
    
    scale_factor = SIZE[1] / 1080.0
    center_attraction = 0.05
    noise_scale = 0.005
    
    for i in range(N_SPHERES):
        p = positions[i]
        
        dir_to_center = -p
        dist = np.linalg.norm(dir_to_center) + 1e-5
        force = (dir_to_center / dist) * center_attraction * dist * 0.02
        
        nx = py5.os_noise(p[0]*noise_scale, p[1]*noise_scale, t*10) - 0.5
        ny = py5.os_noise(p[1]*noise_scale, p[2]*noise_scale, t*10 + 100) - 0.5
        nz = py5.os_noise(p[2]*noise_scale, p[0]*noise_scale, t*10 + 200) - 0.5
        
        velocities[i] += force + np.array([nx, ny, nz]) * 5.0 * scale_factor
        velocities[i] *= 0.95
        
        positions[i] += velocities[i]
        
        py5.push_matrix()
        py5.translate(positions[i][0], positions[i][1], positions[i][2])
        
        r = radii[i] * (1.0 + 0.3 * py5.sin(t * py5.TWO_PI * 2 + i))
        
        py5.fill(colors[i], 90, 40, 15)
        
        for shell in range(3, 0, -1):
            py5.push_matrix()
            py5.scale(shell * 0.5)
            py5.sphere(r)
            py5.pop_matrix()
            
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
