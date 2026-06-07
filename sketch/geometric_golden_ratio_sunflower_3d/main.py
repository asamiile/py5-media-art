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

def draw():
    py5.background(15, 10, 15)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, -100)
    
    t = py5.frame_count * 0.02
    py5.rotate_x(py5.PI / 4)
    py5.rotate_z(t * 0.5)
    
    num_seeds = 1200
    c = 15 # Scaling factor
    phi = (1 + 5**0.5) / 2 # Golden ratio
    golden_angle = py5.TWO_PI * (2 - phi)
    
    py5.no_stroke()
    
    for i in range(1, num_seeds + 1):
        r = c * py5.sqrt(i)
        theta = i * golden_angle
        
        x = r * py5.cos(theta)
        y = r * py5.sin(theta)
        
        # Add a wave displacement using distance and time
        dist = py5.dist(0, 0, x, y)
        z = py5.sin(dist * 0.05 - t * 2) * 50 + py5.os_noise(x * 0.01, y * 0.01, t) * 100
        
        py5.push_matrix()
        py5.translate(x, y, z)
        
        # Color based on radius and angle
        hue = (dist * 0.5 - t * 20 + py5.degrees(theta) * 0.1) % 360
        py5.fill(hue, 90, 100, 90)
        
        # Seed size
        size = 2 + py5.sqrt(i) * 0.15
        py5.sphere(size)
        
        py5.pop_matrix()

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
