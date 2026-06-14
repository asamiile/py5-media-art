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

# Precompute arcs
num_arcs = 1500
arc_starts = np.random.uniform(-400, 400, (num_arcs, 3))
arc_ends = np.random.uniform(-400, 400, (num_arcs, 3))
# Push them toward the surface of a sphere
for arr in (arc_starts, arc_ends):
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    arr[:] = (arr / norms) * np.random.uniform(200, 300, (num_arcs, 1))

# Control points are pushed outward from center
mid_points = (arc_starts + arc_ends) / 2
mid_norms = np.linalg.norm(mid_points, axis=1, keepdims=True)
mid_norms[mid_norms == 0] = 1 # avoid div zero
arc_cp1 = mid_points + (mid_points / mid_norms) * np.random.uniform(100, 500, (num_arcs, 1))
arc_cp2 = mid_points + (mid_points / mid_norms) * np.random.uniform(100, 500, (num_arcs, 1))

arc_widths = np.random.uniform(1, 4, num_arcs)
arc_phases = np.random.uniform(0, py5.TWO_PI, num_arcs)

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    py5.no_fill()
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    py5.rotate_y(t * py5.TWO_PI * 0.2)
    py5.rotate_x(t * py5.TWO_PI * 0.1)
    
    for i in range(num_arcs):
        phase = arc_phases[i] + t * py5.TWO_PI * 2.0
        # Determine visibility and intensity based on a sine wave (pulsing arcs)
        intensity = py5.sin(phase)
        
        if intensity > 0:
            # Color mapping: Deep red (0) to Yellow (60)
            hue = 20 + intensity * 40
            sat = 100 - intensity * 20
            brightness = 60 + intensity * 40
            alpha = 10 + intensity * 40
            
            py5.stroke(hue, sat, brightness, alpha)
            py5.stroke_weight(arc_widths[i])
            
            # Add noise turbulence to control points
            noise_val1 = py5.os_noise(arc_cp1[i,0]*0.01, arc_cp1[i,1]*0.01, arc_cp1[i,2]*0.01 + t*5) * 100
            noise_val2 = py5.os_noise(arc_cp2[i,0]*0.01, arc_cp2[i,1]*0.01, arc_cp2[i,2]*0.01 + t*5) * 100
            
            p1x, p1y, p1z = arc_starts[i]
            c1x, c1y, c1z = arc_cp1[i] + noise_val1
            c2x, c2y, c2z = arc_cp2[i] + noise_val2
            p2x, p2y, p2z = arc_ends[i]
            
            py5.begin_shape()
            py5.vertex(p1x, p1y, p1z)
            py5.bezier_vertex(c1x, c1y, c1z, c2x, c2y, c2z, p2x, p2y, p2z)
            py5.end_shape()
            
    # Draw central "sun" core
    py5.no_stroke()
    py5.fill(15, 100, 40, 60)
    py5.sphere(190)
    py5.fill(30, 80, 80, 40)
    py5.sphere(180)
    py5.fill(60, 20, 100, 30)
    py5.sphere(170)
    py5.no_fill()

    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count == 2 or py5.frame_count % 60 == 0:
        py5.load_np_pixels()
        if py5.np_pixels.std() < 1.0:
            print(f"[Error] Blank screen detected on frame {py5.frame_count} (std < 1.0). Aborting.")
            import os
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
            
        import os
        os._exit(0)

py5.run_sketch()
