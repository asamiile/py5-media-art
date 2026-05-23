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
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

NUM_SEEDS = 4000
C_FACTOR = 8.0 # Scaling factor

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(15)
    py5.blend_mode(py5.ADD)
    
    t = py5.frame_count * 0.01
    
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    # Rotate the entire spiral over time
    py5.rotate_z(t * 0.5)
    # Tilt slightly to give 3D depth
    py5.rotate_x(py5.sin(t * 0.3) * 0.4)
    py5.rotate_y(py5.cos(t * 0.4) * 0.3)
    
    # The Golden Angle is ~137.5 degrees (in radians: 2.39996)
    # We animate the angle VERY slightly around the golden angle.
    # Small deviations create massive changes in the visible spiral arms (Moiré patterns).
    golden_angle = 137.5
    divergence_angle = golden_angle + py5.sin(t * 0.5) * 0.1
    angle_rad = py5.radians(divergence_angle)
    
    py5.no_stroke()
    
    for n in range(1, NUM_SEEDS + 1):
        # Vogel's model for phyllotaxis
        r = C_FACTOR * py5.sqrt(n)
        theta = n * angle_rad
        
        x = r * py5.cos(theta)
        y = r * py5.sin(theta)
        
        # Add a 3D dome effect (z depends on radius)
        z = py5.remap(r, 0, C_FACTOR * py5.sqrt(NUM_SEEDS), 300, -300)
        
        # Color depends on angle and distance from center
        hue = (n * 0.5 - t * 50) % 360
        saturation = py5.remap(n, 0, NUM_SEEDS, 40, 100)
        brightness = py5.remap(n, 0, NUM_SEEDS, 100, 40)
        
        # Size of the "seed" grows slightly as it gets further out
        size = py5.remap(n, 0, NUM_SEEDS, 3, 12)
        
        py5.push_matrix()
        py5.translate(x, y, z)
        
        # Rotate the individual seed to face outwards
        py5.rotate_z(theta)
        
        py5.fill(hue, saturation, brightness, 90)
        
        # Draw a petal/seed shape (elongated ellipse)
        py5.ellipse(0, 0, size * 2.5, size)
        
        # Add a glowing center
        py5.fill(hue, 30, 100, 100)
        py5.circle(size * 0.5, 0, size * 0.5)
        
        py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
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
