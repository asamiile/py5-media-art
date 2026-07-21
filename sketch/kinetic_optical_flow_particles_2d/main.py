from pathlib import Path
import shutil
import subprocess
import sys
import random
import py5
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = random.randint(15, 20)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Particle settings
NUM_PARTICLES = 150000
NOISE_SCALE = 0.003
Z_OFF_SPEED = 0.002
FLOW_MAGNITUDE = 5.0

particles_x = np.random.uniform(0, SIZE[0], NUM_PARTICLES)
particles_y = np.random.uniform(0, SIZE[1], NUM_PARTICLES)
particles_hues = np.random.choice([320, 180, 50], NUM_PARTICLES).astype(np.float32)

z_off = 0.0

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.background(0)

def draw():
    global particles_x, particles_y, z_off
    
    # Fade background slightly for trails
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 0, 0, 15)
    py5.rect(0, 0, py5.width, py5.height)
    
    # os_noise returns values between -1 and 1
    noise_vals = py5.os_noise(
        particles_x * NOISE_SCALE,
        particles_y * NOISE_SCALE,
        np.full(NUM_PARTICLES, z_off)
    )
    
    # Map noise to angles (0 to 4 PI for lots of swirling)
    angles = noise_vals * py5.TWO_PI * 2.0
    
    # Move particles
    particles_x += np.cos(angles) * FLOW_MAGNITUDE
    particles_y += np.sin(angles) * FLOW_MAGNITUDE
    
    # Wrap around edges
    particles_x = particles_x % py5.width
    particles_y = particles_y % py5.height
    
    # Draw particles grouped by color for speed
    py5.blend_mode(py5.ADD)
    py5.stroke_weight(2)
    
    mask1 = particles_hues == 320
    py5.stroke(320, 90, 100, 40)
    py5.points(np.column_stack((particles_x[mask1], particles_y[mask1])))
    
    mask2 = particles_hues == 180
    py5.stroke(180, 90, 100, 40)
    py5.points(np.column_stack((particles_x[mask2], particles_y[mask2])))
    
    mask3 = particles_hues == 50
    py5.stroke(50, 90, 100, 40)
    py5.points(np.column_stack((particles_x[mask3], particles_y[mask3])))
    
    z_off += Z_OFF_SPEED

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
        import os
        os._exit(0)

py5.run_sketch()
