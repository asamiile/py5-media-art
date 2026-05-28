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
DURATION_SEC = 15  # 15s animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_particles = 40000
radii = None
angles = None
speeds = None
z_offsets = None

def setup():
    global radii, angles, speeds, z_offsets
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.background(0)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.blend_mode(py5.ADD)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Event horizon is roughly radius 200
    radii = np.random.uniform(250, 1500, num_particles)
    # Density bias towards center
    radii = 250 + (radii - 250) ** 1.5 / (1250**0.5)
    
    angles = np.random.uniform(0, py5.PI * 2, num_particles)
    
    # Keplerian speed: v ~ 1 / sqrt(r)
    speeds = 200.0 / np.sqrt(radii)
    
    # Small vertical variation
    z_offsets = np.random.normal(0, 10, num_particles)

def draw():
    global radii, angles
    
    py5.blend_mode(py5.BLEND)
    py5.background(0, 0, 0, 20)
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.05
    
    py5.translate(py5.width / 2, py5.height / 2, -500)
    
    # Camera angle to see the disk
    py5.rotate_x(py5.PI / 2.5)
    
    # Update angles
    angles += speeds * 0.02
    
    # Draw particles
    x = np.cos(angles) * radii
    y = np.sin(angles) * radii
    
    # Gravitational lensing warp (fake relativistic effect)
    # Bend the disk severely upwards/downwards near the center
    warp = 80000 / (radii - 150)
    # Split warp based on Y position (front/back of disk)
    front_back = np.sign(y)
    z = z_offsets + warp * front_back
    
    # Draw as points
    py5.stroke_weight(2)
    py5.begin_shape(py5.POINTS)
    for i in range(num_particles):
        r = radii[i]
        
        # Color based on radius (inner is white-hot, outer is dark red)
        hue = py5.remap(r, 250, 1500, 50, 0)
        hue = max(0, min(50, hue))
        
        sat = py5.remap(r, 250, 800, 10, 100)
        sat = max(10, min(100, sat))
        
        bri = py5.remap(r, 250, 1200, 100, 30)
        bri = max(30, min(100, bri))
        
        py5.stroke(hue, sat, bri, 60)
        py5.vertex(x[i], y[i], z[i])
    py5.end_shape()

    # Draw event horizon (black hole shadow)
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0)
    py5.push_matrix()
    py5.rotate_x(-py5.PI / 2.5) # Face camera
    py5.circle(0, 0, 480)
    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    # Fail-safe: abort if nothing is drawn
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
