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
    py5.background(5, 5, 10)
    py5.blend_mode(py5.ADD)
    py5.translate(py5.width / 2, py5.height / 2, -300)
    
    t = py5.frame_count * 0.05
    py5.rotate_x(py5.PI / 3 + py5.sin(t * 0.2) * 0.1)
    py5.rotate_z(t * 0.3)
    
    grid_size = 50
    spacing = 25
    offset = (grid_size * spacing) / 2
    
    py5.translate(-offset, -offset, 0)
    
    py5.no_stroke()
    
    for x in range(grid_size):
        for y in range(grid_size):
            cx = x * spacing
            cy = y * spacing
            
            # Quantum wave function formula (combination of sines and noise)
            dist_center = py5.dist(cx, cy, offset, offset)
            
            wave1 = py5.sin(dist_center * 0.05 - t) * 50
            wave2 = py5.cos(cx * 0.02 + t) * py5.sin(cy * 0.02 + t) * 100
            noise_val = py5.os_noise(cx * 0.01, cy * 0.01, t * 0.5) * 150
            
            z = wave1 + wave2 + noise_val
            
            # Probability density (amplitude squared roughly)
            prob = py5.remap(abs(z), 0, 200, 0, 1)
            
            py5.push_matrix()
            py5.translate(cx, cy, z)
            
            # Color shifts based on "probability" and time
            hue = (dist_center * 0.2 - t * 10 + prob * 120) % 360
            py5.fill(hue, 90, 100, 60 + prob * 40)
            
            # Size of "particle"
            size = py5.remap(prob, 0, 1, 2, 8)
            
            # Draw particle
            py5.rect(-size/2, -size/2, size, size)
            
            py5.pop_matrix()


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
