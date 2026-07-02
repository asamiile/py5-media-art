from pathlib import Path
import shutil
import subprocess
import sys
import py5
import numpy as np
import math
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from lib.paths import sketch_dir
from lib.sizes import get_sizes

SKETCH_DIR = sketch_dir(__file__)
WORK_NAME = SKETCH_DIR.name
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 10  # 10 seconds animation
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = f"{WORK_NAME}_p1.png"
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Generate Recaman sequence
def get_recaman(n_terms):
    visited = {0}
    curr = 0
    sequence = [0]
    for i in range(1, n_terms):
        backward = curr - i
        if backward > 0 and backward not in visited:
            curr = backward
        else:
            curr = curr + i
        sequence.append(curr)
        visited.add(curr)
    return sequence

N_TERMS = 140
RECAMAN_SEQ = get_recaman(N_TERMS)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Calculate loop parameters
    t = py5.frame_count / TOTAL_FRAMES
    theta = t * 2 * math.pi
    
    # Background (dark obsidian navy)
    py5.background(245, 50, 6)
    
    # Perspective and camera settings
    py5.perspective(math.pi / 3, SIZE[0] / SIZE[1], 10, 10000)
    
    # Camera rotates slowly around the center
    cam_radius = 850 + 150 * math.sin(theta)
    cam_x = cam_radius * math.cos(theta * 0.5)
    cam_y = 300 * math.sin(theta)
    cam_z = cam_radius * math.sin(theta * 0.5)
    py5.camera(cam_x, cam_y, cam_z, 0, 0, 0, 0, 1, 0)
    
    # Additive glow rendering
    py5.blend_mode(py5.ADD)
    py5.no_fill()
    
    # Normalize sequence values for rendering scale
    max_val = max(RECAMAN_SEQ)
    scale_factor = 450.0 / max_val
    
    # Draw multiple symmetric wings
    n_wings = 3
    for wing in range(n_wings):
        py5.push_matrix()
        # Rotate each wing around the Y-axis
        py5.rotate_y(wing * (2 * math.pi / n_wings) + theta * 0.25)
        
        for i in range(1, len(RECAMAN_SEQ)):
            prev = RECAMAN_SEQ[i - 1] * scale_factor
            curr = RECAMAN_SEQ[i] * scale_factor
            
            # Midpoint and radius of the arc
            center_x = (prev + curr) / 2.0 - (max_val * scale_factor / 2.0)
            radius = abs(curr - prev) / 2.0
            
            # Skip drawing zero-radius arcs
            if radius < 0.1:
                continue
                
            # Dynamic wave propagation through indices
            wave_val = math.sin(theta - i * 0.1)
            
            # Rotate each arch individually to create a nested gyroscopic structure
            py5.push_matrix()
            py5.translate(center_x, 0, 0)
            py5.rotate_x(wave_val * 0.6)
            
            # Select color based on index and wave phase
            hue_phase = (theta + i * 0.05) % (2 * math.pi)
            if i % 7 == 0:
                # Orange Amber Accent
                hue = 25
                sat = 95
                val = py5.remap(math.sin(hue_phase * 2), -1, 1, 80, 100)
                stroke_w = 2.5
                alpha = py5.remap(math.sin(hue_phase), -1, 1, 50, 95)
            else:
                # Sapphire to Cyan base
                hue = py5.remap(math.cos(hue_phase), -1, 1, 185, 220)
                sat = py5.remap(math.sin(hue_phase), -1, 1, 75, 95)
                val = py5.remap(math.cos(hue_phase * 1.5), -1, 1, 65, 88)
                stroke_w = 1.2
                alpha = py5.remap(math.sin(hue_phase), -1, 1, 30, 80)
                
            py5.stroke(hue, sat, val, alpha)
            py5.stroke_weight(stroke_w)
            
            # Draw semi-circular arch in P3D
            py5.begin_shape()
            # Alternate upper and lower semicircles
            sign = 1 if i % 2 == 0 else -1
            n_segments = 36
            for step in range(n_segments + 1):
                ang = step * (math.pi / n_segments)
                ax = math.cos(ang) * radius
                ay = sign * math.sin(ang) * radius
                py5.vertex(ax, ay, 0)
            py5.end_shape()
            
            py5.pop_matrix()
            
        py5.pop_matrix()
        
    py5.blend_mode(py5.BLEND)
    
    # Save frame
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))
    
    # Fail-safe: abort if nothing is drawn
            
    # Progress feedback
    if py5.frame_count % 60 == 0:
        print(f"[Render Progress] Frame {py5.frame_count}/{TOTAL_FRAMES} ({py5.frame_count/TOTAL_FRAMES*100:.1f}%)")
        
    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        
        # Compile frames into MP4
        print(f"[Render FFmpeg] Compiling {TOTAL_FRAMES} frames into video...")
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-vcodec", "libx264", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / f"{WORK_NAME}.mp4"),
        ], check=True)
        
        # Save a preview snapshot
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)
        
        # Clean up frames directory
        if FRAMES_DIR.exists():
            shutil.rmtree(FRAMES_DIR)
            print("[Render Cleanup] Temporary frames directory successfully removed.")
            
        print("[Render Complete] Video and preview successfully generated.")
        os._exit(0)

py5.run_sketch()
