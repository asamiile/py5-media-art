from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
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
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

def setup():
    py5.size(SIZE[0], SIZE[1], py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)

def draw():
    py5.background(0, 0, 5) # Obsidian black
    
    # Lighting for specular reflections
    py5.lights()
    py5.ambient_light(0, 0, 10)
    py5.directional_light(270, 70, 100, 0.5, 0.5, -1) # Violet tint
    py5.directional_light(45, 80, 100, -0.5, 0.5, -1) # Gold tint
    py5.spot_light(0, 0, 100, 0, 0, 1000, 0, 0, -1, py5.PI/2, 2) # Bright center light
    
    py5.translate(py5.width / 2, py5.height / 2 + 400, -600)
    py5.rotate_x(py5.PI / 2.5)
    
    # Slow rotation
    py5.rotate_z(py5.frame_count * 0.005)
    
    py5.no_stroke()
    # Use specular material
    py5.specular(0, 0, 80)
    py5.shininess(50)
    py5.fill(0, 0, 15) # Dark silver/black fluid
    
    cols, rows = 120, 120
    size = 40
    
    t = py5.frame_count * 0.015
    
    py5.translate(-cols*size/2, -rows*size/2)
    
    for y in range(rows - 1):
        py5.begin_shape(py5.TRIANGLE_STRIP)
        for x in range(cols):
            for dy in (0, 1):
                px = x * size
                py = (y + dy) * size
                
                # To make hexagonal spikes, we use a combination of sine waves
                v1 = np.sin(px * 0.05 + py * 0.05)
                v2 = np.sin(px * 0.05 - py * 0.05)
                v3 = np.sin(py * 0.07)
                hex_pattern = (v1 * v2 * v3) ** 2
                
                # Magnetic field strength (macro scale)
                mag = py5.noise(px * 0.002, py * 0.002, t)
                
                # Rise up where field is strong
                # Sharpness depends on mag
                spike = hex_pattern * np.exp(mag * 4.0) * 15.0
                
                # Base fluid movement
                base = py5.noise(px * 0.01, py * 0.01, t * 0.5) * 200 - 100
                
                pz = base + spike
                
                # Dynamic coloring based on height
                # Mapping height to slightly different hues (dark violet to gold)
                if pz > base + 100:
                    py5.emissive(45, 80, min(100, (pz - base - 100)*0.5)) # Golden tips
                else:
                    py5.emissive(0, 0, 0)
                    
                py5.vertex(px, py, pz)
        py5.end_shape()

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

py5.run_sketch()
