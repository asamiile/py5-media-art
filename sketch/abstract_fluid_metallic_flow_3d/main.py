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

RES = 20
COLS = SIZE[0] // RES + 10
ROWS = SIZE[1] // RES + 10

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()

def draw():
    py5.background(10, 20, 10)
    
    time_val = py5.frame_count * 0.02
    
    # Lighting for metallic look
    py5.ambient_light(0, 0, 20)
    py5.directional_light(40, 60, 100, 1, 1, -1) # Gold light
    py5.directional_light(200, 60, 100, -1, -1, -1) # Blue light
    py5.light_specular(0, 0, 100) # Bright white specular highlights
    
    py5.translate(SIZE[0]/2, SIZE[1]/2, -200)
    py5.rotate_x(py5.PI / 3) # Tilt camera to look across the surface
    
    py5.translate(-SIZE[0]/2, -SIZE[1]/2)
    
    # Material properties
    py5.specular(0, 0, 100)
    py5.shininess(15.0)
    
    py5.fill(0, 0, 50) # Base greyish metallic color
    
    # We will use triangle strips to render the mesh
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            px = (x - 5) * RES
            py1 = (y - 5) * RES
            py2 = (y - 4) * RES
            
            # Fluid waves using noise
            n1 = py5.os_noise(x * 0.05, y * 0.05, time_val)
            n2 = py5.os_noise(x * 0.05, (y + 1) * 0.05, time_val)
            
            z1 = py5.remap(n1, 0, 1, -200, 200)
            z2 = py5.remap(n2, 0, 1, -200, 200)
            
            py5.vertex(px, py1, z1)
            py5.vertex(px, py2, z2)
        py5.end_shape()

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
