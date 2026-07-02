from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np

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
    FRAMES_DIR.mkdir(exist_ok=True)
    py5.no_stroke()
    
def draw():
    py5.background(10, 5, 5) # Obsidian Black with slight red tint
    
    # Glow blend
    py5.blend_mode(py5.ADD)
    py5.hint(py5.DISABLE_DEPTH_TEST)
    
    py5.translate(py5.width / 2, py5.height / 2, 0)
    
    t = py5.frame_count * 0.05
    
    num_rings = 40
    num_segments = 24
    
    # Portal travel effect
    # The progress loops from 0 to 1 over one segment width
    travel_progress = (t * 0.2) % 1.0
    
    for ring_idx in range(num_rings, 0, -1):
        # Scale decreases exponentially to create infinite depth
        # We add travel_progress so the rings smoothly grow and move forward
        continuous_idx = ring_idx - travel_progress
        
        radius = 2000 * (0.85 ** continuous_idx)
        prev_radius = 2000 * (0.85 ** (continuous_idx - 1))
        
        z = -continuous_idx * 150
        prev_z = -(continuous_idx - 1) * 150
        
        # Ring rotation
        rot_offset = continuous_idx * 0.15 + t * 0.05
        
        py5.push_matrix()
        py5.translate(0, 0, z)
        
        for i in range(num_segments):
            angle1 = (i / num_segments) * py5.TWO_PI + rot_offset
            angle2 = ((i + 1) / num_segments) * py5.TWO_PI + rot_offset
            
            x1, y1 = np.cos(angle1) * radius, np.sin(angle1) * radius
            x2, y2 = np.cos(angle2) * radius, np.sin(angle2) * radius
            
            prev_rot_offset = (continuous_idx - 1) * 0.15 + t * 0.05
            p_angle1 = (i / num_segments) * py5.TWO_PI + prev_rot_offset
            p_angle2 = ((i + 1) / num_segments) * py5.TWO_PI + prev_rot_offset
            
            px1, py1 = np.cos(p_angle1) * prev_radius, np.sin(p_angle1) * prev_radius
            px2, py2 = np.cos(p_angle2) * prev_radius, np.sin(p_angle2) * prev_radius
            
            # Distance from center for coloring
            depth_ratio = continuous_idx / num_rings
            
            # Noise-based brightness
            n = py5.os_noise(i * 0.5, ring_idx * 0.2, t * 0.2)
            
            alpha = int(255 * (1 - depth_ratio) * n)
            
            if i % 2 == 0:
                py5.fill(255, 215, 0, alpha) # Fiery Gold
            else:
                py5.fill(220, 20, 60, alpha) # Crimson Red
                
            if n > 0.8:
                py5.fill(255, 255, 255, alpha * 1.5) # Solar White
                
            py5.begin_shape()
            py5.vertex(x1, y1, 0)
            py5.vertex(x2, y2, 0)
            py5.vertex(px2, py2, prev_z - z)
            py5.vertex(px1, py1, prev_z - z)
            py5.end_shape(py5.CLOSE)
            
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
