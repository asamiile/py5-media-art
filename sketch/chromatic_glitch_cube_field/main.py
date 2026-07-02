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

NUM_CUBES = 200
cubes = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    # Use RGB for additive chromatic aberration
    py5.color_mode(py5.RGB, 255)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    for _ in range(NUM_CUBES):
        cubes.append({
            'x': py5.random(-800, 800),
            'y': py5.random(-800, 800),
            'z': py5.random(-800, 800),
            'rx': py5.random(py5.TWO_PI),
            'ry': py5.random(py5.TWO_PI),
            's': py5.random(20, 150),
            'rs': py5.random(0.01, 0.05) * (1 if py5.random(1) > 0.5 else -1)
        })

def draw_scene():
    py5.no_fill()
    py5.stroke_weight(3)
    
    for c in cubes:
        py5.push_matrix()
        py5.translate(c['x'], c['y'], c['z'])
        py5.rotate_x(c['rx'] + py5.frame_count * c['rs'])
        py5.rotate_y(c['ry'] + py5.frame_count * c['rs'])
        py5.box(c['s'])
        py5.pop_matrix()

def draw():
    py5.background(0)
    
    t = py5.frame_count * 0.02
    
    # Calculate glitch intensity
    # Sporadic spikes in noise create a glitching effect
    glitch_val = py5.noise(t * 10)
    glitch_intensity = 0
    if glitch_val > 0.7:
        glitch_intensity = py5.remap(glitch_val, 0.7, 1.0, 0, 100)
        
    py5.blend_mode(py5.ADD)
    
    # Base camera transformation
    cam_z = -500 + py5.sin(t * 0.5) * 200
    cam_ry = t * 0.2
    
    # Red Channel
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, cam_z)
    py5.rotate_y(cam_ry)
    # Apply chromatic aberration offset based on glitch
    py5.translate(py5.random(-glitch_intensity, glitch_intensity) - 5, 0, 0)
    py5.stroke(255, 0, 0)
    draw_scene()
    py5.pop_matrix()

    # Green Channel
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, cam_z)
    py5.rotate_y(cam_ry)
    # Center channel, no major offset unless glitching hard
    py5.translate(py5.random(-glitch_intensity, glitch_intensity), py5.random(-glitch_intensity, glitch_intensity) * 0.5, 0)
    py5.stroke(0, 255, 0)
    draw_scene()
    py5.pop_matrix()
    
    # Blue Channel
    py5.push_matrix()
    py5.translate(py5.width / 2, py5.height / 2, cam_z)
    py5.rotate_y(cam_ry)
    py5.translate(py5.random(-glitch_intensity, glitch_intensity) + 5, 0, 0)
    py5.stroke(0, 0, 255)
    draw_scene()
    py5.pop_matrix()
    
    # Add digital scanlines
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 50)
    for y in range(0, py5.height, 4):
        py5.rect(0, y, py5.width, 2)
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)", flush=True)

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "/opt/homebrew/bin/ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vf", "tmix=frames=3:weights=1 1 1", "-vcodec", "libx264", "-pix_fmt", "yuv420p",
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
