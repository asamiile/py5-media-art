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
PREVIEW_SIZE, OUTPUT_SIZE, _ = get_sizes()
SIZE = OUTPUT_SIZE

# Parameters
# We create a ribbon made of many parallel strands
NUM_STRANDS = 100
POINTS_PER_STRAND = 4000
TOTAL_POINTS = NUM_STRANDS * POINTS_PER_STRAND

# A continuous parameter array t
t_vals_base = np.linspace(0, 40 * np.pi, POINTS_PER_STRAND)

def setup():
    py5.size(*SIZE)
    py5.pixel_density(1)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    # Motion blur
    py5.blend_mode(py5.BLEND)
    py5.no_stroke()
    py5.fill(0, 5, 10, 40) 
    py5.rect(0, 0, SIZE[0], SIZE[1])
    
    py5.blend_mode(py5.ADD)
    
    time = py5.frame_count * 0.015
    
    # Base frequencies for the Lissajous knot
    freq_x = 3.0
    freq_y = 4.0
    freq_z = 5.0
    
    # We dynamically shift the phases to make the knot weave itself
    phase_x = time * 0.8
    phase_y = time * 1.1
    phase_z = time * 1.4
    
    # We also slowly modulate the frequencies to create a "breathing" shape
    # that morphs from one knot topology to another
    f_mod = np.sin(time * 0.2) * 0.5
    freq_x += f_mod
    freq_y -= f_mod * 0.8
    freq_z += f_mod * 1.2
    
    x_all = np.zeros(TOTAL_POINTS)
    y_all = np.zeros(TOTAL_POINTS)
    z_all = np.zeros(TOTAL_POINTS)
    
    # We create the ribbon by adding small sine wave offsets to each strand
    for i in range(NUM_STRANDS):
        # The base path
        t_vals = t_vals_base
        
        # Strand offsets (thickness of ribbon)
        offset_a = (i / NUM_STRANDS) * 2 * np.pi
        rad_offset = 20.0
        
        # Calculate 3D Lissajous
        x = 300.0 * np.sin(freq_x * t_vals + phase_x)
        y = 300.0 * np.sin(freq_y * t_vals + phase_y)
        z = 300.0 * np.sin(freq_z * t_vals + phase_z)
        
        # Add a high-frequency "wire" twist around the main path
        x += rad_offset * np.sin(30.0 * t_vals + offset_a)
        y += rad_offset * np.cos(30.0 * t_vals + offset_a)
        z += rad_offset * np.sin(20.0 * t_vals + offset_a * 2.0)
        
        start_idx = i * POINTS_PER_STRAND
        end_idx = start_idx + POINTS_PER_STRAND
        
        x_all[start_idx:end_idx] = x
        y_all[start_idx:end_idx] = y
        z_all[start_idx:end_idx] = z

    # 3D Rotation
    rot_y = time * 0.5
    rot_x = time * 0.3
    
    cos_ry = np.cos(rot_y)
    sin_ry = np.sin(rot_y)
    
    x_rot1 = x_all * cos_ry - z_all * sin_ry
    z_rot1 = x_all * sin_ry + z_all * cos_ry
    
    cos_rx = np.cos(rot_x)
    sin_rx = np.sin(rot_x)
    
    y_rot2 = y_all * cos_rx - z_rot1 * sin_rx
    z_rot2 = y_all * sin_rx + z_rot1 * cos_rx
    
    # Perspective projection
    fov = 1200.0
    z_offset = 800.0
    z_proj = z_rot2 + z_offset
    z_proj = np.maximum(z_proj, 1.0)
    
    x2d = (x_rot1 / z_proj) * fov + SIZE[0]/2
    y2d = SIZE[1]/2 - (y_rot2 / z_proj) * fov
    
    py5.stroke_weight(1.5)
    
    # Map color based on Z-depth (z_rot2) so the front is bright and back is dim/different color
    # Back -> Purple/Blue
    mask_back = z_rot2 < -100
    if np.any(mask_back):
        py5.stroke(50, 0, 255, 30)
        pts = np.column_stack((x2d[mask_back], y2d[mask_back]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Mid -> Cyan
    mask_mid = (z_rot2 >= -100) & (z_rot2 <= 100)
    if np.any(mask_mid):
        py5.stroke(0, 255, 200, 30)
        pts = np.column_stack((x2d[mask_mid], y2d[mask_mid]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
        py5.end_shape()
        
    # Front -> White/Cyan
    mask_front = z_rot2 > 100
    if np.any(mask_front):
        py5.stroke(200, 255, 255, 50)
        pts = np.column_stack((x2d[mask_front], y2d[mask_front]))
        py5.begin_shape(py5.POINTS)
        py5.vertices(pts)
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
        import os
        os._exit(0)

py5.run_sketch()
