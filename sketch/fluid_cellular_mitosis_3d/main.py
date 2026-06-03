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
    py5.color_mode(py5.HSB, 360, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(280, 80, 10)  # Very dark purple/black
    
    t = py5.frame_count / TOTAL_FRAMES
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    py5.rotate_x(t * py5.TWO_PI)
    py5.rotate_y(py5.sin(t * py5.TWO_PI) * py5.PI / 4)
    
    # Distance the two cells pull apart
    split_dist = py5.sin(t * py5.PI) * 200
    
    py5.no_stroke()
    py5.fill(120, 90, 80)
    
    # Render isosurface approximation with points
    # We'll use a spiral sphere distribution
    num_points = 80000
    phi = 1.618033988749895
    
    py5.begin_shape(py5.POINTS)
    for i in range(num_points):
        # Fibonacci sphere points
        y = 1 - (i / float(num_points - 1)) * 2
        radius = py5.sqrt(1 - y * y)
        theta = py5.TWO_PI * i / phi
        
        x = py5.cos(theta) * radius
        z = py5.sin(theta) * radius
        
        # Scale to base size
        base_r = 300
        px, py_pos, pz = x * base_r, y * base_r, z * base_r
        
        # Calculate distance to two moving centers (Mitosis)
        d1 = py5.dist(px, py_pos, pz, -split_dist, 0, 0)
        d2 = py5.dist(px, py_pos, pz, split_dist, 0, 0)
        
        # Metaball scalar field
        # Density = r1^2 / d1^2 + r2^2 / d2^2
        r_field = 250
        density = (r_field**2 / (d1**2 + 1)) + (r_field**2 / (d2**2 + 1))
        
        # We only draw points near the surface (density ~= 1)
        # We map this by projecting the point outward/inward based on density
        
        # 3D Noise for organic membrane
        n = py5.os_noise(px * 0.005, py_pos * 0.005, pz * 0.005 + t * 5)
        
        # Modify position based on metaball density and noise
        pull = density * 0.5 + n * 0.5
        
        fx = px * pull
        fy = py_pos * pull
        fz = pz * pull
        
        # Color based on noise and split distance
        hue = (120 + n * 60 + density * 30 + t * 60) % 360
        brightness = 100 if density > 0.8 and density < 1.2 else 40
        
        py5.stroke(hue, 90, brightness)
        py5.vertex(fx, fy, fz)
        
    py5.end_shape()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

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
        import os
        os._exit(0)

py5.run_sketch()
