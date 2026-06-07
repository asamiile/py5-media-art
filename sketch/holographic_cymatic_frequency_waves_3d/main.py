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
    py5.background(10, 10, 20)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, -200)
    
    t = py5.frame_count * 0.05
    py5.rotate_x(py5.PI / 3)
    py5.rotate_z(t * 0.1)
    
    # Grid parameters
    grid_res = 120
    spacing = 15
    offset = (grid_res * spacing) / 2
    
    py5.translate(-offset, -offset, 0)
    
    # Cymatic parameters (changing frequencies)
    kx = py5.remap(py5.sin(t * 0.2), -1, 1, 1, 5)
    ky = py5.remap(py5.cos(t * 0.3), -1, 1, 1, 5)
    
    py5.no_stroke()
    
    for x in range(grid_res):
        for y in range(grid_res):
            cx = x * spacing
            cy = y * spacing
            
            # Map grid coords to [-PI, PI] for wave function
            nx = py5.remap(x, 0, grid_res, -py5.PI, py5.PI)
            ny = py5.remap(y, 0, grid_res, -py5.PI, py5.PI)
            
            # Chladni plate standing wave approximation
            chladni = py5.cos(nx * kx) * py5.cos(ny * ky) - py5.cos(nx * ky) * py5.cos(ny * kx)
            
            # Where chladni is near 0, sand collects
            sand = 1.0 - abs(chladni)
            sand = pow(sand, 4) # Sharpen the lines
            
            z = sand * 150
            
            # Color based on position and height
            dist_center = py5.dist(cx, cy, offset, offset)
            hue = (dist_center * 0.1 + z + t * 20) % 360
            
            if sand > 0.1:
                py5.push_matrix()
                py5.translate(cx, cy, z)
                py5.fill(hue, 90, 100, 60 + sand * 40)
                size = sand * 8
                py5.rect(0, 0, size, size)
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
