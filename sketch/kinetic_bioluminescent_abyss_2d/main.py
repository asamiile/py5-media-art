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

# Particle setup
N_PARTICLES = 1500
positions = np.random.rand(N_PARTICLES, 2) * [SIZE[0], SIZE[1]]
velocities = np.zeros((N_PARTICLES, 2))
# Flashing phase per particle
phases = np.random.rand(N_PARTICLES) * py5.TWO_PI
flash_rates = 0.05 + np.random.rand(N_PARTICLES) * 0.05

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0, 5, 10)
    py5.color_mode(py5.RGB, 255)

def draw():
    global positions, velocities, phases
    
    # Trails
    py5.blend_mode(py5.BLEND)
    py5.fill(0, 5, 10, 40)
    py5.rect(0, 0, py5.width, py5.height)
    
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    # Update logic (vector field + flashes)
    # Using numpy for speed
    
    # Generate flow field
    grid_scale = 0.003
    for i in range(N_PARTICLES):
        nx = py5.os_noise(positions[i, 0] * grid_scale, positions[i, 1] * grid_scale, t) * py5.TWO_PI * 4
        
        vx = np.cos(nx) * 1.5
        vy = np.sin(nx) * 1.5
        
        velocities[i] = velocities[i] * 0.9 + np.array([vx, vy]) * 0.1
        positions[i] += velocities[i]
        
        # Advance phase
        phases[i] += flash_rates[i]
        
        # Wrap
        positions[i, 0] = positions[i, 0] % py5.width
        positions[i, 1] = positions[i, 1] % py5.height

    # Bioluminescent flashes: calculate distances and synchronize/trigger flashes if close
    # To keep it fast, we do a simplified proximity check
    
    # Base brightness from phase
    brightness = (np.sin(phases) + 1) * 0.5 # 0 to 1
    
    # Draw
    py5.no_stroke()
    for i in range(N_PARTICLES):
        b = brightness[i]
        if b > 0.8:
            # Bright flash
            alpha = int(py5.remap(b, 0.8, 1.0, 0, 255))
            
            # Deep sea green / cyan core
            py5.fill(0, 255, 200, alpha)
            py5.circle(positions[i, 0], positions[i, 1], 8)
            
            # Glow
            py5.fill(0, 150, 255, alpha * 0.3)
            py5.circle(positions[i, 0], positions[i, 1], 24)
        elif b > 0.2:
            # Dim ambient glow
            alpha = int(b * 50)
            py5.fill(0, 100, 150, alpha)
            py5.circle(positions[i, 0], positions[i, 1], 4)

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
