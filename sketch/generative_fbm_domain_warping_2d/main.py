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

# Particle system configuration
NUM_PARTICLES = 15000
px = np.zeros(NUM_PARTICLES, dtype=np.float32)
py = np.zeros(NUM_PARTICLES, dtype=np.float32)
color_seeds = np.zeros(NUM_PARTICLES, dtype=np.float32)

def fbm(x, y, time):
    # simple 3-octave fbm using py5.os_noise
    v = 0.0
    amp = 0.5
    freq = 1.0
    for _ in range(3):
        v += py5.os_noise(x * freq, y * freq, time) * amp
        freq *= 2.0
        amp *= 0.5
    return v

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    # Initialize particles
    for i in range(NUM_PARTICLES):
        px[i] = py5.random(py5.width)
        py[i] = py5.random(py5.height)
        color_seeds[i] = py5.random(1.0)

def draw():
    # Subtle fade using normal blend mode
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 10)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2.0)
    
    time = py5.frame_count * 0.005
    
    for i in range(NUM_PARTICLES):
        x = px[i]
        y = py[i]
        
        # Domain warping vector field
        nx = x * 0.001
        ny = y * 0.001
        
        # q = fbm(p)
        qx = fbm(nx, ny, time)
        qy = fbm(nx + 5.2, ny + 1.3, time)
        
        # r = fbm(p + q)
        rx = fbm(nx + 4.0 * qx, ny + 4.0 * qy, time + 0.5)
        ry = fbm(nx + 8.3 * qx, ny + 2.8 * qy, time - 0.5)
        
        # angle derived from r
        angle = rx * py5.TWO_PI * 2.0
        
        # move particle
        speed = 4.0
        nx_pos = x + py5.cos(angle) * speed
        ny_pos = y + py5.sin(angle) * speed
        
        # Determine color from warping and seed
        hue = py5.remap(ry, -1, 1, 150, 350)
        hue = (hue + color_seeds[i] * 50) % 360
        
        py5.stroke(hue, 90, 80, 40)
        py5.line(x, y, nx_pos, ny_pos)
        
        # update position and wrap
        if nx_pos < 0 or nx_pos > py5.width or ny_pos < 0 or ny_pos > py5.height:
            px[i] = py5.random(py5.width)
            py[i] = py5.random(py5.height)
        else:
            px[i] = nx_pos
            py[i] = ny_pos

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
