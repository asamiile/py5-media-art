from pathlib import Path
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
FRAMES_DIR = SKETCH_DIR / "frames"
DURATION_SEC = 15
FPS = 60
TOTAL_FRAMES = DURATION_SEC * FPS
PREVIEW_FILENAME = preview_filename(pattern=1)
PREVIEW_SIZE, OUTPUT_SIZE, SIZE = get_sizes()

# Simulation Parameters
NUM_THREADS = 16
POINTS_PER_THREAD = 250
RADIUS = 150

# State
threads = None
stars = None

def setup():
    global threads, stars
    py5.size(*SIZE, py5.P3D)
    py5.smooth(8)
    FRAMES_DIR.mkdir(exist_ok=True)
    
    # Initialize Threads
    threads = []
    for i in range(NUM_THREADS):
        angle = py5.TWO_PI * i / NUM_THREADS
        # Points along Z axis
        pts = np.zeros((POINTS_PER_THREAD, 3))
        for j in range(POINTS_PER_THREAD):
            z = (j / POINTS_PER_THREAD - 0.5) * 800
            pts[j] = [RADIUS * np.cos(angle), RADIUS * np.sin(angle), z]
        threads.append(pts)
    
    # Stars
    num_stars = 15000
    star_pos = np.random.uniform(-1500, 1500, (num_stars, 3))
    star_mag = np.random.uniform(0.5, 2.5, num_stars)
    stars = (star_pos, star_mag)

def draw():
    global threads
    py5.background(2, 5, 10)  # Deep Obsidian
    
    t = py5.frame_count / 60.0
    
    # Camera
    cam_dist = 900 + 100 * np.sin(t * 0.2)
    py5.camera(cam_dist * np.cos(t * 0.1), -100 + 50 * np.cos(t * 0.3), cam_dist * np.sin(t * 0.1), 
               0, 0, 0, 0, 1, 0)
    
    # Draw Stars
    py5.stroke_weight(1)
    for p, m in zip(stars[0], stars[1]):
        alpha = 150 + 100 * np.sin(t * 5 + m * 10)
        py5.stroke(200, 230, 255, alpha)
        py5.point(*p)
    
    # Update and Draw Threads
    py5.no_fill()
    
    for i, pts in enumerate(threads):
        angle_off = py5.TWO_PI * i / NUM_THREADS
        
        # Color mapping: Indigo -> Cyan -> Crimson
        # We'll use multi-pass style for glow effect
        
        # Base colors
        c_indigo = (106, 13, 173)  # Royal Purple
        c_cyan = (0, 255, 255)
        c_crimson = (220, 20, 60)
        
        # Additive passes
        passes = 3
        for p in range(passes):
            alpha = 80 if p == 0 else (40 if p == 1 else 20)
            weight = 1.5 if p == 0 else (3.5 if p == 1 else 6.0)
            
            py5.stroke_weight(weight)
            py5.begin_shape()
            
            for j in range(POINTS_PER_THREAD):
                # Weave logic
                z_norm = j / POINTS_PER_THREAD
                phase = t * 1.5 + z_norm * 5 + angle_off
                
                # Helical motion
                helix_x = 40 * np.cos(phase * 1.2)
                helix_y = 40 * np.sin(phase * 0.8)
                
                # Noise perturbation
                nx = py5.noise(i * 0.1, j * 0.05, t * 0.2) - 0.5
                ny = py5.noise(i * 0.1 + 10, j * 0.05, t * 0.2) - 0.5
                nz = py5.noise(i * 0.1 + 20, j * 0.05, t * 0.2) - 0.5
                
                noise_scale = 100 * np.sin(t * 0.3 + z_norm * py5.PI)
                
                # Final position
                # Radius oscillates to create "unfolding" effect
                curr_r = RADIUS * (0.8 + 0.4 * np.sin(t * 0.5 + z_norm * 2))
                
                x = curr_r * np.cos(angle_off + phase * 0.1) + helix_x + nx * noise_scale
                y = curr_r * np.sin(angle_off + phase * 0.1) + helix_y + ny * noise_scale
                z = pts[j, 2] + nz * noise_scale
                
                # Color blending based on thread index and Z position
                mix = (np.sin(t + z_norm * 4 + i) + 1) / 2
                if mix < 0.4:
                    r, g, b_val = c_indigo
                elif mix < 0.8:
                    r, g, b_val = c_cyan
                else:
                    r, g, b_val = c_crimson
                
                py5.stroke(r, g, b_val, alpha)
                py5.vertex(x, y, z)
            
            py5.end_shape()

    # Save frames
    py5.save_frame(str(FRAMES_DIR / "frame-####.png"))

    if py5.frame_count >= TOTAL_FRAMES:
        py5.exit_sketch()
        # FFmpeg
        subprocess.run([
            "ffmpeg", "-y", "-r", str(FPS),
            "-i", str(FRAMES_DIR / "frame-%04d.png"),
            "-c:v", "libx264", "-crf", "32", "-pix_fmt", "yuv420p",
            str(SKETCH_DIR / "output.mp4"),
        ], check=True)
        # Preview
        mid = str(FRAMES_DIR / f"frame-{TOTAL_FRAMES // 2:04d}.png")
        subprocess.run(["cp", mid, str(SKETCH_DIR / PREVIEW_FILENAME)], check=True)

if __name__ == "__main__":
    py5.run_sketch()
