from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import os

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

GRID = 30
SPACING = 30
particles = []

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    global particles
    offset = (GRID - 1) * SPACING / 2.0
    for x in range(GRID):
        for y in range(GRID):
            for z in range(GRID):
                px = x * SPACING - offset
                py = y * SPACING - offset
                pz = z * SPACING - offset
                
                # Keep spherical distribution
                dist = np.sqrt(px*px + py*py + pz*pz)
                if dist < offset:
                    particles.append(np.array([px, py, pz]))

def draw():
    py5.background(0) # Stark black
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    
    t = py5.frame_count * 0.02
    
    py5.translate(py5.width/2, py5.height/2, 0)
    
    py5.rotate_y(t * 0.2)
    py5.rotate_x(py5.PI/6 + np.sin(t*0.1)*0.2)
    
    # State interpolation (Particle vs Wave)
    # A wave that oscillates between 0 (particle grid) and 1 (wave form)
    state = (np.sin(t * 1.5) * 0.5 + 0.5)
    # Smoothstep for sharper transitions
    state = state * state * (3 - 2 * state)
    
    py5.blend_mode(py5.ADD)
    
    py5.stroke_weight(3)
    py5.begin_shape(py5.POINTS)
    
    # Interference sources
    source1 = np.array([np.sin(t)*200, 0, np.cos(t)*200])
    source2 = np.array([np.cos(t*1.5)*200, 0, np.sin(t*1.5)*200])
    
    for p in particles:
        # Base grid position
        grid_pos = p.copy()
        
        # Calculate wave displacement
        d1 = np.linalg.norm(p - source1)
        d2 = np.linalg.norm(p - source2)
        
        wave_amp1 = np.sin(d1 * 0.05 - t * 5) * 30
        wave_amp2 = np.sin(d2 * 0.05 - t * 5) * 30
        
        # Interference pattern
        total_amp = wave_amp1 + wave_amp2
        
        # Wave pos pushes points along Y axis
        wave_pos = p.copy()
        wave_pos[1] += total_amp
        
        # Interpolate
        final_pos = grid_pos * (1 - state) + wave_pos * state
        
        # Color based on state and amplitude
        if state < 0.1:
            py5.stroke(0, 0, 100, 80) # Pure white particle
        else:
            # Chromatic shift based on height
            if total_amp > 0:
                py5.stroke(0, 100, 100, 60) # Red
            else:
                py5.stroke(180, 100, 100, 60) # Cyan
                
        py5.vertex(*final_pos)
        
    py5.end_shape()
    
    py5.blend_mode(py5.BLEND)

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2:
        py5.load_np_pixels()
        if py5.np_pixels.std() == 0:
            print("[Error] Blank screen detected on frame 2 (std=0). Aborting.")
            os._exit(1)

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
            
        os._exit(0)

py5.run_sketch()
