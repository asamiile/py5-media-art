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

GRID_SIZE = 40
CELL_SIZE = 40

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
def draw():
    py5.background(15, 25, 10)
    
    # Setup Isometric camera
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 200, -500)
    py5.rotate_x(-py5.PI/6)
    py5.rotate_y(py5.PI/4 + py5.frame_count * 0.002) # Slow spin
    
    time_val = py5.frame_count * 0.03
    
    py5.ambient_light(0, 0, 30)
    py5.directional_light(200, 50, 100, 1, 1, -1)
    py5.directional_light(300, 50, 100, -1, 1, 1)
    
    # Offset so grid is centered
    offset_x = -GRID_SIZE * CELL_SIZE / 2
    offset_z = -GRID_SIZE * CELL_SIZE / 2
    
    py5.translate(offset_x, 0, offset_z)
    
    py5.no_stroke()
    
    for x in range(GRID_SIZE):
        for z in range(GRID_SIZE):
            n = py5.os_noise(x * 0.08, z * 0.08, time_val)
            
            # Base height
            h = 20 + n * 400
            
            # Pulse waves sweeping across
            dist_to_center = py5.dist(x, z, GRID_SIZE/2, GRID_SIZE/2)
            pulse = py5.sin(dist_to_center * 0.5 - time_val * 2)
            if pulse > 0.8:
                h += py5.remap(pulse, 0.8, 1.0, 0, 200)
                hue = (200 + time_val * 20 + dist_to_center * 10) % 360
                py5.fill(hue, 80, 100)
                py5.emissive(hue, 80, 100)
            else:
                py5.fill(220, 50, 30)
                py5.emissive(0, 0, 0)
                
            py5.push_matrix()
            py5.translate(x * CELL_SIZE, -h/2, z * CELL_SIZE)
            # Make gaps between boxes
            py5.box(CELL_SIZE * 0.8, h, CELL_SIZE * 0.8)
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
