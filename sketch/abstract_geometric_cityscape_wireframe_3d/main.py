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

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_fill()
    py5.stroke_weight(2)

def draw():
    py5.background(0, 0, 5) # Dark space
    py5.blend_mode(py5.ADD)
    
    # Flight variables
    flight_speed = 5
    offset_z = py5.frame_count * flight_speed
    
    # Setup camera for isometric/perspective flyover
    cam_x = SIZE[0] / 2
    cam_y = SIZE[1] * 0.3 + py5.sin(py5.frame_count * 0.01) * 100
    cam_z = SIZE[1] * 0.5
    
    py5.camera(cam_x, cam_y, cam_z, 
               SIZE[0] / 2, SIZE[1], -SIZE[1], 
               0, 1, 0)
    
    grid_size = 60
    cols = int(SIZE[0] / grid_size) + 10
    rows = int(SIZE[1] * 2 / grid_size) + 10
    
    start_x = -grid_size * 5
    start_z = SIZE[1]
    
    py5.translate(start_x, SIZE[1] * 0.8, start_z)
    
    for z in range(rows):
        for x in range(cols):
            # Calculate noise for height
            noise_val = py5.os_noise(x * 0.1, (z * grid_size - offset_z) * 0.005, py5.frame_count * 0.005)
            
            # Form "districts" with taller buildings
            district_noise = py5.os_noise(x * 0.05, (z * grid_size - offset_z) * 0.002)
            
            h = py5.remap(noise_val, 0, 1, 20, 300)
            if district_noise > 0.6:
                h *= 3
            
            # Pulse the very tall buildings
            if h > 400:
                pulse = (py5.sin(py5.frame_count * 0.1 + x + z) + 1) * 0.5
                h += pulse * 100
                py5.stroke((180 + h * 0.2 + py5.frame_count * 2) % 360, 80, 100, 80 + pulse * 20)
            else:
                py5.stroke((220 + x * 2 + z * 2) % 360, 60, 100, 50)
                
            py5.push_matrix()
            py5.translate(x * grid_size, -h/2, -z * grid_size)
            # Add a slight rotation to some buildings for variety
            if district_noise > 0.7:
                py5.rotate_y(py5.frame_count * 0.02)
            py5.box(grid_size * 0.8, h, grid_size * 0.8)
            py5.pop_matrix()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))


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
