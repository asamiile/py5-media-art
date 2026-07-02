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

COLS = 50
ROWS = 50
SCL = 60 # Scale of each grid cell

# Mesh data
terrain = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize terrain array
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            row.append(0)
        terrain.append(row)

def draw():
    py5.background(10, 80, 10) # Dark background
    py5.blend_mode(py5.ADD)
    
    # Update terrain with moving noise (the "wind")
    flying = py5.frame_count * 0.02
    
    yoff = flying
    for y in range(ROWS):
        xoff = 0
        for x in range(COLS):
            # Complex noise for crystalline peaks and valleys
            n1 = py5.os_noise(xoff, yoff)
            n2 = py5.os_noise(xoff * 2, yoff * 2) * 0.5
            n3 = py5.os_noise(xoff * 4, yoff * 4) * 0.25
            total_noise = n1 + n2 + n3
            
            # Use power to create sharp peaks like crystals
            terrain[y][x] = py5.remap(pow(abs(total_noise), 2.5), 0, 1.75, -200, 600)
            xoff += 0.1
        yoff += 0.1

    # Camera setup
    py5.translate(SIZE[0]/2, SIZE[1]/2 + 200, -600)
    py5.rotate_x(py5.PI / 3)
    
    # Slow panning rotation
    py5.rotate_z(py5.frame_count * 0.002)
    
    py5.translate(-COLS * SCL / 2, -ROWS * SCL / 2)
    
    # Draw the crystalline aurora mesh
    py5.no_stroke()
    
    for y in range(ROWS - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(COLS):
            # Vertex 1 (Top)
            z1 = terrain[y][x]
            # Aurora colors based on height and position
            hue1 = py5.remap(z1, -200, 600, 120, 280) # Green to Purple
            glow1 = py5.remap(py5.sin(y * 0.2 - flying * 2), -1, 1, 50, 200)
            py5.fill(hue1, 80, 100, glow1)
            py5.vertex(x * SCL, y * SCL, z1)
            
            # Vertex 2 (Bottom)
            z2 = terrain[y+1][x]
            hue2 = py5.remap(z2, -200, 600, 120, 280)
            glow2 = py5.remap(py5.sin((y+1) * 0.2 - flying * 2), -1, 1, 50, 200)
            py5.fill(hue2, 80, 100, glow2)
            py5.vertex(x * SCL, (y+1) * SCL, z2)
            
        py5.end_shape()

    py5.blend_mode(py5.BLEND)

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
