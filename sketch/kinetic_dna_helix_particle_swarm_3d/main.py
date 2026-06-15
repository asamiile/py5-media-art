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

# Precompute particle parameters
num_particles = 15000
# Base parameters along the helix
t_vals = np.random.uniform(-py5.PI * 4, py5.PI * 4, num_particles)
strand = np.random.choice([0, 1], num_particles)
radius = 200

base_x = np.cos(t_vals + strand * py5.PI) * radius
base_y = t_vals * 150  # Height of the helix
base_z = np.sin(t_vals + strand * py5.PI) * radius

particle_sizes = np.random.uniform(2, 6, num_particles)
particle_hues = np.where(strand == 0, 280, 90) # Electric violet and Acid green

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.rotate_y(t * py5.TWO_PI)
    py5.rotate_x(py5.sin(t * py5.TWO_PI) * 0.2)
    
    # Calculate noise displacement for all particles
    for i in range(num_particles):
        px = base_x[i]
        py_coord = base_y[i]
        pz = base_z[i]
        
        # 4D noise
        noise_val = py5.os_noise(px * 0.005, py_coord * 0.005, pz * 0.005, t * 2.0)
        
        # Swirl factor based on time and height
        swirl = py5.sin(py_coord * 0.01 + t * py5.TWO_PI * 2.0)
        
        # Displace particles
        disp_x = px + (noise_val * 200 * swirl)
        disp_y = py_coord + (noise_val * 100)
        disp_z = pz + (noise_val * 200 * swirl)
        
        # Pulse intensity
        pulse = py5.sin(t * py5.TWO_PI * 4.0 + i * 0.01) * 0.5 + 0.5
        
        py5.stroke(particle_hues[i], 90, 100, 30 + pulse * 70)
        py5.stroke_weight(particle_sizes[i])
        py5.point(disp_x, disp_y, disp_z)

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
