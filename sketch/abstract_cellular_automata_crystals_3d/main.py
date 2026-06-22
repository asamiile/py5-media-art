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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

GRID_SIZE = 15
CELL_SIZE = SIZE[1] * 0.04
THRESHOLD = 0.6 # Only draw cells where noise > threshold

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(15, 10, 15) # Very dark purple
    
    # Lighting for crystals
    py5.ambient_light(50, 50, 50)
    py5.directional_light(200, 20, 100, 0.5, 0.5, -1)
    py5.directional_light(300, 50, 80, -0.5, -0.5, 1)
    
    # Camera setup
    py5.translate(SIZE[0]/2, SIZE[1]/2, -SIZE[1]*0.5)
    
    # Slow dynamic rotation
    py5.rotate_x(py5.frame_count * 0.003)
    py5.rotate_y(py5.frame_count * 0.005)
    py5.rotate_z(py5.frame_count * 0.002)
    
    time_val = py5.frame_count * 0.01
    
    # Center the grid
    py5.translate(-GRID_SIZE * CELL_SIZE / 2, -GRID_SIZE * CELL_SIZE / 2, -GRID_SIZE * CELL_SIZE / 2)
    
    py5.no_stroke()
    
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            for z in range(GRID_SIZE):
                # 4D noise (3D pos + time)
                n = py5.os_noise(x * 0.15, y * 0.15, z * 0.15 + time_val)
                
                # Normalize noise from [-1, 1] to [0, 1]
                n_norm = (n + 1) / 2.0
                
                if n_norm > THRESHOLD:
                    # Scale based on how far past the threshold it is
                    scale_val = py5.remap(n_norm, THRESHOLD, 1.0, 0.1, 1.0)
                    
                    # Color based on position and noise
                    hue = (x * 10 + y * 5 + z * 8 + time_val * 50) % 360
                    
                    py5.push_matrix()
                    py5.translate(x * CELL_SIZE, y * CELL_SIZE, z * CELL_SIZE)
                    
                    # Material properties
                    py5.fill(hue, 80, 100, 200) # Semi-transparent
                    py5.specular(100, 0, 100)
                    py5.shininess(10.0)
                    
                    # Individual cell rotation for chaotic crystal look
                    py5.rotate_x(n * py5.TWO_PI)
                    py5.rotate_y(n * py5.TWO_PI)
                    
                    py5.box(CELL_SIZE * scale_val)
                    py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count}. Aborting.")
            import os
            os._exit(1)

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")

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
            print("[Render Cleanup] Temporary frames directory removed.")
        import os
        os._exit(0)

py5.run_sketch()
