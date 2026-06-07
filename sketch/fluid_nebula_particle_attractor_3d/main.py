from pathlib import Path
import shutil
import subprocess
import sys
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
DURATION_SEC = 10
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.hint(py5.DISABLE_DEPTH_TEST)

def draw():
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.02
    py5.rotate_y(t)
    py5.rotate_x(py5.sin(t * 0.5) * 0.5)
    
    # 3D Spiral Attractor
    num_particles = 15000
    
    py5.stroke_weight(2)
    
    py5.begin_shape(py5.POINTS)
    for i in range(num_particles):
        idx = i / num_particles
        
        # Base spherical coordinates
        phi = py5.acos(1 - 2 * idx)
        theta = py5.PI * (1 + 5**0.5) * i
        
        radius = 400
        
        # Add a swirling vortex effect using noise and time
        noise_val = py5.os_noise(idx * 10, t * 0.5)
        swirl_angle = theta + t * 5 * (1 - idx) + noise_val * py5.TWO_PI
        
        r = radius * py5.sin(phi) + py5.sin(swirl_angle * 5) * 50
        
        x = r * py5.cos(swirl_angle)
        y = radius * py5.cos(phi)
        z = r * py5.sin(swirl_angle)
        
        # Distort coordinates
        nx = py5.os_noise(x * 0.005, y * 0.005, z * 0.005, t) - 0.5
        ny = py5.os_noise(x * 0.005 + 100, y * 0.005, z * 0.005, t) - 0.5
        nz = py5.os_noise(x * 0.005 + 200, y * 0.005, z * 0.005, t) - 0.5
        
        x += nx * 200
        y += ny * 200
        z += nz * 200
        
        # Color gradient based on y-position and noise
        hue = (180 + (y / radius) * 60 + noise_val * 60 + t * 20) % 360
        py5.stroke(hue, 90, 100, 60)
        
        py5.vertex(x, y, z)
        
    py5.end_shape()

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2. Aborting.")
            import os
            os._exit(1)

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
