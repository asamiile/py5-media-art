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
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.background(0)

def draw():
    py5.background(10, 15, 20)
    
    # Orthographic projection for isometric view
    # ortho(left, right, bottom, top, near, far)
    w = py5.width / 2
    h = py5.height / 2
    py5.ortho(-w, w, -h, h, -2000, 2000)
    
    t = py5.frame_count * 0.03
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    # Isometric rotations
    py5.rotate_x(-py5.asin(1 / py5.sqrt(3)))
    py5.rotate_y(py5.PI / 4)
    
    # Rotate the whole grid slowly
    py5.rotate_y(t * 0.2)
    
    grid_size = 40
    box_size = 30
    spacing = 35
    
    offset = (grid_size * spacing) / 2
    
    py5.translate(-offset, 0, -offset)
    
    py5.stroke(200, 50, 80, 50)
    py5.stroke_weight(1)
    
    for x in range(grid_size):
        for z in range(grid_size):
            px = x * spacing
            pz = z * spacing
            
            # Distance from center for radial wave
            cx = x - grid_size/2
            cz = z - grid_size/2
            dist = py5.sqrt(cx*cx + cz*cz)
            
            # Height based on perlin noise and sine wave
            noise_val = py5.os_noise(x * 0.1, z * 0.1, t * 0.5)
            wave_val = py5.sin(dist * 0.3 - t * 2)
            
            # Combine them
            h_val = (noise_val * 0.7 + wave_val * 0.3) * 300
            
            if h_val < 5:
                h_val = 5
            
            # Color mapping
            hue = (200 + noise_val * 60 + dist * 5 + t * 20) % 360
            sat = 60 + wave_val * 40
            brt = 50 + noise_val * 50
            
            py5.fill(hue, sat, brt)
            
            py5.push_matrix()
            py5.translate(px, h_val / 2, pz)
            py5.box(box_size, h_val, box_size)
            py5.pop_matrix()

    if py5.frame_count % 60 == 0:
        py5.load_np_pixels()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({(py5.frame_count/TOTAL_FRAMES)*100:.1f}%)")
        sys.stdout.flush()

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
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
