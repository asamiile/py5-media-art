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

# Precompute spherical Fibonacci points
N = 3000
golden_ratio = (1 + np.sqrt(5)) / 2
indices = np.arange(0, N, dtype=float) + 0.5
phi = np.arccos(1 - 2 * indices / N)
theta = py5.TWO_PI * indices / golden_ratio

points_x = np.sin(phi) * np.cos(theta)
points_y = np.sin(phi) * np.sin(theta)
points_z = np.cos(phi)

core_radius = 200

def setup():
    py5.size(*SIZE, py5.P3D)
    py5.smooth()
    py5.pixel_density(1)
    py5.color_mode(py5.HSB, 360, 100, 100, 100)
    FRAMES_DIR.mkdir(exist_ok=True)

def draw():
    py5.background(0)
    py5.blend_mode(py5.ADD)
    py5.no_stroke()
    
    py5.translate(SIZE[0] / 2, SIZE[1] / 2, 0)
    t = py5.frame_count / float(TOTAL_FRAMES)
    
    # Rotate the entire core
    py5.rotate_y(t * py5.TWO_PI)
    py5.rotate_x(t * py5.TWO_PI * 0.5)
    
    # Draw central core
    py5.fill(210, 80, 20, 100)
    py5.sphere(core_radius * 0.95)
    
    for i in range(N):
        x = points_x[i]
        y = points_y[i]
        z = points_z[i]
        
        # Calculate pulse using 4D noise
        noise_val = py5.os_noise(x * 2.0, y * 2.0, z * 2.0, t * 5.0)
        pulse = py5.sin(t * py5.TWO_PI * 3.0 + i * 0.1) * 0.5 + 0.5
        
        # Combine noise and pulse
        intensity = noise_val * pulse
        
        # Base pillar length
        pillar_len = 50 + intensity * 300
        
        py5.push_matrix()
        # Translate to the surface of the core
        py5.translate(x * core_radius, y * core_radius, z * core_radius)
        
        # Orient the box along the normal vector
        # Compute rotation axis from (0,0,1) to (x,y,z)
        v1 = np.array([0, 0, 1])
        v2 = np.array([x, y, z])
        cross_prod = np.cross(v1, v2)
        dot_prod = np.dot(v1, v2)
        
        # If not directly opposite
        if dot_prod < 0.9999:
            angle = np.arccos(dot_prod)
            py5.rotate(angle, float(cross_prod[0]), float(cross_prod[1]), float(cross_prod[2]))
            
        # Shift so the box starts at the surface and extrudes outward
        py5.translate(0, 0, pillar_len / 2)
        
        if intensity > 0.6:
            # Bright amber data burst
            py5.fill(40, 90, 100, 80)
            py5.stroke(40, 50, 100, 90)
        elif intensity > 0.3:
            # Electric blue
            py5.fill(210, 80, 90, 60)
            py5.no_stroke()
        else:
            # Dim blue
            py5.fill(210, 60, 40, 40)
            py5.no_stroke()
            
        py5.stroke_weight(1)
        py5.box(8, 8, pillar_len)
        py5.pop_matrix()

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
