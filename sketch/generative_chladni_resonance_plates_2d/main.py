from pathlib import Path
import shutil
import subprocess
import sys
import random
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
DURATION_SEC = random.randint(15, 30)
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

NUM_PTS = 150000
pts = None

def setup():
    global pts
    py5.size(*SIZE)
    py5.pixel_density(1)
    py5.background(10, 5, 5)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize points randomly across the screen
    x = np.random.uniform(0, SIZE[0], NUM_PTS)
    y = np.random.uniform(0, SIZE[1], NUM_PTS)
    pts = np.column_stack((x, y))

def draw():
    # Subtle fade to leave slight trails and simulate motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(15, 10, 10, 40)
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    t = py5.frame_count * 0.005
    
    # Morphing parameters for Chladni plate
    # n and m are the resonance modes. We morph them slowly.
    # Typical modes are integers, but continuous values create chaotic morphing.
    n = 3.0 + 2.0 * np.sin(t * 0.7)
    m = 5.0 + 3.0 * np.cos(t * 0.5)
    
    a = 1.0
    b = 1.0 # can also be -1 for different patterns
    
    # Map positions to [-1, 1]
    nx = (pts[:, 0] - SIZE[0]/2) / (SIZE[0]/2)
    ny = (pts[:, 1] - SIZE[1]/2) / (SIZE[1]/2)
    
    # Chladni equation
    # C(x, y) = a * sin(pi * n * x) * sin(pi * m * y) + b * sin(pi * m * x) * sin(pi * n * y)
    term1 = a * np.sin(np.pi * n * nx) * np.sin(np.pi * m * ny)
    term2 = b * np.sin(np.pi * m * nx) * np.sin(np.pi * n * ny)
    
    C = term1 + term2
    amp = np.abs(C)
    
    # The bounce magnitude depends on the amplitude of vibration
    # Also add a tiny base noise so they don't get completely stuck forever
    bounce = amp * 25.0 + 0.1
    
    # Update positions with random walk proportional to bounce
    # We use a mix of pure random and a slight drift towards the center to avoid losing particles
    noise_x = np.random.randn(NUM_PTS) * bounce
    noise_y = np.random.randn(NUM_PTS) * bounce
    
    pts[:, 0] += noise_x
    pts[:, 1] += noise_y
    
    # Keep particles inside bounds (wrap around or clamp)
    # Wrapping around creates a cool continuous flow
    pts[:, 0] = pts[:, 0] % SIZE[0]
    pts[:, 1] = pts[:, 1] % SIZE[1]
    
    # Draw particles
    py5.blend_mode(py5.ADD)
    py5.stroke(255, 220, 150, 150) # Golden sand color
    py5.stroke_weight(1.5)
    
    # Use py5.points for extremely fast rendering of thousands of points
    py5.points(pts)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
            import sys
            sys.stdout.flush()
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
