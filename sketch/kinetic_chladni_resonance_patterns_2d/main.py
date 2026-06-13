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
DURATION_SEC = 20
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

num_particles = 100000
positions = None
velocities = None

def setup():
    global positions, velocities
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    positions = np.random.rand(num_particles, 2) * np.array([py5.width, py5.height])
    velocities = np.zeros((num_particles, 2))
    py5.background(0)

def draw():
    global positions, velocities
    
    py5.fill(0, 0, 0, 20)
    py5.no_stroke()
    py5.rect(0, 0, py5.width, py5.height)
    
    t = py5.frame_count * 0.005
    m = 2 + py5.sin(t * 0.5) * 5
    n = 3 + py5.cos(t * 0.7) * 4
    
    norm_x = (positions[:, 0] / py5.width) * 2 - 1
    norm_y = (positions[:, 1] / py5.height) * 2 - 1
    
    epsilon = 0.01
    
    def chladni(x, y, m_val, n_val):
        return np.cos(n_val * py5.PI * x) * np.cos(m_val * py5.PI * y) - np.cos(m_val * py5.PI * x) * np.cos(n_val * py5.PI * y)
        
    val_center = np.abs(chladni(norm_x, norm_y, m, n))
    val_dx = np.abs(chladni(norm_x + epsilon, norm_y, m, n))
    val_dy = np.abs(chladni(norm_x, norm_y + epsilon, m, n))
    
    grad_x = (val_dx - val_center) / epsilon
    grad_y = (val_dy - val_center) / epsilon
    
    noise_x = np.random.randn(num_particles) * 0.002
    noise_y = np.random.randn(num_particles) * 0.002
    
    velocities[:, 0] = velocities[:, 0] * 0.9 - grad_x * 2.0 + noise_x * py5.width
    velocities[:, 1] = velocities[:, 1] * 0.9 - grad_y * 2.0 + noise_y * py5.height
    
    positions += velocities
    
    positions[:, 0] = np.mod(positions[:, 0], py5.width)
    positions[:, 1] = np.mod(positions[:, 1], py5.height)
    
    hue = (py5.frame_count * 0.5) % 360
    py5.stroke(hue, 80, 100, 50)
    py5.stroke_weight(2)
    py5.blend_mode(py5.ADD)
    
    py5.points(positions)
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
